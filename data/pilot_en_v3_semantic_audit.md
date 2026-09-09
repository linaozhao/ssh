# English Pilot v3 Semantic Audit

Total high-risk samples: 46

## attr_en_000003_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `low`
- Gold: `B`

### High-Risk Constraints


- C2: `has_conflict=False` -> The selected candidate must have no conflict of interest.

### Violation Signature

- A: ['C3']
- B: []
- C: ['C2']
- D: ['C1', 'C2']

## attr_en_000006_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `D`

### High-Risk Constraints


- C4: `has_schedule_conflict=False` -> Candidates with a scheduling conflict are ineligible.

### Violation Signature

- A: ['C3']
- B: ['C1', 'C4']
- C: ['C2']
- D: []

## attr_en_000007_original

- scenario: `expert_recruitment`
- option_closeness: `hard`
- structural_complexity: `low`
- Gold: `A`

### High-Risk Constraints


- C1: `has_schedule_conflict=False` -> The candidate must have no scheduling conflict.
- C2: `needs_supervision=False` -> Only candidates who can work independently without extra oversight are eligible.

### Violation Signature

- A: []
- B: ['C2']
- C: ['C3']
- D: ['C1']

## attr_en_000008_original

- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `D`

### High-Risk Constraints


- C1: `requires_extra_equipment=False` -> Candidates who need extra equipment support are ineligible.

### Violation Signature

- A: ['C2']
- B: ['C1']
- C: ['C3', 'C4']
- D: []

## attr_en_000009_original

- scenario: `expert_recruitment`
- option_closeness: `hard`
- structural_complexity: `low`
- Gold: `A`

### High-Risk Constraints


- C3: `has_conflict=False` -> Anyone with a conflict of interest is ineligible.

### Violation Signature

- A: []
- B: ['C3']
- C: ['C2']
- D: ['C1']

## attr_en_000011_original

- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `B`

### High-Risk Constraints


- C1: `has_schedule_conflict=False` -> The candidate must have no scheduling conflict.

### Violation Signature

- A: ['C1', 'C3']
- B: []
- C: ['C2']
- D: ['C4']

## attr_en_000017_original

- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `A`

### High-Risk Constraints


- C1: `requires_extra_equipment=False` -> The selected candidate must be able to participate without additional equipment.
- C3: `has_schedule_conflict=False` -> The candidate must have no scheduling conflict.

### Violation Signature

- A: []
- B: ['C2', 'C4']
- C: ['C3']
- D: ['C1']

## attr_en_000021_original

- scenario: `project_assignment`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `A`

### High-Risk Constraints


- C1: `has_schedule_conflict=False` -> The selected candidate must have a schedule that does not conflict with the project.

### Violation Signature

- A: []
- B: ['C1', 'C3']
- C: ['C3', 'C5']
- D: ['C2', 'C4', 'C5']

## attr_en_000032_original

- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `A`

### High-Risk Constraints


- C1: `needs_supervision=False` -> Only candidates who can work independently without extra oversight are eligible.
- C4: `has_schedule_conflict=False` -> The candidate must have no scheduling conflict.

### Violation Signature

- A: []
- B: ['C2']
- C: ['C4']
- D: ['C1', 'C3']

## attr_en_000033_original

- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `D`

### High-Risk Constraints


- C3: `needs_supervision=False` -> Only candidates who can work independently without extra oversight are eligible.
- C4: `requires_extra_equipment=False` -> The selected candidate must be able to participate without additional equipment.

### Violation Signature

- A: ['C1']
- B: ['C3', 'C4']
- C: ['C2']
- D: []

## attr_en_000035_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `B`

### High-Risk Constraints


- C3: `needs_supervision=False` -> The candidate must be able to work without additional supervision.

### Violation Signature

- A: ['C2']
- B: []
- C: ['C1', 'C3']
- D: ['C4']

## attr_en_000036_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `D`

### High-Risk Constraints


- C4: `needs_supervision=False` -> Additional supervision must not be required.

### Violation Signature

- A: ['C1']
- B: ['C2', 'C3']
- C: ['C4']
- D: []

## attr_en_000038_original

- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `D`

### High-Risk Constraints


- C2: `requires_extra_equipment=False` -> The candidate must not require additional specialized equipment.
- C4: `has_schedule_conflict=False` -> The candidate must have no scheduling conflict.

### Violation Signature

- A: ['C2']
- B: ['C1']
- C: ['C3', 'C4']
- D: []

## attr_en_000039_original

- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `low`
- Gold: `B`

### High-Risk Constraints


- C1: `has_schedule_conflict=False` -> The selected candidate must have a schedule that does not conflict with the project.
- C2: `requires_extra_equipment=False` -> The candidate must not require additional specialized equipment.

### Violation Signature

- A: ['C1', 'C3']
- B: []
- C: ['C3']
- D: ['C2']

## attr_en_000040_original

- scenario: `availability_selection`
- option_closeness: `hard`
- structural_complexity: `low`
- Gold: `C`

### High-Risk Constraints


- C1: `has_schedule_conflict=False` -> The candidate must have no scheduling conflict.

### Violation Signature

