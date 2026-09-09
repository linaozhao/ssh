# English-First Multi-Constraint Attribute Filter Generator

This project generates deterministic boolean-attribute filtering items for MAD Constraint Drift benchmark development.
The formal task representation is language-independent, while the current generator realizes each task directly in English.

Current scope:

- Boolean attribute pool with strict polarity rules.
- Scenario-compatible constraint sampling.
- Gold candidate and distractor generation.
- Option-constraint matrix and violation signatures.
- English constraint and candidate realization.
- Structural validation, strict semantic validation, and lexical-overlap audit.
- A 100-item English Pilot v3 dataset.
- Independent Qwen3-8B and Llama-3.1-8B single-agent screening.
- Empirical difficulty, constraint-error, disagreement, and MAD-candidate analysis.
- A 27-item homogeneous Qwen/Llama small baseline MAD pilot with three agents and two revision rounds.
- Deterministic answer-transition, violation-set, peer-adoption, and consensus analysis.
- An additive v4.1 generator with independent constraint-load, distractor-similarity, and non-target information-load factors.

Not included in this stage:

- Full-scale or heterogeneous MAD experiments.
- The 15-category Drift Judge taxonomy.
- LLM paraphrasing.
- ProofWriter, SciFact, or EntailmentBank integration.
- Drift classification.
- Human annotation tools.

## Install

```bash
cd /data/zla/mad_attr_filter_generator
python -m pip install -r requirements.txt
```

Runtime generation uses the Python standard library. Tests require `pytest`.

## Generate English Pilot v3

```bash
python scripts/generate_pilot.py \
  --output data/pilot_en_v3.jsonl \
  --stats-output data/pilot_en_v3_statistics.json \
  --num-items 100 \
  --seed 42 \
  --examples-output data/pilot_en_v3_examples.md \
  --audit-output data/pilot_en_v3_semantic_audit.md \
  --lexical-output data/pilot_en_v3_lexical_audit.json
```

Outputs:

- `data/pilot_en_v3.jsonl`
- `data/pilot_en_v3_statistics.json`
- `data/pilot_en_v3_examples.md`
- `data/pilot_en_v3_semantic_audit.md`
- `data/pilot_en_v3_lexical_audit.json`

The English Pilot is the formal benchmark. `pilot_en_v3_zh_view.*` is a
human-readable Chinese translation view and is not used for model inference.

## Validate

```bash
python scripts/validate_dataset.py data/pilot_en_v3.jsonl
```

Stress test 1,000 temporary English items:

```bash
python scripts/validate_generation.py \
  --num-items 1000 \
  --seed 2026 \
  --strict-semantic
```

Run tests:

```bash
pytest -q
```

## Generate Factorized v4.1 Prototype

v4.1 is an additive generation path. It does not replace `generate_item()` or
change the v3 schema and datasets. Generate the current 18-cell prototype
with 10 items per cell:

```bash
python scripts/generate_v4_pool.py \
  --items-per-cell 10 \
  --output data/multi_constraint_v4_1_prototype.jsonl \
  --report-output v4_1_generator_report.md \
  --seed 42
```

Run the independent cell-level factor audit:

```bash
python scripts/audit_v4_factors.py \
  data/multi_constraint_v4_1_prototype.jsonl \
  --output v4_factor_audit.json \
  --refinement-report-output V4_1_REFINEMENT_REPORT.md
```

The three factors are independent:

- `constraint_load`: CL1, CL2, and CL3 produce 3, 5, and 7 constraints.
- `distractor_similarity`: DS1 uses a `ceil(k/2)` violation threshold, DS2 mixes one near miss with two clear errors, and DS3 uses three one-constraint near misses.
- `information_load`: IL1 displays only target facts; IL2 adds two scenario-compatible professional or scheduling facts per candidate without adding them to formal attributes.

Every v4.1 item contains `difficulty_factors` and `generation_metadata` while
preserving the Gold answer, formal constraints, matrix, and violation
signatures. The CLI reloads and independently validates the serialized JSONL
before writing the report.

## Single-Agent Screening

Model names, endpoints, generation parameters, seeds, and Qwen thinking mode
are defined in `config/single_agent_config.json`. Start the configured local
OpenAI-compatible model servers before inference, then run:

```bash
python scripts/run_single_agent.py --resume
python scripts/analyze_single_agent.py
```

Resume keys are `(item_id, model_alias, run_id)`. Existing runs are skipped.
`--retry-failed` retries API failures only; malformed model responses remain
completed experimental samples and are never regenerated.

Screening outputs:

