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
