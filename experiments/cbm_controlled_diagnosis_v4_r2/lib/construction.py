"""Frozen controlled groups plus a separate finite-language interpretation pass.

The verification parser reads actual text and official evidence, never variants or
expected labels. Natural-language coverage is deliberately bounded and documented.
"""
from __future__ import annotations

import copy
import re
from collections import Counter

from common import ROOT, REPO, digest, read_rows, write_json, write_rows, write_text, span
from diagnosis import state_at, diagnose
from mad_attr_filter.attributes import ATTRIBUTE_BY_KEY
from cbm_drift_v3.state import enumerate_candidate_set

SOURCE = REPO / 'experiments/cbm_drift_diagnostic_v3/data/gpu2_shared_20261110/evidence_sequences.jsonl'


def fact_sentence(attr: str, candidate: str, value: bool, style: int) -> str:
    spec = ATTRIBUTE_BY_KEY[attr]
    phrases = spec.candidate_true_templates if value else spec.candidate_false_templates
    return phrases[style % 3].format(name=f'Candidate {candidate}').rstrip('.') + '.'


def rule_sentence(rule: dict, candidate: str, value: bool, style: int) -> str:
    rid, attr, val = rule['id'], rule['attribute'], str(value).lower()
    if style == 0:
        return f'For candidate {candidate}, I apply {rid} as requiring {attr} = {val}.'
    return f'My eligibility test for candidate {candidate} under {rid} is that {attr} must be {val}.'


def decision_sentence(candidate: str, retain: bool, style: int) -> str:
    if style == 0:
        return f'Therefore I {"retain" if retain else "exclude"} candidate {candidate}.'
    return f'My decision is to {"retain" if retain else "exclude"} candidate {candidate}.'


def make_message(task_id: str, index: int, agent: int, stage: int, rnd: int, text: str, history: list[dict]) -> dict:
    return {'message_id': 'm_' + digest([task_id, index])[:14], 'agent_id': f'agent_{agent}',
            'evidence_stage': stage, 'round': rnd, 'text': text,
            'visible_history_ids': [m['message_id'] for m in history if (m['evidence_stage'], m['round']) < (stage, rnd)]}


def parse_controlled_text(task: dict) -> dict:
    """Read public sentences with an independent recognizer, not generation traces."""
    claims = []
    for m in task['messages']:
        text = m['text']
        # Scoped quotation/rejection: later asserted correction is not rejected.
        rejected = [(q.start(1), q.end(1)) for q in re.finditer(r'"([^"]+)"', text)
                    if ('I reject that claim.' in text or 'That quoted assertion is false.' in text)]
        for candidate in task['candidates']:
            for attr, spec in ATTRIBUTE_BY_KEY.items():
                if attr not in {r['attribute'] for r in task['rules']}:
                    continue
                for value, templates in ((True, spec.candidate_true_templates), (False, spec.candidate_false_templates)):
                    for template in set(templates):
                        phrase = template.format(name=f'Candidate {candidate}').rstrip('.') + '.'
                        for match in re.finditer(re.escape(phrase), text):
                            stance = 'rejected' if any(a <= match.start() and match.end() <= b for a, b in rejected) else 'asserted'
                            claims.append({'message_id': m['message_id'], 'kind': 'fact', 'candidate_id': candidate,
                                           'attribute': attr, 'value': value, 'stance': stance,
                                           'quote': match[0], 'start': match.start(), 'end': match.end(),
                                           'cited_evidence_ids': [], 'cited_version': None})
        patterns = [r'For candidate ([ABCD]), I apply (C\d+) as requiring (\w+) = (true|false)\.',
                    r'My eligibility test for candidate ([ABCD]) under (C\d+) is that (\w+) must be (true|false)\.']
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                c, rid, attr, val = match.groups()
                claims.append({'message_id': m['message_id'], 'kind': 'rule', 'candidate_id': c,
                               'rule_id': rid, 'attribute': attr, 'value': val == 'true', 'stance': 'asserted',
                               'quote': match[0], 'start': match.start(), 'end': match.end()})
        for match in re.finditer(r'(?:Therefore I|My decision is to) (retain|exclude) candidate ([ABCD])\.', text):
            decision, c = match.groups()
            claims.append({'message_id': m['message_id'], 'kind': 'decision', 'candidate_id': c,
                           'decision': decision, 'attribute': None, 'stance': 'asserted',
                           'quote': match[0], 'start': match.start(), 'end': match.end()})
    # Prevent multiple identical phrases from inflating reference counts.
    unique = {(c['message_id'], c['start'], c['end']): c for c in claims}
    return {'claims': list(unique.values()), 'uncertainties': []}


