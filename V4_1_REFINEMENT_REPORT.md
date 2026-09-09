# V4.1 Refinement Report

## 1. Changes

- Replaced the fixed DS1 threshold with `ceil(number_of_constraints / 2)`.
- Replaced hobby noise and explicit background cues with scenario-compatible non-target work facts.
- Added exact question-template IDs and a per-cell factor confound audit.
- Kept v3 generation, Gold construction, matrix computation, and violation-signature computation unchanged.

## 2. DS1 Definition

DS1 distractors must each violate at least `ceil(k/2)` constraints. The thresholds are CL1=2, CL2=3, and CL3=4. Signatures are sampled without replacement whenever at least three valid subsets exist.

## 3. IL2 Definition

IL2 adds two domain-relevant non-target facts per candidate. These facts are compatible with the current scenario, use keys outside the formal `ATTRIBUTE_POOL`, appear naturally in candidate prose, and are excluded from Gold, matrix, and violation-signature evaluation.

## 4. Prototype Generation

- Items: 180
- Cells: 18
- Constraint load: `{'CL1': 60, 'CL2': 60, 'CL3': 60}`
- Distractor similarity: `{'DS1_far': 60, 'DS2_medium': 60, 'DS3_near': 60}`
- Information load: `{'IL1_low': 90, 'IL2_high': 90}`
- Scenario: `{'availability_selection': 60, 'expert_recruitment': 60, 'project_assignment': 60}`
- Gold position: `{'A': 45, 'B': 45, 'C': 45, 'D': 45}`

## 5. Audit Summary

- All 18 cells present: True
- Equal cell sizes: True
- Scenario balance within one item per cell: True
- Gold balance within one item per cell: True
- Minimum template variants per cell: 9
- DS verification: True
- IL verification: True
- Full validation: True
- No obvious factor confounding detected: True
- Warnings: `[]`

## 6. Remaining Limitations

- Factor levels remain generation controls, not empirically calibrated model difficulty.
- Non-target facts are deterministic templates and may not distract all model families equally.
- Constraint attributes are sampled randomly within scenario rules, so the audit reports residual frequency variation.
- Question and option lengths intentionally differ across CL and IL levels; those are treatment effects, not balancing variables.
- No model inference or MAD experiment was run.
