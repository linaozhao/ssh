"""Offline protocol, construction, matching, and bounded-resume regression tests."""
import copy
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from common import ROOT, digest, read_json, write_json
from construction import build, validate_groups, parse_controlled_text
from diagnosis import state_at, diagnose, temporal, validate_extraction
from protocol import render, normalize_final, parse_response
from scoring import core, basis_ok, score, aggregate
import runner


@pytest.fixture(scope='module')
def materials():
    return build()


def test_all_192_groups_independent_reference(materials):
    tasks, refs, manifest = materials
    report = validate_groups(tasks, refs, manifest)
    assert report['tasks'] == 192
    assert report['by_task'] == {'A': 72, 'B1': 72, 'B2': 48}
    assert report['split_counts'] == {'dev': 96, 'holdout': 96}


def test_unknown_not_false(materials):
    task = copy.deepcopy(materials[0][0])
    extraction = parse_controlled_text(task)
    task['evidence'] = []
    result = diagnose(task, extraction)
    facts = [c for c in result['checked_claims'] if c['kind'] == 'fact']
    assert facts and not any('F' in c['labels'] for c in facts)
    assert facts[0]['uncertainty_reason'] == 'unsupported_assertion_on_unknown_fact'


@pytest.mark.parametrize('variant,label', [('A1', 'F'), ('A2', 'R'), ('A3', 'I'), ('A4', 'unresolved'), ('A5', None), ('A6', 'F')])
def test_stance_and_explanation(materials, variant, label):
    tasks, refs, manifest = materials
    byid = {t['task_id']: t for t in tasks}
    for meta in manifest:
        if meta['variant'] != variant:
            continue
        t = byid[meta['task_id']]
        result = diagnose(t, parse_controlled_text(t))
        assert {l for c in result['claims'] for l in c['labels']} == ({label} if label else set())
        if variant == 'A5':
            assert not result['current_error']
            assert any(c['stance'] == 'rejected' for c in result['checked_claims'])


@pytest.mark.parametrize('variant,status', [('B1-1', 'unknown'), ('B1-2', 'newly_introduced'), ('B1-3', 'persistent'), ('B1-4', 'corrected'), ('B1-5', 'recurrence'), ('B1-6', 'post_update_reversion')])
def test_time_status_and_updates(materials, variant, status):
    tasks, _, manifest = materials
    byid = {t['task_id']: t for t in tasks}
    for meta in manifest:
        if meta['variant'] == variant:
            t = byid[meta['task_id']]
            result = diagnose(t, parse_controlled_text(t))
            assert result['claims'][0]['temporal_status'] == status
            if variant == 'B1-6':
                assert state_at(t, 3)['active_evidence'] != state_at(t, 4)['active_evidence']
                assert result['claims'][0]['active_version'] == 2
                assert result['claims'][0]['cited_version'] is None


def test_other_agent_not_self_history(materials):
    t = copy.deepcopy(next(t for t, m in zip(materials[0], materials[2]) if m['variant'] == 'B1-2'))
    t['messages'][0]['agent_id'] = 'different_agent'
    r = diagnose(t, parse_controlled_text(t))
    assert r['claims'][0]['temporal_status'] == 'unknown'


def test_hidden_history_not_used(materials):
    t = copy.deepcopy(next(t for t, m in zip(materials[0], materials[2]) if m['variant'] == 'B1-2'))
    t['messages'][-1]['visible_history_ids'] = []
    assert diagnose(t, parse_controlled_text(t))['claims'][0]['temporal_status'] == 'unknown'


def test_b2_no_target_leak_and_synchronous_visibility(materials):
    for t in materials[0]:
        for method in ('M0', 'M1', 'M2'):
            public = json.loads(render({**t, 'expected_labels': ['F'], 'variant': 'A1', 'split': 'holdout'}, method)[1]['content'])
            assert not {'expected_labels', 'variant', 'split', 'group_id', 'reference'} & public.keys()
            if t['task_kind'] == 'B2':
                assert 'target_message_id' not in public
        for m in t['messages']:
            mids = {x['message_id']: x for x in t['messages']}
            assert all((mids[x]['evidence_stage'], mids[x]['round']) < (m['evidence_stage'], m['round']) for x in m['visible_history_ids'])


def test_b2_first_rounds_and_no_error(materials):
    for t, r, m in zip(*materials):
        if t['task_kind'] != 'B2':
            continue
        pos = int(m['variant'].split('-')[1])
        if pos == 3:
            assert r['first_error_message_ids'] == [] and not r['current_error']
        else:
            assert len(r['first_error_message_ids']) == 1
            msg = next(x for x in t['messages'] if x['message_id'] == r['first_error_message_ids'][0])
            assert msg['round'] == pos


def test_extra_rule_not_destroy_core(materials):
    r = materials[1][0]['claims'][0]
    p = {**r, 'required_rule_ids': r['required_rule_ids'] + ['C999']}
    assert core(p, r, True)
    assert not basis_ok(p, r)


def test_matching_does_not_use_label(materials):
    r = materials[1][0]['claims'][0]
    assert core({**r, 'labels': ['R']}, r, True)


