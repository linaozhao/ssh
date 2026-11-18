"""Audit both development versions against the user's cumulative authorization."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from common import ROOT, read_json, read_rows, write_json


def main() -> None:
    config = read_json(ROOT / 'config/judge.json')
    experiments = [ROOT.parent / config['prior_experiment'], ROOT]
    rows = []
    for directory in experiments:
        ledger_path = directory / 'results/attempts.jsonl'
        ledger = read_rows(ledger_path) if ledger_path.exists() else []
        tokens, known, missing, costed = 0, 0, [], 0
        for r in ledger:
            p = directory / 'results/calls' / (r['attempt_id'] + '.json')
            observed = read_json(p).get('usage', {}).get('total_tokens') if p.exists() else None
            if observed is None:
                costed += r['reserved_tokens']
                missing.append(r['attempt_id'])
            else:
                tokens += observed
                costed += observed
                known += 1
        rows.append({'experiment': directory.name, 'physical_generation_attempts': len(ledger),
                     'calls_with_reported_token_usage': known, 'provider_reported_tokens': tokens,
                     'conservatively_accounted_tokens': costed, 'usage_unknown_attempts': missing})
    attempts = sum(r['physical_generation_attempts'] for r in rows)
    costed = sum(r['conservatively_accounted_tokens'] for r in rows)
    report = {'experiments': rows, 'cumulative_generation_attempts': attempts,
              'attempt_cap': config['physical_attempt_cap'], 'remaining_attempt_allowance': config['physical_attempt_cap'] - attempts,
              'conservatively_accounted_tokens': costed, 'token_cap': config['total_token_cap'],
              'status': 'within_budget' if attempts <= config['physical_attempt_cap'] and costed <= config['total_token_cap'] else 'exceeded',
              'note': 'Generation requests include aborted legacy attempts and every M2 extraction/follow-up. Non-generative /models checks are separate; monetary cost unknown.'}
    write_json(ROOT / 'results/cumulative_budget_audit.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
