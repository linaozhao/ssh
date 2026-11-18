"""Bounded CPU API execution, immutable fingerprints and auditable resumption."""
from __future__ import annotations

import concurrent.futures
import datetime
import getpass
import json
import os
import platform
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from common import ROOT, REPO, digest, file_hash, read_json, read_rows, write_json, write_rows
from construction import prepare, SOURCE
from diagnosis import diagnose
from protocol import render, parse_response, normalize_final, RUBRIC, FINAL_SCHEMA, EXTRACT_SCHEMA


def load_tasks() -> list[dict]:
    return sum((read_rows(ROOT / f'data/{kind}_inputs.jsonl') for kind in ('A', 'B1', 'B2')), [])


def fingerprint() -> dict:
    files = sorted((ROOT / 'lib').glob('*.py')) + sorted((ROOT / 'config').glob('*.json'))
    files += sorted((ROOT / 'data').glob('*_inputs.jsonl')) + sorted((ROOT / 'references').glob('*_references.jsonl'))
    files += [ROOT / 'data/group_manifest.jsonl']
    files += [REPO / 'experiments/cbm_drift_diagnostic_v3/src/cbm_drift_v3/state.py', REPO / 'src/mad_attr_filter/attributes.py']
    return {str(p.relative_to(REPO)): file_hash(p) for p in files}


def prepare_run() -> dict:
    prepare()
    config = read_json(ROOT / 'config/judge.json')
    manifest = read_rows(ROOT / 'data/group_manifest.jsonl')
    byid = {m['task_id']: m for m in manifest}
    queue = []
    for t in load_tasks():
        for method in ('M0', 'M1', 'M2'):
            phase = 'extract' if method == 'M2' else 'diagnose'
            prompt = render(t, method, phase)
            # UTF-8 bytes plus framing is an intentionally conservative tokenizer-independent proxy.
            bound = len(json.dumps(prompt, ensure_ascii=False).encode()) + 256
            max_calls = 2 if method == 'M2' else 1
            supplement_bound = bound + 2 * config['max_tokens'] * 4 if method == 'M2' else 0
            queue.append({'request_id': 'q_' + digest([config['experiment_id'], t['task_id'], method])[:20],
                          'task_id': t['task_id'], 'split': byid[t['task_id']]['split'], 'method': method,
                          'task_kind': t['task_kind'], 'prompt_sha256': digest(prompt),
                          'prompt_utf8_byte_token_proxy': bound, 'max_calls': max_calls,
                          'upper_bound_with_supplement': bound + supplement_bound + max_calls * config['max_tokens']})
    write_rows(ROOT / 'queue.jsonl', queue, True)
    write_json(ROOT / 'protocol_schema.json', {'rubric': RUBRIC, 'final': FINAL_SCHEMA, 'extraction': EXTRACT_SCHEMA}, True)
    files = fingerprint()
    frozen = {'experiment_id': config['experiment_id'], 'starting_commit': 'ad3199d1d8968edaba18963a21ca9e9b7c9dd16e',
              'source_file': str(SOURCE.relative_to(REPO)), 'source_sha256': file_hash(SOURCE),
              'files': files, 'fingerprint': digest(files), 'queue_sha256': file_hash(ROOT / 'queue.jsonl'),
              'prompt_protocol_sha256': file_hash(ROOT / 'protocol_schema.json'),
              'python': platform.python_version(), 'platform': platform.platform(),
              'reference_kind': 'program_verified_not_human', 'methods': ['M0', 'M1', 'M2'],
              'split_protocol': '6/6 existing families; new controlled texts, not new base-task generalization',
              'online_default': False, 'real_mad_evaluation': 'not_started', 'gpu_used': False}
    write_json(ROOT / 'freeze.json', frozen, True)
    budget = {'method_task_units': len(queue), 'input_tasks': 192, 'base_max_physical_calls': sum(q['max_calls'] for q in queue),
              'retry_cap': config['retry_cap'], 'attempt_cap': config['physical_attempt_cap'],
              'configured_total_token_cap': config['total_token_cap'],
              'worst_case_prompt_and_completion_proxy': sum(q['upper_bound_with_supplement'] for q in queue),
              'estimation_method': 'Actual rendered prompt UTF-8 byte lengths + 256 framing; supplemental size reserved conservatively. Not provider-exact tokenization.',
              'actual_usage_source': 'provider usage; missing usage charged by reservation; money unknown',
              'by_split': {s: {'units': sum(q['split'] == s for q in queue), 'calls_upper_bound': sum(q['max_calls'] for q in queue if q['split'] == s)} for s in ('dev', 'holdout')}}
    write_json(ROOT / 'budget.json', budget, True)
    return frozen


