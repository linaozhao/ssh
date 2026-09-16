# CBM-Attr v1

CBM-Attr v1 is a CBM-inspired dynamic adaptation of this repository's v4.1
boolean attribute-filtering benchmark. It retains a finite candidate space and
uses formal turn-level evidence to calculate an exact candidate-set oracle.

It borrows the evidence-management questions of *When Should Models Change
Their Minds? Contextual Belief Management in Large Language Models* and its
official [CBM implementation](https://github.com/zjunlp/CBM): when a state
should stay fixed, when a correction should update it, and whether non-target
information changes it. It is not a reproduction of BeliefTrack's Rule
Discovery or Circuit Diagnosis tasks.

## Semantics

The requirements are visible from the first dynamic round. Candidate facts
arrive over time. The expected response is the set of candidates **not yet
eliminated** by current active evidence:

- A known violation excludes a candidate.
- An unknown required attribute does not exclude a candidate.
- Unknown does not mean false and does not prove full eligibility.
- A restatement does not change active evidence.
- A correction invalidates the named old evidence and supplies a new version.

The direct oracle is independently checked by enumerating every completion of
unknown boolean attributes.

## Conditions

- `A_original`: original one-shot, single-choice item.
- `B_source_set`: all source facts in one candidate-set request.
- `C_clean`: target evidence arrives over rounds 1-3; rounds 4-5 restate facts.
- `E_noise`: formally identical to `C_clean` plus two domain-compatible,
  non-target facts per candidate.
- `D_update`: forks from the actual `C_clean` conversation after round 3 and
  corrects every violated attribute of one deterministic wrong candidate.
- `P_snapshot`: an independent static request for every C/E round and D rounds
  4-5, containing active evidence but no previous model response.

The update operation only tests restoration of a previously eliminated
candidate. It does not cover arbitrary belief contraction or requirement
changes.

## Dataset

The source is the frozen v4.1 extension pool. Selection seed `20260916` chooses
72 items: four from each of 18 CL x DS x IL cells, with one Gold A/B/C/D item
per cell. Selection never reads model outcomes.

Each item and run has 26 logical requests:

```text
A(1) + B(1) + C(5) + E(5) + D-new-branch(2) + snapshots(12) = 26
72 items x 3 seeds x 26 = 5,616 requests
```

The 18-cell preflight uses one item and one repetition per cell, or 468
requests. When all fingerprints remain unchanged, those records are reused in
the formal run.

## Reproduce

From the repository root:

```bash
python experiments/cbm_attr_v1/scripts/prepare_dataset.py
python experiments/cbm_attr_v1/scripts/validate_dataset.py
pytest -q experiments/cbm_attr_v1/tests

python experiments/cbm_attr_v1/scripts/run_experiments.py --phase preflight --resume
python experiments/cbm_attr_v1/scripts/run_experiments.py --phase formal --resume
python experiments/cbm_attr_v1/scripts/analyze_results.py
```

The runner checks frozen data, configuration, prompt, and parser fingerprints
before resuming. A dynamic request is never reused across different histories.
API failures are retried only according to the frozen configuration; ordinary
wrong answers, format anomalies, and truncations remain experimental outcomes.

## Layout

- `config/experiment_config.json`: Qwen3-8B endpoint and frozen parameters.
- `data/selection_manifest.jsonl`: deterministic source selection.
- `data/source_items.jsonl`: complete local copies of selected source items.
- `data/episodes.jsonl`: clean, noise, and correction formal trajectories.
- `data/snapshots.jsonl`: active-evidence static controls.
- `data/request_plan.jsonl`: all logical calls and dependency links.
- `data/validation_report.json`: structural and semantic checks.
- `results/raw_outputs.jsonl`: actual messages, raw responses, parsing, usage,
  finish reason, and request errors.
- `results/turn_metrics.jsonl`: turn-level set metrics.
- `results/paired_statistics.csv`: retention, update, noise, and snapshot pairs.
- `results/parse_audit.jsonl`: every non-strict, invalid, or truncated response.
- `reports/CBM_ATTR_V1_REPORT.md`: Chinese experiment report.

## Limitations

Only Qwen3-8B is evaluated, each factor cell contains four source items, and
three samples do not prove permanent stability. Dynamic versus snapshot
differences jointly reflect dialogue organization, earlier responses, and
presentation. This single-agent experiment neither demonstrates MAD drift nor
identifies an internal cognitive mechanism.
