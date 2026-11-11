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

- The original R2 configuration is restricted to physical GPU4, with no fallback.
  The separately authorized `experiment_gpu2_shared_r2_20261110.json` permits
  sharing physical GPU2, checks its UUID before launch, reserves at least 1 GiB
  free memory, and never terminates another user's process.
- Judge disabled by default; only `JUDGE_API_KEY_V3_NEW`, no old-variable fallback.
- The requested DeepSeek-v4.1 flash provider ID must be independently verified.
- No secret value or secret fingerprint is stored in project artifacts.
- No real-trajectory Judge queue runs in this stage.
- Mock clients require explicit software mode and cannot be program experiment results.
- Raw future responses remain local by default; commit manifests and smaller summaries.

## GitHub Archive

The authorized 2026-11-11 upload includes the completed run's raw responses and
checkpoints as a compressed, SHA-256-verified bundle. See [archive instructions](artifacts/README.md).
Source, data, reports and blank human-annotation materials remain directly
browsable in the repository. No new inference or human evaluation is started.

## Authorized Official-API Continuation (2026-11-10)

The independent run is `cbm_drift_v3_shared_history_gpu2_20261110_v1`.
Its new data live in `data/gpu2_shared_20261110/`; old R2 data/results remain
unchanged. The official API configuration uses `https://api.deepseek.com` and
the authenticated `deepseek-flash` model ID. The provider documents this ID as
DeepSeek-V4.1-Flash; the `/models` probe is saved with the run.

`scripts/run_official_judge.py` obtains the key through a hidden prompt, holds
it only in the running process, and clears it on exit. Never supply a key in
command-line arguments, tracked files, or logs.

The first 12 responses exposed an evidence-version compatibility issue: the
provider used integer versions from the supplied evidence table, while the
validator expected full evidence IDs. `scripts/revalidate_judge.py` creates a
new directory with the same frozen requests and raw responses, resolving an
integer only when its explicit evidence references identify exactly one fact.
It records the old/new validation and inherits all attempts. It makes no new
model calls and never uses reference labels for normalization. Ambiguous
versions remain invalid. This continuation is stored in
`controlled_judge_official_flash_parser_v2/`; the original 12 outputs are kept.

Use `--judge-results-subdir controlled_judge_official_flash_parser_v2` with
`scripts/run_pipeline.py` to analyze/report that continuation. Raw records are
not duplicated in the experiment's unique-call total. The 132 real annotation
targets and their subsequent Judge evaluation remain deferred.

The completed run's original `input_tokens_counted` field has a documented
Transformers5.12.1 compatibility defect (BatchEncoding key count). Use
`context_token_recount.jsonl`, which independently matches every provider token
count; no raw responses are changed. The subsequent counter and shutdown fixes
have regression tests and archived pre-fix execution sources. This completed
run is read-only; future inference requires a new run ID, not a resume under
changed source fingerprints. See `RUNBOOK_ZH.md` for details.

## Tests

From the repository root:

```bash
pytest -q -o addopts='' experiments/cbm_drift_diagnostic_v3/tests experiments/cbm_drift_diagnostic_v2/tests
python -m compileall -q experiments/cbm_drift_diagnostic_v3/src experiments/cbm_drift_diagnostic_v3/scripts
git diff --check
```