class OnlineRunner:
    """Never retry normal wrong answers, malformed JSON or truncated outputs."""

    def __init__(self, key: str, config: dict, frozen: dict):
        self.key, self.config, self.frozen = key, config, frozen
        self.directory = ROOT / 'results'
        self.directory.mkdir(exist_ok=True)
        self.calls = self.directory / 'calls'
        self.units = self.directory / 'units'
        self.calls.mkdir(exist_ok=True)
        self.units.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        self.halt = threading.Event()
        self.ledger_path = self.directory / 'attempts.jsonl'
        self.ledger = read_rows(self.ledger_path) if self.ledger_path.exists() else []
        self.spent = sum(r['reserved_tokens'] for r in self.ledger)
        # A crashed in-flight attempt keeps its reservation. Never blindly rerun it.
        completed = {p.stem: read_json(p) for p in self.calls.glob('*.json')}
        for row in self.ledger:
            c = completed.get(row['attempt_id'])
            if c and c.get('usage', {}).get('total_tokens') is not None:
                self.spent += c['usage']['total_tokens'] - row['reserved_tokens']
        for p in list(self.calls.glob('*.json')) + list(self.units.glob('*.json')):
            if read_json(p).get('fingerprint') != frozen['fingerprint']:
                raise ValueError(f'Fingerprint mismatch: {p.name}')

    def request(self, payload: dict, path: str) -> dict:
        body = json.dumps(payload).encode() if payload else None
        req = urllib.request.Request(self.config['base_url'] + path, data=body,
                                     headers={'Authorization': 'Bearer ' + self.key, 'Content-Type': 'application/json'})
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=self.config['timeout_seconds']) as response:
            return json.loads(response.read())

    def probe(self) -> dict:
        """Model-list verification does not consume completion requests."""
        try:
            response = self.request({}, '/models')
            names = [r['id'] for r in response.get('data', [])]
            ok = self.config['model'] in names
            result = {'status': 'verified' if ok else 'model_missing', 'advertised_models': names,
                      'requested_model_id': self.config['model'], 'credential_saved': False,
                      'mapping_provenance': 'Existing official API model mapping; catalogue verifies deployed ID, not unexposed weight revision.'}
        except urllib.error.HTTPError as exc:
            result = {'status': 'blocked', 'http_status': exc.code, 'reason': 'authenticated_model_catalogue_request_failed', 'credential_saved': False}
        except (OSError, ValueError) as exc:
            result = {'status': 'blocked', 'reason': type(exc).__name__, 'credential_saved': False}
        write_json(self.directory / 'model_probe.json', result)
        return result

    def call(self, q: dict, phase: str, prompt: list[dict]) -> dict:
        config = self.config
        payload = {'model': config['model'], 'messages': prompt, 'max_tokens': config['max_tokens'],
                   'thinking': config['thinking'], 'reasoning_effort': config['reasoning_effort'],
                   'response_format': config['response_format'], 'stream': False}
        reserve = len(json.dumps(prompt, ensure_ascii=False).encode()) + 256 + config['max_tokens']
        if reserve > config['context_token_bound']:
            return {'status': 'context_bound_exceeded', 'raw_response': ''}
        for attempt in range(config['max_infrastructure_retries'] + 1):
            aid = q['request_id'] + '_' + phase + f'_{attempt}'
            destination = self.calls / (aid + '.json')
            if destination.exists():
                old = read_json(destination)
                if old['payload_sha256'] != digest(payload):
                    raise ValueError('Payload changed on resume')
                if not old.get('retryable') or attempt == config['max_infrastructure_retries']:
                    return old
                continue
            with self.lock:
                if any(x['attempt_id'] == aid for x in self.ledger):
                    return {'status': 'unresolved_inflight_attempt', 'raw_response': '', 'attempt_id': aid}
                if self.halt.is_set():
                    return {'status': 'blocked_after_service_failure', 'raw_response': ''}
                retries = sum(r['retry'] for r in self.ledger)
                calls = sum(not r['retry'] for r in self.ledger)
                if len(self.ledger) >= config['physical_attempt_cap'] or calls >= config['physical_call_cap_without_retries'] or (attempt and retries >= config['retry_cap']) or self.spent + reserve > config['total_token_cap']:
                    self.halt.set()
                    return {'status': 'budget_exhausted', 'raw_response': ''}
                entry = {'attempt_id': aid, 'request_id': q['request_id'], 'phase': phase, 'split': q['split'],
                         'retry': attempt > 0, 'reserved_tokens': reserve, 'payload_sha256': digest(payload),
                         'fingerprint': self.frozen['fingerprint'], 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
                with self.ledger_path.open('a') as f:
                    f.write(json.dumps(entry) + '\n')
                    f.flush()
                    os.fsync(f.fileno())
                self.ledger.append(entry)
                self.spent += reserve
            start = time.monotonic()
            row = {**entry, 'status': 'api_success', 'payload': payload, 'raw_response': '', 'usage': {}, 'retryable': False}
            try:
                data = self.request(payload, '/chat/completions')
                row['provider_response'] = data
                choice = data.get('choices', [{}])[0]
                row.update(raw_response=choice.get('message', {}).get('content') or '', finish_reason=choice.get('finish_reason'),
                           usage=data.get('usage', {}), returned_model=data.get('model'))
                parsed, source = parse_response(row['raw_response'])
                row.update(parsed=parsed, parse_source=source)
                if not choice.get('message'):
                    row['status'] = 'invalid_provider_response'
            except urllib.error.HTTPError as exc:
                row.update(status='api_failure', http_status=exc.code,
                           retryable=exc.code in (408, 429, 500, 502, 503, 504), exception_type='HTTPError')
                if exc.code in (401, 402, 403):
                    self.halt.set()
            except (OSError, ValueError) as exc:
                row.update(status='api_failure', exception_type=type(exc).__name__, retryable=True)
            row['latency_seconds'] = time.monotonic() - start
            write_json(destination, row, True)
            with self.lock:
                if row.get('usage', {}).get('total_tokens') is not None:
                    self.spent += row['usage']['total_tokens'] - reserve
            if not row['retryable'] or attempt == config['max_infrastructure_retries']:
                return row
            time.sleep(3)
        raise AssertionError('Unreachable retry loop')

    def unit(self, q: dict, task: dict) -> dict:
        destination = self.units / (q['request_id'] + '.json')
        if destination.exists():
            return read_json(destination)
        if self.halt.is_set():
            return {'status': 'not_attempted'}
        method = q['method']
        phase = 'extract' if method == 'M2' else 'diagnose'
        prompt = render(task, method, phase)
        if digest(prompt) != q['prompt_sha256']:
            raise ValueError('Frozen queue prompt changed')
        response = self.call(q, phase, prompt)
        if response['status'] in ('budget_exhausted', 'blocked_after_service_failure'):
            return response
        prediction, errors = None, []
        supplemental = False
        if response['status'] == 'api_success' and response.get('finish_reason') != 'length':
            if method == 'M2' and isinstance(response.get('parsed'), dict):
                prediction = diagnose(task, response['parsed'])
                if prediction['needs_semantic_review']:
                    supplemental = True
                    second = self.call(q, 'supplement', render(task, method, 'supplement', prediction))
                    if second['status'] == 'api_success' and second.get('finish_reason') != 'length':
                        prediction, errors = normalize_final(task, second.get('parsed'))
                    else:
                        prediction = None
                    response = second
            else:
                prediction, errors = normalize_final(task, response.get('parsed'))
        result = {**q, 'fingerprint': self.frozen['fingerprint'], 'status': response['status'],
                  'prediction': prediction, 'normalization_errors': errors, 'supplemental_call': supplemental,
                  'parse_source': response.get('parse_source'), 'finish_reason': response.get('finish_reason'),
                  'schema_valid': prediction is not None and not errors,
                  'api_attempt_ids': [r['attempt_id'] for r in self.ledger if r['request_id'] == q['request_id']]}
        write_json(destination, result, True)
        return result


def execute(split: str, allow_online: bool, get_key: bool = False, limit: int | None = None) -> dict:
    if not allow_online:
        raise ValueError('Online disabled: explicit --online required')
    frozen = read_json(ROOT / 'freeze.json')
    if frozen['files'] != fingerprint():
        raise ValueError('Code/config/data/reference fingerprint changed; new version required')
    config = read_json(ROOT / 'config/judge.json')
    if split == 'holdout':
        gate = ROOT / 'dev_review.json'
        if not gate.exists() or read_json(gate).get('fingerprint') != frozen['fingerprint']:
            raise ValueError('Review development outputs and freeze gate before holdout')
    key = getpass.getpass('Fresh authorized API key (hidden): ') if get_key else os.environ.get(config['api_key_env'])
    if not key:
        write_json(ROOT / 'results/online_status.json', {'status': 'blocked', 'reason': 'missing_fresh_authorized_credential'})
        return {'status': 'blocked', 'reason': 'missing_fresh_authorized_credential'}
    runner = OnlineRunner(key, config, frozen)
    probe = runner.probe()
    if probe['status'] != 'verified':
        return probe
    tasks = {t['task_id']: t for t in load_tasks()}
    queue = [q for q in read_rows(ROOT / 'queue.jsonl') if q['split'] == split]
    # A deterministic optional preflight cap is development-only, never holdout selection.
    if limit is not None:
        if split != 'dev':
            raise ValueError('Holdout cannot be selectively limited')
        queue = queue[:limit]
    with concurrent.futures.ThreadPoolExecutor(max_workers=config['max_workers']) as pool:
        futures = {pool.submit(runner.unit, q, tasks[q['task_id']]): q for q in queue}
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            row = future.result()
            if i % 6 == 0 or row['status'] != 'api_success':
                print(json.dumps({'split': split, 'finished_units': i, 'queued_units': len(queue),
                                  'last_status': row['status'], 'physical_attempts': len(runner.ledger),
                                  'accounted_tokens': runner.spent}), flush=True)
    runner.key = ''
    status = {'status': 'stopped_after_service_or_budget_failure' if runner.halt.is_set() else 'queue_processed',
              'split': split, 'attempts': len(runner.ledger), 'accounted_tokens': runner.spent}
    write_json(ROOT / 'results/online_status.json', status)
    return status