- A: ['C1']
- B: ['C3']
- C: []
- D: ['C2']

## attr_en_000041_original

- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `A`

### High-Risk Constraints


- C5: `requires_extra_equipment=False` -> Candidates who need extra equipment support are ineligible.

### Violation Signature

- A: []
- B: ['C1', 'C2', 'C3']
- C: ['C4', 'C5']
- D: ['C1', 'C3']

## attr_en_000042_original

- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `A`

### High-Risk Constraints


- C3: `has_schedule_conflict=False` -> The candidate must have no scheduling conflict.

### Violation Signature

- A: []
- B: ['C1', 'C2', 'C3', 'C4']
- C: ['C1', 'C4']
- D: ['C3', 'C5']

## attr_en_000046_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `B`

### High-Risk Constraints


- C1: `has_schedule_conflict=False` -> Candidates with a scheduling conflict are ineligible.
- C4: `has_conflict=False` -> The selected candidate must have no conflict of interest.

### Violation Signature

- A: ['C1', 'C4']
- B: []
- C: ['C2']
- D: ['C3']

## attr_en_000047_original

- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `B`

### High-Risk Constraints


- C1: `requires_extra_equipment=False` -> Candidates who need extra equipment support are ineligible.

### Violation Signature

- A: ['C1', 'C2']
- B: []
- C: ['C4']
- D: ['C3']

## attr_en_000051_original

- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- Gold: `A`

### High-Risk Constraints


- C2: `needs_supervision=False` -> The candidate must be able to work without additional supervision.
- C3: `requires_extra_equipment=False` -> The candidate must not require additional specialized equipment.

### Violation Signature

- A: []
- B: ['C1']
- C: ['C1', 'C3']
- D: ['C2']

## attr_en_000052_original

- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `C`

### High-Risk Constraints


- C4: `needs_supervision=False` -> The candidate must be able to work without additional supervision.

### Violation Signature

- A: ['C2', 'C4']
- B: ['C3']
- C: []
- D: ['C1']

## attr_en_000054_original

- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `C`

### High-Risk Constraints


- C2: `requires_extra_equipment=False` -> The candidate must not require additional specialized equipment.

### Violation Signature

- A: ['C1', 'C4']
- B: ['C3']
- C: []
- D: ['C2']

## attr_en_000055_original

- scenario: `project_assignment`
- option_closeness: `hard`
- structural_complexity: `low`
- Gold: `A`

### High-Risk Constraints


- C1: `has_conflict=False` -> Anyone with a conflict of interest is ineligible.

### Violation Signature

- A: []
- B: ['C3']
- C: ['C1']
- D: ['C2']

## attr_en_000056_original

- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `C`

### High-Risk Constraints


- C2: `requires_extra_equipment=False` -> The selected candidate must be able to participate without additional equipment.

### Violation Signature

- A: ['C1', 'C5']
- B: ['C1', 'C4']
- C: []
- D: ['C1', 'C2', 'C3', 'C4', 'C5']

## attr_en_000057_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `B`

### High-Risk Constraints


- C4: `has_conflict=False` -> Candidates must be free of conflicts related to the project.

### Violation Signature

- A: ['C2']
- B: []
- C: ['C1', 'C4']
- D: ['C3']

## attr_en_000058_original

- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `D`

### High-Risk Constraints


- C2: `requires_extra_equipment=False` -> Candidates who need extra equipment support are ineligible.
- C4: `has_schedule_conflict=False` -> Candidates with a scheduling conflict are ineligible.

### Violation Signature

- A: ['C1']
- B: ['C2', 'C3']
- C: ['C4']
- D: []

## attr_en_000059_original

- scenario: `project_assignment`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `A`

### High-Risk Constraints


- C5: `needs_supervision=False` -> Only candidates who can work independently without extra oversight are eligible.

### Violation Signature

- A: []
- B: ['C1', 'C3']
- C: ['C2', 'C4', 'C5']
- D: ['C2', 'C4']

## attr_en_000061_original

- scenario: `project_assignment`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `D`

### High-Risk Constraints


- C2: `has_schedule_conflict=False` -> Candidates with a scheduling conflict are ineligible.

### Violation Signature

- A: ['C1', 'C3', 'C4', 'C5']
- B: ['C2', 'C3']
- C: ['C2', 'C4']
- D: []

## attr_en_000062_original

- scenario: `project_assignment`
- option_closeness: `hard`
- structural_complexity: `low`
- Gold: `D`

### High-Risk Constraints


- C3: `needs_supervision=False` -> The candidate must be able to work without additional supervision.

### Violation Signature

- A: ['C3']
- B: ['C1']
- C: ['C2']
- D: []

## attr_en_000064_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `C`

### High-Risk Constraints


- C3: `needs_supervision=False` -> The candidate must be able to work without additional supervision.
- C4: `has_conflict=False` -> The selected candidate must have no conflict of interest.

### Violation Signature

- A: ['C4']
- B: ['C2', 'C3']
- C: []
- D: ['C1']

## attr_en_000067_original

- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `C`

### High-Risk Constraints


- C1: `needs_supervision=False` -> Additional supervision must not be required.

