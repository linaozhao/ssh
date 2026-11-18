"""Reference-independent checking of extracted public claims and visible history.

This module never loads references, group relations or construction variants.
Unknown official facts remain unknown. Claimed and effective versions are separate.
"""
from __future__ import annotations

from typing import Any
from cbm_drift_v3.state import replay_evidence, solve_candidate_set


def state_at(task: dict, stage: int) -> dict:
    replay = replay_evidence(e for e in task['evidence'] if e['appearance_stage'] <= stage)
    return {**replay, **solve_candidate_set(task['rules'], replay['active_evidence'])}


def structured_context(task: dict) -> list[dict]:
    """State is computed only from public official inputs, not intended errors."""
    return [{'evidence_stage': s, **state_at(task, s)}
            for s in sorted({m['evidence_stage'] for m in task['messages']})]


def validate_extraction(task: dict, extracted: dict) -> tuple[list[dict], list[str]]:
    messages = {m['message_id']: m for m in task['messages']}
    claims, errors = [], []
    if not isinstance(extracted, dict) or not isinstance(extracted.get('claims'), list):
        return [], ['extraction_schema']
    for idx, claim in enumerate(extracted['claims']):
        if not isinstance(claim, dict):
            errors.append(f'{idx}:not_object')
            continue
        m = messages.get(claim.get('message_id'))
        quote = claim.get('quote')
        if not m or not isinstance(quote, str) or not quote:
            errors.append(f'{idx}:unknown_message_or_empty_quote')
            continue
        start, end = claim.get('start'), claim.get('end')
        # Unique verbatim quotes permit deterministic offset repair; preserve audit.
        repaired = False
        if type(start) is not int or type(end) is not int or m['text'][start:end] != quote:
            if m['text'].count(quote) != 1:
                errors.append(f'{idx}:invalid_span')
                continue
            start = m['text'].index(quote)
            end, repaired = start + len(quote), True
        kind = claim.get('kind')
        if kind not in ('fact', 'rule', 'decision') or claim.get('stance') not in ('asserted', 'quoted', 'rejected', 'hypothetical'):
            errors.append(f'{idx}:kind_or_stance')
            continue
        if claim.get('candidate_id') not in task['candidates']:
            errors.append(f'{idx}:candidate')
            continue
        if kind in ('fact', 'rule') and (claim.get('attribute') not in {r['attribute'] for r in task['rules']} or type(claim.get('value')) is not bool):
            errors.append(f'{idx}:attribute_or_value')
            continue
        if kind == 'rule' and claim.get('rule_id') not in {r['id'] for r in task['rules']}:
            errors.append(f'{idx}:rule')
            continue
        if kind == 'decision' and claim.get('decision') not in ('retain', 'exclude'):
            errors.append(f'{idx}:decision')
            continue
        claims.append({**claim, 'start': start, 'end': end, 'offset_repaired': repaired,
                       'agent_id': m['agent_id'], 'evidence_stage': m['evidence_stage'], 'round': m['round']})
    return claims, errors


def check_claims(task: dict, claims: list[dict]) -> list[dict]:
    """Evaluate formal predicates without hallucinating unexpressed premises."""
    rules = {r['id']: r for r in task['rules']}
    out = []
    for claim in claims:
        state = state_at(task, claim['evidence_stage'])
        facts = {(f['candidate_id'], f['attribute']): f for f in state['active_evidence'] if f['fact_kind'] == 'target'}
        cand, attr = claim['candidate_id'], claim.get('attribute')
        fact = facts.get((cand, attr))
        rule = next((r for r in task['rules'] if r['attribute'] == attr), None)
        result = {**claim, 'labels': [], 'current_error': False, 'uncertainty_reason': None,
                  'conflicting_evidence_ids': [], 'required_rule_ids': [],
                  'active_version': fact['version'] if fact else None,
                  'cited_version': claim.get('cited_version'), 'cited_evidence_ids': claim.get('cited_evidence_ids', [])}
        if claim['stance'] != 'asserted':
            out.append(result)
            continue
        if claim['kind'] == 'fact':
            if fact is None:
                result['uncertainty_reason'] = 'unsupported_assertion_on_unknown_fact'
            elif claim['value'] != fact['value']:
                result.update(current_error=True, labels=['F'], conflicting_evidence_ids=[fact['evidence_id']])
        elif claim['kind'] == 'rule':
            actual = rules[claim['rule_id']]
            if attr != actual['attribute'] or claim['value'] != actual['required_value']:
                result.update(current_error=True, labels=['R'], required_rule_ids=[actual['id']])
        elif claim['kind'] == 'decision':
            correct = (claim['decision'] == 'retain') == (cand in state['oracle'])
            if not correct:
                premises = [c for c in claims if c['message_id'] == claim['message_id'] and c['candidate_id'] == cand and c['stance'] == 'asserted']
                wrong_premise, decisive = False, []
                for p in premises:
                    if p['kind'] == 'fact':
                        f = facts.get((cand, p['attribute']))
                        wrong_premise |= f is not None and p['value'] != f['value']
                        r = next((r for r in task['rules'] if r['attribute'] == p['attribute']), None)
                        explicit_rule = any(q['kind'] == 'rule' and q['rule_id'] == r['id'] and q['value'] == r['required_value'] and q['attribute'] == r['attribute'] for q in premises) if r else False
                        if f and r and explicit_rule and p['value'] == f['value'] and f['value'] != r['required_value'] and claim['decision'] == 'retain':
                            decisive.append((f, r))
                    elif p['kind'] == 'rule':
                        r = rules[p['rule_id']]
                        wrong_premise |= p['attribute'] != r['attribute'] or p['value'] != r['required_value']
                result['current_error'] = True
                if wrong_premise:
                    # Explained F/R errors are represented by those premise claims.
                    result['explained_by_premise_error'] = True
                elif decisive:
                    f, r = decisive[0]
                    result.update(labels=['I'], attribute=f['attribute'], required_rule_ids=[r['id']],
                                  conflicting_evidence_ids=[f['evidence_id']], active_version=f['version'])
                else:
                    result.update(labels=['unresolved'], uncertainty_reason='insufficient_explicit_premises')
        if rule and result['labels'] == ['F']:
            result['required_rule_ids'] = [rule['id']]
        out.append(result)
    return out