- `results/single_agent_outputs.jsonl`: all raw and parsed independent responses.
- `results/single_agent_statistics.json`: model and grouped accuracy statistics.
- `results/single_agent_item_analysis.jsonl`: six-run item-level summaries.
- `results/constraint_error_statistics.json`: normalized constraint-error counts.
- `results/mad_candidate_items.jsonl`: all 100 items with screening metadata.
- `results/single_agent_examples.md`: representative manual inspection samples.
- `results/single_agent_report.md`: conclusions and MAD suitability assessment.
- `data/pilot_en_v3_with_empirical_difficulty.jsonl`: a separate enriched dataset.

## Small Baseline MAD Pilot

Prepare the deterministic 17-vulnerable plus 10-control manifest, run the two
homogeneous model families, and analyze the trajectories:

```bash
python scripts/prepare_mad_pilot.py
python scripts/run_mad_pilot.py --resume
python scripts/analyze_mad_pilot.py
```

The MAD runner checkpoints every `(item_id, model_family, agent_id, round)`.
Round 0 calls are independent; Rounds 1 and 2 expose only the previous natural
responses of the three same-family agents. Gold answers, matrices, constraint
IDs, and violation signatures are never included in model prompts.

MAD outputs:

- `results/mad_pilot_manifest.jsonl`: selected vulnerable and stable-control items.
- `results/mad_pilot_progress.jsonl`: call-level resumable checkpoints.
- `results/mad_pilot_trajectories.jsonl`: complete R0/R1/R2 trajectories.
- `results/mad_pilot_events.jsonl`: objective agent-level transitions.
- `results/mad_pilot_statistics.json`: model/group/round statistics.
- `results/mad_pilot_key_cases.md`: all harmful/corrective events and selected controls.
- `results/mad_pilot_report.md`: the baseline MAD findings.

## JSON Schema

Each item contains:

- `item_id`: item variant ID, e.g. `attr_en_000001_original`.
- `base_item_id`: base item ID.
- `generator_version`: `3.0-en`.
- `task_family`: `multi_constraint`.
- `task_type`: `attribute_filter`.
- `scenario`: one of `expert_recruitment`, `project_assignment`, or `availability_selection`.
- `language`: `en`.
- `option_closeness`: `easy`, `medium`, or `hard`.
- `structural_complexity`: `low`, `medium`, or `high`.
- `empirical_difficulty`: `null` in the original Pilot and assigned in the separate screening-enriched file.
- `question`: English natural-language item.
- `options`: A-D candidate descriptions.
- `gold_answer`: the single correct option.
- `constraints`: formal constraints plus English realization.
- `entities`: full structured candidate attributes and displayed facts.
- `option_constraint_matrix`: whether each option satisfies each constraint.
- `option_violation_signature`: violated constraint IDs per option.

## Strict Polarity Rules

Positive ability and qualification attributes can only be required as `true`.
Availability attributes can only be required as `true`.
Risk attributes can only be required as `false`.

Disabled as constraints:

- `requires_remote`
- `prefers_on_site_work`
- `prefers_long_term_project`

Replacement work-mode attributes:

- `can_work_remote = true`
- `can_work_onsite = true`

## Difficulty Fields

`option_closeness` describes how close distractors are to the Gold option:

- `easy`: wrong options violate 2, 2, and at least 2 constraints.
- `medium`: wrong options violate 1, 1, and 2 constraints.
- `hard`: all wrong options violate exactly 1 constraint.

`structural_complexity` is based on constraint count:

- `low`: 3 constraints.
- `medium`: 4 constraints.
- `high`: 5 constraints.

Neither field is an empirical model difficulty label.

## Known Limitations

- The benchmark uses deterministic English templates only.
- It does not use LLM paraphrasing.
- Screening results reflect the configured local model builds and sampling backend.
- Difficulty comes from tracking constraints and near-correct options, not from intentionally obscure language.

## v4.1 Single-Agent Calibration

The v4.1 prototype keeps the 18 factor cells separate from the v3 difficulty
fields. Calibration uses `difficulty_factors` and `metadata.difficulty_cell`
directly and never synthesizes `option_closeness` or `structural_complexity`.

Run the stratified 18-item preflight, then the formal 180-item experiment and
analysis:

```bash
python scripts/run_v4_1_calibration.py --phase preflight
python scripts/run_v4_1_calibration.py --phase formal --resume --reuse-preflight
python scripts/analyze_v4_1_calibration.py
```

The frozen configuration is `config/v4_1_calibration_config.json`. Results are
written under `results/v4_1_calibration/`. Each response stores the experiment,
dataset, configuration, prompt and protocol fingerprint through the aggregate
`experiment_fingerprint`; resume rejects mismatched or duplicate records.

The v4.1 parser separately records whether an A-D answer can be identified and
whether the complete response complies with the requested JSON schema. Text
fallback accepts only an unambiguous explicit final answer, not ordinary
mentions of candidates in the explanation. Parser revision 2 also recognizes
an exact A-D value in an otherwise malformed JSON `answer` field while keeping
`json_compliant=false`; conflicting explicit answers remain unresolved.
