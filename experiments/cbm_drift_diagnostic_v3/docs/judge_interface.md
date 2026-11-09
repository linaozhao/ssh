# Judge / Evaluation Interface (R2)

Implementation: `src/cbm_drift_v3/evaluation.py`, `judge.py`, dedicated tests
and metrics/rubric documentation. No old experiment is modified.

## Integration Contract

- `prepare_controlled_judge(cases, config, output_dir) -> dict`: offline only;
  writes a frozen 144-request manifest and JSONL queue from 72 cases. Exactly
  36 dev and 36 holdout cases, two protocols `direct` and `structured`.
  Six dev targets (12 existing requests) are marked as technical preflight.
- `render_package(case, protocol) -> dict`: reconstructs allowlisted raw
  materials. Structured gets only explicitly allowlisted computable state.
  References are never opened or accepted as an input file by this function.
- `validate_prediction(value, package) -> dict`: schema, exact quote/offset,
  object-ID and formal checks are separate; no semantic-label certification.
- `evaluate_controlled(predictions, references, *, allow_mock=False) -> dict`:
  separate dev/holdout and protocol summaries, paired differences. Pending,
  ambiguous and uncertain current-deviation references are not definite gold.
- `evaluate_events(predictions, references) -> dict`: category-independent
  one-to-one exact claim/object/span matching; all applicable reference claims
  stay in recall denominators, including unmatched messages.

Preferred case fields: `case_id`, `case_sha256`, `base_item_id`, `split`,
`schema_version`, `rules`, `evidence`, `history`, `target_message`, and
`computed_state`. `target_message` has `message_id`, `agent_id`,
`evidence_stage`, `round`, `text`. Raw case IDs/split/stratum/mutation/template
metadata remain queue-only. Alternate controlled-case field names can be
adapted in the renderer without reading reference labels.

References follow plan section 6.3: `expected_current_deviation`,
`expected_content_labels`, `expected_temporal_status`, `claims`, verification
metadata. Claim identity: message/agent/stage/round, exact quote and offsets,
`candidate_ids`, `attribute`, `rule_ids`. Classification is scored only after
fixed matching. `conflicting_evidence_ids`, `evidence_version`, `stance` and
`prior_support` remain attached to their own claim.

Configuration may be a judge mapping or contain a `judge` mapping. Only the
new `JUDGE_API_KEY_V3_NEW` is eligible. Default model configuration is
`deepseek-v4.1-flash`; that ID is explicitly **unverified** and is not silently
replaced. No live transport is invoked by preparation. Missing credentials
leave B blocked; software tests are not online evaluation.

The requested provider model ID is pending verification. A changed verified
configuration must use a new `results_subdir`, retaining this pending queue.