def test_failed_outputs_stay_in_denominators(materials):
    t, ref, m = materials[0][0], materials[1][0], materials[2][0]
    row = score(t, ref, None, m, 'M0')
    result = aggregate([row, {**row, 'variant': 'A2'}, {**row, 'variant': 'A3'}, {**row, 'variant': 'A4'}, {**row, 'variant': 'A5'}, {**row, 'variant': 'A6'}])
    assert result['detection']['recall'] == 0
    assert result['core_exact']['fn'] == 6


def test_empty_or_ambiguous_parsing():
    assert parse_response('not JSON')[0] is None
    assert parse_response('{"claims":[]}\n{"claims":[]}')[0] is None
    assert parse_response('```json\n{"claims":[]}\n```')[1] == 'unique_json_extraction'


def test_quote_offset_repair_is_visible(materials):
    t, r = materials[0][0], materials[1][0]
    p = copy.deepcopy(r)
    p['claims'][0]['start'] = -100
    normalized, errors = normalize_final(t, p)
    assert not errors and normalized['claims'][0]['offset_repaired']


def test_reproducible(materials):
    assert digest(build()) == digest(materials)


def test_resume_and_no_format_retry(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    cfg = read_json(ROOT / 'config/judge.json')
    obj = runner.OnlineRunner('test-placeholder', cfg, {'fingerprint': 'fixed'})
    q = {'request_id': 'test_request', 'split': 'dev'}
    with patch.object(obj, 'request', return_value={'choices': [{'message': {'content': 'not-json'}, 'finish_reason': 'stop'}], 'usage': {'total_tokens': 7}}) as req:
        a = obj.call(q, 'diagnose', [{'role': 'user', 'content': 'test'}])
        b = obj.call(q, 'diagnose', [{'role': 'user', 'content': 'test'}])
        assert req.call_count == 1 and a == b
        assert a['parsed'] is None
    with pytest.raises(ValueError, match='Payload changed'):
        obj.call(q, 'diagnose', [{'role': 'user', 'content': 'changed'}])
    with pytest.raises(ValueError, match='Fingerprint'):
        runner.OnlineRunner('test-placeholder', cfg, {'fingerprint': 'changed'})


def test_budget_blocks_before_network(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    cfg = {**read_json(ROOT / 'config/judge.json'), 'physical_attempt_cap': 0}
    obj = runner.OnlineRunner('test-placeholder', cfg, {'fingerprint': 'fixed'})
    with patch.object(obj, 'request') as req:
        assert obj.call({'request_id': 'q', 'split': 'dev'}, 'diagnose', [])['status'] == 'budget_exhausted'
        req.assert_not_called()


def test_network_retry_bounded(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    cfg = read_json(ROOT / 'config/judge.json')
    obj = runner.OnlineRunner('test-placeholder', cfg, {'fingerprint': 'fixed'})
    with patch.object(obj, 'request', side_effect=OSError('offline')), patch('runner.time.sleep'):
        result = obj.call({'request_id': 'q', 'split': 'dev'}, 'diagnose', [])
        assert result['status'] == 'api_failure'
        assert len(obj.ledger) == 2


def test_resume_crashed_attempt_not_duplicated(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    cfg = read_json(ROOT / 'config/judge.json')
    obj = runner.OnlineRunner('test-placeholder', cfg, {'fingerprint': 'fixed'})
    obj.ledger.append({'attempt_id': 'q_diagnose_0', 'retry': False})
    with patch.object(obj, 'request') as req:
        result = obj.call({'request_id': 'q', 'split': 'dev'}, 'diagnose', [])
        assert result['status'] == 'unresolved_inflight_attempt'
        req.assert_not_called()


def test_no_online_without_explicit_flag():
    with pytest.raises(ValueError, match='Online disabled'):
        runner.execute('dev', False)


def test_m2_does_not_use_reference_parser(materials):
    t = materials[0][0]
    extracted = parse_controlled_text(t)
    with patch('construction.parse_controlled_text', side_effect=AssertionError('Reference parser must never run')):
        assert diagnose(t, extracted)['current_error']


def test_no_false_post_update_reversion_without_acceptance(materials):
    t = copy.deepcopy(next(t for t, m in zip(materials[0], materials[2]) if m['variant'] == 'B1-6'))
    deleted = t['messages'].pop(1)['message_id']
    t['messages'][-1]['visible_history_ids'].remove(deleted)
    result = diagnose(t, parse_controlled_text(t))
    assert result['claims'][0]['temporal_status'] != 'post_update_reversion'


def test_b2_agent_and_type_coverage(materials):
    from collections import Counter
    agents, labels = Counter(), Counter()
    for t, r, m in zip(*materials):
        if m['variant'] != 'B2-0':
            continue
        agents[r['claims'][0]['agent_id']] += 1
        labels.update(r['claims'][0]['labels'])
    assert set(agents.values()) == {4}
    assert labels == {'F': 4, 'R': 4, 'I': 4}


def test_extra_evidence_does_not_erase_core(materials):
    r = materials[1][0]['claims'][0]
    p = {**r, 'conflicting_evidence_ids': r['conflicting_evidence_ids'] + ['unrelated']}
    assert core(p, r, False)
    assert not basis_ok(p, r)


def test_reference_version_not_cited_version(materials):
    for t, r, m in zip(*materials):
        if m['variant'] == 'B1-6':
            c = r['claims'][0]
            assert c['active_version'] == 2
            assert c['cited_version'] is None
            assert c['cited_evidence_ids'] == []
