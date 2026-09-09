# v4 Factorized Difficulty Generator Report

## Scope

The v4 path is additive. The existing v3 `generate_item()` and v3 validator remain unchanged. Items are generated directly from the same language-independent Boolean attributes and are then realized with deterministic English templates.

## Architecture

1. `DifficultyConfig` validates three independent factors and maps CL1/CL2/CL3 to 3/5/7 constraints.
2. `generate_v4_item()` samples a scenario and formal constraints, creates one Gold candidate, and constructs distractors from factor-controlled violation signatures.
3. IL2 background facts are stored separately from formal candidate attributes and are only added to candidate prose.
4. `validate_v4_item()` independently recomputes the matrix and signatures, validates the DS pattern, and confirms that adding irrelevant fact keys cannot change constraint evaluation.
5. `generate_v4_pool()` traverses the complete 3 x 3 x 2 factorial design with a fixed count per cell.

## Factor Definitions

| Factor | Level | Operational definition |
| --- | --- | --- |
| Constraint load | CL1 / CL2 / CL3 | 3 / 5 / 7 independently sampled constraints |
| Distractor similarity | DS1_far | Every wrong option violates at least 3 constraints |
| Distractor similarity | DS2_medium | Exactly one wrong option violates 1 constraint; two violate at least 2 |
| Distractor similarity | DS3_near | Every wrong option violates exactly 1 constraint |
| Information load | IL1_low | Only constraint-relevant facts are displayed |
| Information load | IL2_high | Two non-evaluative background facts are added per candidate |

## Generation Summary

- Output: `data/multi_constraint_v4_pool.jsonl`
- Global seed: `42`
- Difficulty cells: 18
- Items per cell: 10
- Requested items: 180
- Generated items: 180
- Attempts: 180
- Retries: 0
- Generation failures: 0
- Validation failures: 0

## Cell Distribution

| Constraint load | Distractor similarity | Information load | Items |
| --- | --- | --- | --- |
| CL1 | DS1_far | IL1_low | 10 |
| CL1 | DS1_far | IL2_high | 10 |
| CL1 | DS2_medium | IL1_low | 10 |
| CL1 | DS2_medium | IL2_high | 10 |
| CL1 | DS3_near | IL1_low | 10 |
| CL1 | DS3_near | IL2_high | 10 |
| CL2 | DS1_far | IL1_low | 10 |
| CL2 | DS1_far | IL2_high | 10 |
| CL2 | DS2_medium | IL1_low | 10 |
| CL2 | DS2_medium | IL2_high | 10 |
| CL2 | DS3_near | IL1_low | 10 |
| CL2 | DS3_near | IL2_high | 10 |
| CL3 | DS1_far | IL1_low | 10 |
| CL3 | DS1_far | IL2_high | 10 |
| CL3 | DS2_medium | IL1_low | 10 |
| CL3 | DS2_medium | IL2_high | 10 |
| CL3 | DS3_near | IL1_low | 10 |
| CL3 | DS3_near | IL2_high | 10 |

## Marginal Distribution

- Constraint load: `{'CL1': 60, 'CL2': 60, 'CL3': 60}`
- Constraint counts: `{3: 60, 5: 60, 7: 60}`
- Distractor similarity: `{'DS1_far': 60, 'DS2_medium': 60, 'DS3_near': 60}`
- Information load: `{'IL1_low': 90, 'IL2_high': 90}`
- Gold positions: `{'A': 45, 'B': 45, 'C': 45, 'D': 45}`
- Scenarios: `{'availability_selection': 60, 'expert_recruitment': 60, 'project_assignment': 60}`
- Wrong-option violation counts: `{1: 240, 2: 51, 3: 152, 4: 59, 5: 33, 6: 4, 7: 1}`
- Displayed irrelevant facts: 720

## Validation Results

- Validated items: 180 / 180
- Validation pass rate: 1.000
- Gold candidates satisfying all constraints: PASS
- Stored matrices matching independent recomputation: PASS
- Stored violation signatures matching independent recomputation: PASS
- Near-distractor one-violation rules: PASS
- Irrelevant facts excluded from formal evaluation: PASS

## Boolean Boundary Note

For `CL1 x DS1_far`, a wrong option must violate at least three of exactly three Boolean constraints. All three distractors therefore necessarily have the same formal signature `[C1, C2, C3]`. v4 permits this mathematically unavoidable duplicate while still requiring unique names and a unique Gold. The v3 uniqueness rule is unchanged.

Duplicate-signature cell counts observed: `{'CL1__DS1_far__IL1_low': 10, 'CL1__DS1_far__IL2_high': 10}`

## Current Limitations

- v4 factor levels control generation structure; they are not yet empirical difficulty labels.
- Irrelevant facts are simple deterministic background statements and have not been calibrated with models.
- DS3 samples three one-constraint violations, so with CL2/CL3 not every constraint is represented by a distractor.
- No model inference, MAD debate, or drift classification was run in this stage.
