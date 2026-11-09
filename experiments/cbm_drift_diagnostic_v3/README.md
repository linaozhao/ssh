# CBM Drift Diagnostic v3 R2

This directory is an independent, controlled-first implementation of
`MAD_drift_v3_Codex_plan_ZH.md`, revision `controlled-first-r2`.
Legacy v2 designs/results are read-only; no old responses count as new MAD.

Read `RUN_SUMMARY_ZH.md` for actual execution status and `RUNBOOK_ZH.md` for
reproduction. Generated plans and passing software tests are **not** completed
model experiments.

## Artifacts

- `data/evidence_sequences.jsonl`: 12 frozen families, four conditions, 48 sequences.
- `data/mad_request_plan.jsonl`: 324 shared-prefix + 864 suffix = 1,188 canonical requests.
- `data/branch_views.jsonl`: 48 views, 2,160 references, shared messages not duplicated.
- `data/controlled/`: 72 scripted cases, isolated references, 36/36 family-disjoint split.
- `results/<run_id>/controlled_judge/`: 144 queued requests, including a 12-request preflight subset.
- `annotation/deferred_real/`: 132 planned targets, blind materials and empty human templates.
- `data/controlled_rejected_prequeue_20261109/`: rejected development construction.
  Six compound-claim references had an overlong quote. They are retained for
  provenance, are not the frozen controlled dataset, and never entered an API queue.

The offline verifier parses a restricted English assertion language and checks
it against replayed source evidence. `program_verified` is not `human_verified`.
The holdout uses different source families but shares assertion syntax with dev.

## Safety Boundaries

- Physical GPU4 only, identity + UUID + owned service PID verified; no fallback.
- Judge disabled by default; only `JUDGE_API_KEY_V3_NEW`, no old-variable fallback.
- The requested DeepSeek-v4.1 flash provider ID must be independently verified.
- No secret value or secret fingerprint is stored in project artifacts.
- No real-trajectory Judge queue runs in this stage.
- Mock clients require explicit software mode and cannot be program experiment results.
- Raw future responses remain local by default; commit manifests and smaller summaries.

## Tests

From the repository root:

```bash
pytest -q -o addopts='' experiments/cbm_drift_diagnostic_v3/tests experiments/cbm_drift_diagnostic_v2/tests
python -m compileall -q experiments/cbm_drift_diagnostic_v3/src experiments/cbm_drift_diagnostic_v3/scripts
git diff --check
```