def base_task(sequence: dict, task_id: str, kind: str, stage: int) -> dict:
    evidence = [copy.deepcopy(e) for s in sequence['stages'][:stage] for e in s['events']]
    # Remove future correction annotations from observations.
    for e in evidence:
        e.pop('corrected_by', None)
    return {'task_id': task_id, 'task_kind': kind, 'task_instruction':
            'Retain candidates unless an active known fact violates a fixed requirement. Unknown is not false. '
            'Evaluate public claims, not private thoughts. Official updates only correct facts, never rules.',
            'rules': copy.deepcopy(sequence['rules']), 'evidence': evidence,
            'candidates': {k: v['name'] for k, v in sequence['candidate_map'].items()},
            'messages': [], 'history_scope': 'Only the listed visible messages; no unlisted prior belief may be inferred.'}


def build() -> tuple[list[dict], list[dict], list[dict]]:
    sequences = read_rows(SOURCE)
    families = sorted({s['family_id'] for s in sequences})
    assert len(families) == 12
    indexed = {(s['family_id'], s['branch_type']): s for s in sequences}
    tasks, refs, manifest = [], [], []

    def finish(task: dict, family: str, split: str, variant: str, intent: str | None, temporal_label: str | None = None) -> None:
        verified = diagnose(task, parse_controlled_text(task))
        assert not verified['needs_semantic_review'], task['task_id']
        labels = {x for c in verified['claims'] for x in c['labels']}
        if intent is not None:
            assert labels == ({intent} if intent else set()), (variant, labels, intent)
        if temporal_label:
            assert len(verified['claims']) == 1, (variant, verified)
            assert verified['claims'][0]['temporal_status'] == temporal_label, (variant, verified)
        for m in task['messages']:
            state = state_at(task, m['evidence_stage'])
            assert state['oracle'] == enumerate_candidate_set(task['rules'], state['active_evidence'])
            for mid in m['visible_history_ids']:
                p = next(x for x in task['messages'] if x['message_id'] == mid)
                assert (p['evidence_stage'], p['round']) < (m['evidence_stage'], m['round'])
        ref = {'task_id': task['task_id'], 'verification_status': 'program_verified',
               'human_verified': False, 'current_error': verified['current_error'],
               'first_error_message_ids': verified['first_error_message_ids'], 'claims': verified['claims']}
        tasks.append(task)
        refs.append(ref)
        manifest.append({'task_id': task['task_id'], 'group_id': family + ':' + task['task_kind'],
                         'family_id': family, 'base_item_id': indexed[(family, 'clean')]['base_item_id'],
                         'split': split, 'variant': variant, 'task_kind': task['task_kind'],
                         'input_sha256': digest(task), 'reference_sha256': digest(ref),
                         'changed_factor': {'A1': 'false_fact', 'A2': 'altered_rule', 'A3': 'invalid_inference',
                                            'A4': 'no_explanation', 'A5': 'rejection_and_correct_decision',
                                            'A6': 'paraphrase'}.get(variant, variant)})

    for fi, family in enumerate(families):
        split, style = ('dev', 0) if fi % 2 == 0 else ('holdout', 1)
        clean, update = indexed[(family, 'clean')], indexed[(family, 'update')]
        initial = base_task(clean, 'temporary', 'A', 3)
        # Use an explicitly declared publication prefix of the original events.
        # Never alter values to manufacture a decisive fact; unknowns stay unknown.
        full_initial = initial['evidence']
        for end in range(1, len(full_initial) + 1):
            initial['evidence'] = full_initial[:end]
            observation_stage = initial['evidence'][-1]['appearance_stage']
            state = state_at(initial, observation_stage)
            if any(len(vs) == 1 for vs in state['exclusions'].values()):
                break
        # Isolate one decisive known violation; all other requirements are satisfied/unknown.
        candidates = [(c, vs[0]) for c, vs in sorted(state['exclusions'].items()) if len(vs) == 1]
        if not candidates:
            raise ValueError(f'No unambiguous single-decision object in {family}')
        candidate, violation = candidates[0]
        rule = next(r for r in clean['rules'] if r['id'] == violation['rule_id'])
        attr, actual = rule['attribute'], violation['observed_value']
        correct_fact = fact_sentence(attr, candidate, actual, style)
        false_fact = fact_sentence(attr, candidate, not actual, style)
        correct_rule = rule_sentence(rule, candidate, rule['required_value'], style)
        wrong_rule = rule_sentence(rule, candidate, not rule['required_value'], style)
        bad, good = decision_sentence(candidate, True, style), decision_sentence(candidate, False, style)
        reject = (f'Another speaker claimed: "{false_fact}" I reject that claim. ' if style == 0 else
                  f'The assertion "{false_fact}" has been quoted here. That quoted assertion is false. ')
        texts = [f'{false_fact} {correct_rule} {bad}', f'{correct_fact} {wrong_rule} {bad}',
                 f'{correct_fact} {correct_rule} {bad}', bad,
                 f'{reject}{correct_fact} {correct_rule} {good}',
                 f'{fact_sentence(attr, candidate, not actual, 2)} {correct_rule} {bad}']
        for vi, (text, label) in enumerate(zip(texts, ['F', 'R', 'I', 'unresolved', '', 'F']), 1):
            tid = 't_' + digest([family, 'A', vi, 'r2'])[:16]
            task = base_task(clean, tid, 'A', observation_stage)
            task['evidence'] = copy.deepcopy(initial['evidence'])
            task['publication_scope'] = 'Controlled prefix of original observations; unlisted facts are unknown.'
            task['messages'] = [make_message(tid, 0, 1 + fi % 3, observation_stage, 0, text, [])]
            task['target_message_id'] = task['messages'][0]['message_id']
            finish(task, family, split, f'A{vi}', label)

        # B1 uses existing authorized correction events, never newly invented rule updates.
        corr = next(e for e in update['stages'][3]['events'] if e['event_type'] == 'correction')
        c, a, v = corr['candidate_id'], corr['attribute'], corr['value']
        new, old = fact_sentence(a, c, v, style), fact_sentence(a, c, not v, style)
        histories = [[], [(1, new)], [(1, old)], [(1, old)], [(1, old), (1, new)], [(3, old), (4, new)]]
        times = ['unknown', 'newly_introduced', 'persistent', 'corrected', 'recurrence', 'post_update_reversion']
        for vi, (history, expected_time) in enumerate(zip(histories, times), 1):
            tid = 't_' + digest([family, 'B1', vi, 'r2'])[:16]
            task = base_task(update, tid, 'B1', 4)
            target_stage = 4
            if vi != 6:
                # Publish a current-state snapshot, not the earlier update process.
                # Values/versions/text come from independent replay of original T4.
                active = state_at(task, 4)['active_evidence']
                fields = ('evidence_id', 'candidate_id', 'candidate_name', 'attribute', 'value', 'version', 'text', 'fact_kind')
                task['evidence'] = [{**{k: e[k] for k in fields if k in e}, 'event_type': 'observation', 'appearance_stage': 1} for e in active]
                task['publication_scope'] = 'Opening authoritative snapshot. No official correction occurs within the visible observation window; pre-window changes and prior beliefs are not observed.'
                target_stage = 1
            for j, (stage, text) in enumerate(history):
                task['messages'].append(make_message(tid, j, 1 + fi % 3, stage, j, text, task['messages']))
            text = new if vi == 4 else old
            task['messages'].append(make_message(tid, len(history), 1 + fi % 3, target_stage, len(history), text, task['messages']))
            task['target_message_id'] = task['messages'][-1]['message_id']
            finish(task, family, split, f'B1-{vi}', '' if vi == 4 else 'F', expected_time)

        # B2 has nine synchronous-round messages. Only one message contains an error.
        # Later messages independently use true premises, so no copied error is introduced.
        error_type = ['F', 'R', 'I'][fi % 3]
        bad_text = texts[['F', 'R', 'I'].index(error_type)]
        neutral = f'{correct_fact} {correct_rule} {good}'
        for vi in range(4):
            tid = 't_' + digest([family, 'B2', vi, 'r2'])[:16]
            task = base_task(clean, tid, 'B2', observation_stage)
            task['evidence'] = copy.deepcopy(initial['evidence'])
            task['publication_scope'] = 'Controlled prefix of original observations; unlisted facts are unknown.'
            for rnd in range(3):
                for agent in range(1, 4):
                    text = bad_text if vi == rnd and agent == 1 + (fi // 3 + fi) % 3 else neutral
                    task['messages'].append(make_message(tid, len(task['messages']), agent, observation_stage, rnd, text, task['messages']))
            assert 'target_message_id' not in task
            finish(task, family, split, f'B2-{vi}', error_type if vi < 3 else '')
    return tasks, refs, manifest


def validate_groups(tasks: list[dict], refs: list[dict], manifest: list[dict]) -> dict:
    byid, byref = {t['task_id']: t for t in tasks}, {r['task_id']: r for r in refs}
    assert len(byid) == len(tasks) == len(byref) == 192
    groups = {}
    for m in manifest:
        groups.setdefault(m['group_id'], []).append(m)
    checks = []
    for gid, members in groups.items():
        assert len({m['split'] for m in members}) == 1
        for m in members:
            t, r = byid[m['task_id']], byref[m['task_id']]
            actual = diagnose(t, parse_controlled_text(t))
            assert actual['current_error'] == r['current_error']
            assert actual['claims'] == r['claims']
            assert actual['first_error_message_ids'] == r['first_error_message_ids']
            checks.append({'task_id': t['task_id'], 'official_state': 'passed', 'reference_interpretation': 'passed',
                           'structure_visibility': 'passed', 'reference_level': 'program_verified'})
        if members[0]['task_kind'] == 'A':
            variants = {m['variant']: byid[m['task_id']] for m in members}
            for key in ('rules', 'evidence', 'candidates'):
                assert len({digest(t[key]) for t in variants.values()}) == 1
            decisions = []
            for name in ('A1', 'A2', 'A3', 'A4'):
                parsed = parse_controlled_text(variants[name])
                decisions.append([(c['candidate_id'], c['decision']) for c in parsed['claims'] if c['kind'] == 'decision'])
            assert all(d == decisions[0] for d in decisions)
            for name in ('A1', 'A6'):
                assert {l for c in byref[variants[name]['task_id']]['claims'] for l in c['labels']} == {'F'}
    splits = {}
    for m in manifest:
        splits.setdefault(m['family_id'], set()).add(m['split'])
    assert all(len(v) == 1 for v in splits.values())
    return {'status': 'passed', 'tasks': len(tasks), 'by_task': dict(Counter(t['task_kind'] for t in tasks)),
            'split_counts': dict(Counter(m['split'] for m in manifest)), 'checks': checks,
            'human_verified': 0, 'reference_limitation': 'Finite language parser shares formal evaluator with M2; not independent human semantic gold.'}


def prepare() -> None:
    tasks, refs, manifest = build()
    validation = validate_groups(tasks, refs, manifest)
    frozen = (ROOT / 'freeze.json').exists()
    for kind in ('A', 'B1', 'B2'):
        ids = {t['task_id'] for t in tasks if t['task_kind'] == kind}
        write_rows(ROOT / f'data/{kind}_inputs.jsonl', [t for t in tasks if t['task_id'] in ids], frozen)
        write_rows(ROOT / f'references/{kind}_references.jsonl', [r for r in refs if r['task_id'] in ids], frozen)
    write_rows(ROOT / 'data/group_manifest.jsonl', manifest, frozen)
    write_json(ROOT / 'data/offline_validation.json', validation, frozen)
    lines = ['# Controlled sample review (program verified, NOT human verified)', '']
    for m, t, r in zip(manifest, tasks, refs):
        lines += [f"## {m['split']} {m['variant']} {t['task_id']}", f"Family: {m['family_id']}",
                  'Rules: ' + '; '.join(f"{x['id']}: {x['natural_language']}" for x in t['rules']),
                  'Official evidence:', *[f"- {e['evidence_id']} (stage {e['appearance_stage']}): {e['text']}" for e in t['evidence']],
                  'Messages:', *[f"- {x['message_id']} {x['agent_id']} T{x['evidence_stage']} R{x['round']}: {x['text']}" for x in t['messages']],
                  'Reference: `' + str({'error': r['current_error'], 'claims': [(c['labels'], c['candidate_id'], c.get('attribute'), c['quote'], c['temporal_status']) for c in r['claims']]}) + '`', '']
    write_text(ROOT / 'review/samples.md', '\n'.join(lines), frozen)
