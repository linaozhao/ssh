# Controlled Case Contract

Frozen scripted input/reference contract for the controlled-first R2 pilot.

## Public API

- `build_controlled(sequences: list[dict], output_dir: Path) -> dict`
- `validate_controlled(cases, references) -> dict`
- `judge.render_package(case, protocol) -> dict` allowlists raw materials.
  It never accepts or opens references.

The builder writes `cases.jsonl`, `expected_labels.jsonl`,
`reference_validation.json`, `coverage_manifest.json`, `split_manifest.json`,
and `freeze_manifest.json` under output_dir.
Its return value is the validation report plus artifact paths and hashes.
It makes no API calls. A different frozen output cannot be overwritten.

## Cases

Queue-only metadata: `case_id`, `case_sha256`, `schema_version`, `base_item_id`,
`family_id`, `split` (dev/holdout), `branch_type`, `source_variant_type`.
IDs are opaque hashes, not stratum or temporal labels. No `expected_*`,
stratum, mutation, or reference verification fields occur in cases.

Raw diagnostic materials:

- `task_text`, `candidate_map`, `rules` use the frozen sequence fields.
- `evidence` is the cumulative flat event log through the target stage;
  it preserves IDs, versions, appearance stages and correction/restatement links.
- `history_source` is always `scripted`, never natural model output.
- `history_scope`: `complete` and `trajectory_start` explicitly identify the
  defined scripted trajectory. Incomplete excerpts do NOT imply initial error.
- `history` is a list of messages; `target_message` is one message.
- Message fields: `message_id`, `agent_id`, `evidence_stage`, `round`, `text`,
  `own_previous_message_id`, `visible_peer_message_ids`, `parent_message_ids`.
  `text` is JSON with `answer_set` and `explanation`, matching the MAD protocol.
  Own judgments and legal prior-round peer snippets are distinguishable by agent.

The Judge renderer should allowlist raw materials, strip queue-only metadata,
and recompute structured state from evidence. Do not read expected_labels.jsonl
to render prompts. Structured aids may contain oracle/extra/omitted/three-valued
state, but not controlled content or temporal classifications.

## References

Plan section 6.3 fields plus per-claim `content_labels`, `current_deviation`,
`temporal_status`, `deviation_kind`, `claim_kind`, and `cited_evidence_ids`.
Offsets are half-open Python character indices into the exact message `text`,
not indices into the decoded explanation. `evidence_version` identifies the
active conflicting/supporting fact version; a cited superseded basis remains
separate. Quotes in `prior_support` name their own message and offsets.

Unknown-to-known assertions use F with `deviation_kind=unsupported_assertion`;
they are not called contradictions of known facts. Unexplained wrong answers
use unresolved. Update response values: `adapted`, `reverted`, `not_adapted`,
`not_applicable`. Primary time status is accompanied by claim-local statuses.

`case_sha256` hashes the case without its own hash field.
`reference_sha256` hashes the reference without its own hash field.
No human verification is claimed. Program verification concerns only the
restricted, explicitly documented controlled language, not arbitrary prose.

## Evaluation Boundary

Software tests, program-verified references, and online controlled evaluation
are separate. The builder reports actual built/verified counts and independent
coverage failures. Pending/ambiguous references never enter verified counts.
This 6/6 family split is a pilot controlled holdout, not natural-MAD validation.