### Violation Signature

- A: ['C3']
- B: ['C1', 'C2']
- C: []
- D: ['C4']

## attr_en_000068_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `A`

### High-Risk Constraints


- C4: `has_conflict=False` -> Anyone with a conflict of interest is ineligible.

### Violation Signature

- A: []
- B: ['C3']
- C: ['C1', 'C2']
- D: ['C4']

## attr_en_000071_original

- scenario: `expert_recruitment`
- option_closeness: `hard`
- structural_complexity: `low`
- Gold: `C`

### High-Risk Constraints


- C1: `has_schedule_conflict=False` -> The candidate must have no scheduling conflict.
- C2: `has_conflict=False` -> Anyone with a conflict of interest is ineligible.

### Violation Signature

- A: ['C2']
- B: ['C1']
- C: []
- D: ['C3']

## attr_en_000075_original

- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `C`

### High-Risk Constraints


- C2: `requires_extra_equipment=False` -> The selected candidate must be able to participate without additional equipment.
- C4: `has_schedule_conflict=False` -> Candidates with a scheduling conflict are ineligible.

### Violation Signature

- A: ['C2', 'C3']
- B: ['C1']
- C: []
- D: ['C4']

## attr_en_000076_original

- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- Gold: `B`

### High-Risk Constraints


- C2: `needs_supervision=False` -> Additional supervision must not be required.

### Violation Signature

- A: ['C1', 'C3']
- B: []
- C: ['C1']
- D: ['C2']

## attr_en_000077_original

- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `C`

### High-Risk Constraints


- C3: `requires_extra_equipment=False` -> Candidates who need extra equipment support are ineligible.

### Violation Signature

- A: ['C1', 'C2', 'C3', 'C4', 'C5']
- B: ['C3', 'C5']
- C: []
- D: ['C1', 'C2']

## attr_en_000079_original

- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- Gold: `B`

### High-Risk Constraints


- C1: `needs_supervision=False` -> The candidate must be able to work without additional supervision.

### Violation Signature

- A: ['C1']
- B: []
- C: ['C1', 'C3']
- D: ['C2']

## attr_en_000081_original

- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `D`

### High-Risk Constraints


- C4: `has_schedule_conflict=False` -> The candidate must have no scheduling conflict.

### Violation Signature

- A: ['C2']
- B: ['C1', 'C4']
- C: ['C3']
- D: []

## attr_en_000087_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `D`

### High-Risk Constraints


- C1: `needs_supervision=False` -> Additional supervision must not be required.

### Violation Signature

- A: ['C4']
- B: ['C1', 'C2']
- C: ['C3']
- D: []

## attr_en_000090_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `D`

### High-Risk Constraints


- C1: `needs_supervision=False` -> The candidate must be able to work without additional supervision.
- C2: `has_conflict=False` -> Anyone with a conflict of interest is ineligible.

### Violation Signature

- A: ['C2']
- B: ['C1', 'C3']
- C: ['C4']
- D: []

## attr_en_000092_original

- scenario: `availability_selection`
- option_closeness: `hard`
- structural_complexity: `low`
- Gold: `B`

### High-Risk Constraints


- C2: `has_schedule_conflict=False` -> The candidate must have no scheduling conflict.

### Violation Signature

- A: ['C2']
- B: []
- C: ['C1']
- D: ['C3']

## attr_en_000094_original

- scenario: `project_assignment`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `D`

### High-Risk Constraints


- C1: `has_conflict=False` -> The selected candidate must have no conflict of interest.

### Violation Signature

- A: ['C2', 'C5']
- B: ['C1', 'C2', 'C3', 'C4', 'C5']
- C: ['C1', 'C5']
- D: []

## attr_en_000096_original

- scenario: `availability_selection`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `B`

### High-Risk Constraints


- C1: `has_schedule_conflict=False` -> Candidates with a scheduling conflict are ineligible.
- C4: `requires_extra_equipment=False` -> The candidate must not require additional specialized equipment.

### Violation Signature

- A: ['C1', 'C5']
- B: []
- C: ['C3', 'C4']
- D: ['C2', 'C4']

## attr_en_000097_original

- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- Gold: `A`

### High-Risk Constraints


- C2: `needs_supervision=False` -> Additional supervision must not be required.

### Violation Signature

- A: []
- B: ['C3']
- C: ['C2', 'C3']
- D: ['C1']

## attr_en_000099_original

- scenario: `availability_selection`
- option_closeness: `hard`
- structural_complexity: `low`
- Gold: `B`

### High-Risk Constraints


- C2: `requires_extra_equipment=False` -> The candidate must not require additional specialized equipment.
- C3: `has_schedule_conflict=False` -> Candidates with a scheduling conflict are ineligible.

### Violation Signature

- A: ['C2']
- B: []
- C: ['C3']
- D: ['C1']

## attr_en_000100_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `low`
- Gold: `A`

### High-Risk Constraints


- C1: `has_conflict=False` -> Candidates must be free of conflicts related to the project.

### Violation Signature

- A: []
- B: ['C1', 'C2']
- C: ['C2']
- D: ['C3']