def temporal(task: dict, current: dict, checked: list[dict]) -> tuple[str, list[str]]:
    """Align same-agent same-kind same-object history through explicit visibility."""
    m = next(m for m in task['messages'] if m['message_id'] == current['message_id'])
    allowed = set(m['visible_history_ids'])
    prior = [c for c in checked if c['message_id'] in allowed and c['agent_id'] == current['agent_id']
             and c['kind'] == current['kind'] and c['candidate_id'] == current['candidate_id']
             and c.get('attribute') == current.get('attribute') and c['stance'] == 'asserted'
             and c.get('uncertainty_reason') is None]
    prior.sort(key=lambda c: (c['evidence_stage'], c['round']))
    # Ignore other agents and absence of a claim, even if the window is complete.
    if not prior:
        return ('unknown' if current['current_error'] else 'no_change_observed'), []
    last = prior[-1]
    if not current['current_error']:
        return ('corrected' if last['current_error'] else 'no_change_observed'), [last['message_id']]
    if last['current_error']:
        return 'persistent', [last['message_id']]
    if current['kind'] == 'fact':
        active = next((f for f in state_at(task, current['evidence_stage'])['active_evidence']
                       if f.get('candidate_id') == current['candidate_id'] and f.get('attribute') == current.get('attribute')), None)
        if active and active['event_type'] == 'correction':
            old = next(f for f in task['evidence'] if f['evidence_id'] == active['supersedes_evidence_id'])
            old_seen = [p for p in prior if p['evidence_stage'] < active['appearance_stage'] and p.get('value') == old['value']]
            if old_seen and current['value'] == old['value'] and last['evidence_stage'] >= active['appearance_stage'] and last['value'] == active['value']:
                return 'post_update_reversion', [old_seen[-1]['message_id'], last['message_id']]
    wrong = [p for p in prior[:-1] if p['current_error']]
    if wrong:
        return 'recurrence', [wrong[-1]['message_id'], last['message_id']]
    return 'newly_introduced', [last['message_id']]


def diagnose(task: dict, extraction: dict) -> dict:
    """M2 deterministic second stage. No intended categories are inputs."""
    claims, errors = validate_extraction(task, extraction)
    checked = check_claims(task, claims)
    for c in checked:
        c['temporal_status'], c['support_message_ids'] = temporal(task, c, checked)
    if task['task_kind'] == 'B2':
        events = [c for c in checked if c['current_error'] and c['labels']]
        earliest = min(((c['evidence_stage'], c['round']) for c in events), default=None)
        selected = [c for c in events if (c['evidence_stage'], c['round']) == earliest]
    else:
        target = [c for c in checked if c['message_id'] == task['target_message_id'] and c['stance'] == 'asserted']
        selected = [c for c in target if c['current_error'] and c['labels']]
        if not selected:
            selected = [c for c in target if c['temporal_status'] == 'corrected']
    has_error = any(c['current_error'] for c in selected)
    uncertain = bool(errors or extraction.get('uncertainties') or not checked)
    return {'current_error': has_error if not uncertain else None, 'claims': selected,
            'first_error_message_ids': sorted({c['message_id'] for c in selected if c['current_error']}) if task['task_kind'] == 'B2' else [],
            'no_error': not has_error if not uncertain else None,
            'uncertainty_reason': '; '.join(errors + list(extraction.get('uncertainties', []))) or None,
            'extraction_validation_errors': errors, 'checked_claims': checked,
            'needs_semantic_review': uncertain}
