"""Reproducible CPU-only prepare / run / analyze entrypoint."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from runner import prepare_run, execute
from scoring import analyze


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('command', choices=['prepare', 'run', 'analyze'])
    parser.add_argument('--split', choices=['dev', 'holdout'], default='dev')
    parser.add_argument('--online', action='store_true')
    parser.add_argument('--prompt-key', action='store_true')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    if args.command == 'prepare':
        print(prepare_run()['fingerprint'])
    elif args.command == 'run':
        print(execute(args.split, args.online, args.prompt_key, args.limit))
    else:
        analyze()
        print('reports/RESULTS_ZH.md updated')


if __name__ == '__main__':
    main()
