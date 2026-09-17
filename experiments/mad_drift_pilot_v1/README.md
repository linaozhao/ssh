# MAD Drift Pilot v1

This independent experiment compares homogeneous three-agent MAD with a
same-start self-revision control on both the original static attribute-filter
task and the CBM-inspired dynamic task. It does not modify v3, v4.1, the
540-item pool, or the prior CBM experiment.

## Design

- 18 source items, one from each CL x DS x source-IL cell, selected without
  reading model outcomes.
- Static task: three independent R0 answers, then two synchronous MAD rounds
  and two self-revision rounds forked from the same R0 responses.
- Dynamic task: C_clean and E_noise each have five evidence stages. Every
  stage first collects an isolated judgment, then forks into two synchronous
  MAD rounds and a shared-prior-history within-stage self-revision control.
- D_update reuses the actual C_clean MAD history through stage 3, then runs the
  correction and restatement stages.
- Three independent team roots use seeds 11, 22, and 33. Agent/request seeds
  are deterministically derived and differ between agents.

The self-revision branch at dynamic stage 2 or later can already contain peer
messages from earlier stages because the main MAD history is the common
prefix. It estimates the effect of adding peer communication at the current
stage, not the causal effect of never seeing peers over the whole trajectory.

## Candidate-set protocol v2

The prior concrete format example containing `A` and `C` was removed. The new
protocol describes the JSON fields in prose and never supplies a concrete
candidate set. Unknown, restatement, correction, and not-yet-eliminated
semantics are unchanged. The exact diff is frozen in
`data/candidate_set_prompt_v1_to_v2.diff`.

## Reproduce

From the repository root:

```bash
python experiments/mad_drift_pilot_v1/scripts/prepare_data.py
python experiments/mad_drift_pilot_v1/scripts/validate_data.py
pytest -q experiments/mad_drift_pilot_v1/tests

bash experiments/mad_drift_pilot_v1/scripts/launch_qwen_replicas.sh serve 0 8101
python experiments/mad_drift_pilot_v1/scripts/run_protocol_check.py
python experiments/mad_drift_pilot_v1/scripts/run_mad.py
python experiments/mad_drift_pilot_v1/scripts/analyze_results.py
```

The checked-in configuration lists all six endpoints used in the actual run.
The runner verifies data, configuration, and prompt fingerprints before
resume. It saves actual messages, message hashes, raw responses, parser state,
finish reason, token usage, endpoint, seed, and latency. Failed dependencies
are marked blocked; no conversation history is fabricated.

## Output layout

- `data/selection_manifest.jsonl`: deterministic 18-item selection.
- `data/source_items.jsonl`, `episodes.jsonl`, `snapshots.jsonl`: frozen source
  copies.
- `data/protocol_request_plan.jsonl`: 1,404 protocol-check calls.
- `data/mad_request_plan.jsonl`: 10,530 static and dynamic calls.
- `results/protocol_check/`: old/new protocol comparison and raw responses.
- `results/static/`: static MAD records and transitions.
- `results/cbm/`: condition-sharded CBM raw records and transitions.
- `results/paired_statistics.csv`: condition, stage, branch, and paired
  MAD/self-revision metrics.
- `results/review_queue.jsonl`: objective changes requiring semantic review.
- `reports/case_review.md`: programmatically selected review cases.
- `reports/MAD_DRIFT_PILOT_V1_REPORT.md`: Chinese summary report.

## Interpretation limits

Transition windows overlap, so their counts are not mutually exclusive.
Repeated agents, rounds, and seeds are not independent items. A changed answer
that matches a peer is an adoption signal, not proof of conformity or
sycophancy. Model explanations are output text, not evidence of an internal
mechanism. No complete frozen 15-category taxonomy or Judge configuration was
found in the repository, so this pilot reports objective events and review
candidates rather than inventing formal drift labels.

