# v4.1 Factorized Difficulty Generator Report

## Scope

v4.1 refines the additive v4 generation path. The existing v3 `generate_item()` and v3 validator remain unchanged, as do Gold construction, matrix computation, and violation-signature computation.

## Refinements

1. DS1 now uses the dynamic threshold `ceil(k/2)`: CL1=2, CL2=3, CL3=4.
2. DS1 signatures are sampled without replacement whenever three valid subsets exist.
3. IL2 now adds two scenario-compatible non-target work facts per candidate.
4. Candidate prose contains no explicit background or irrelevance cue.
5. Question intro/ending choices are recorded by exact `template_id` and balanced across each cell.

## Factor Definitions

| Factor | Level | Operational definition |
| --- | --- | --- |
| Constraint load | CL1 / CL2 / CL3 | 3 / 5 / 7 independently sampled constraints |
| Distractor similarity | DS1_far | Every wrong option violates at least ceil(k/2): 2 / 3 / 4 |
| Distractor similarity | DS2_medium | Exactly one wrong option violates 1 constraint; two violate at least 2 |
| Distractor similarity | DS3_near | Every wrong option violates exactly 1 constraint |
| Information load | IL1_low | Only target constraint facts are displayed |
| Information load | IL2_high | Two domain-relevant non-target facts are added per candidate |

## Generation Summary

- Output: `data/multi_constraint_v4_1_prototype.jsonl`
- Generator version: `4.1`
- Global seed: `42`
- Difficulty cells: 18
- Items per cell: 10
- Requested items: 180
- Generated items: 180
- Attempts: 180
- Retries: 0
- Generation failures: 0
- Validation failures: 0
- Generation warnings: 0

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
- Wrong-option violation counts: `{1: 240, 2: 97, 3: 81, 4: 75, 5: 40, 6: 6, 7: 1}`
- Displayed non-target facts: 720
- Items with duplicate wrong signatures: 0

## Validation Results

- Validated items: 180 / 180
- Validation pass rate: 1.000
- Gold candidates satisfying all constraints: PASS
- Stored matrices matching independent recomputation: PASS
- Stored violation signatures matching independent recomputation: PASS
- Dynamic DS1 thresholds and DS2/DS3 patterns: PASS
- Non-target facts outside formal attributes: PASS
- Non-target facts preserving constraint evaluation: PASS
- Scenario relevance of non-target facts: PASS

## Current Limitations

- v4.1 factors are controlled variables, not empirical difficulty labels.
- Non-target facts use deterministic English templates and still require model calibration.
- DS3 represents three distinct one-constraint failures, so CL2/CL3 cannot expose every constraint in an error option.
- No model inference, MAD debate, or drift classification was run.
