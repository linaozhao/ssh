# English Pilot v3 Examples

# easy

## attr_en_000023_original

- scenario: `expert_recruitment`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `C`

### Full Question

A research team needs to recruit one member who satisfies all of the listed requirements.
The selected person must satisfy all of the following requirements:

Requirements:
1. Only candidates who can participate on Tuesday are eligible.
2. Candidates must hold the required professional certification.
3. Availability next month is required.
4. Only candidates with prior research project experience are eligible.
5. Only candidates with experience in project execution are eligible.

Candidates:
A. Cameron has no valid certificate documentation. Cameron cannot start participating next month. Cameron is available for Tuesday work. Cameron has prior experience with research work. Cameron has participated in completed project work.
B. Ellis cannot participate on Tuesday, Ellis is available next month, Ellis has no valid certificate documentation, Ellis has participated in completed project work, and Ellis has participated in research projects.
C. Blair has participated in research projects, Blair can join the project next month, Blair has the required certification, Blair is available for Tuesday work, and Blair has experience contributing to project delivery.
D. Taylor is unavailable on Tuesday, and Taylor is not familiar with project execution. In addition, Taylor is unavailable next month, Taylor has not participated in research projects, and Taylor has no valid certificate documentation.

Which candidate satisfies all of the requirements?

### Formal Constraints

- C1: Only candidates who can participate on Tuesday are eligible. (available_tuesday=True)
- C2: Candidates must hold the required professional certification. (has_certificate=True)
- C3: Availability next month is required. (available_next_month=True)
- C4: Only candidates with prior research project experience are eligible. (has_research_experience=True)
- C5: Only candidates with experience in project execution are eligible. (has_project_experience=True)

### Violation Signature

- A: ['C2', 'C3']
- B: ['C1', 'C2']
- C: []
- D: ['C1', 'C2', 'C3', 'C4', 'C5']

## attr_en_000020_original

- scenario: `expert_recruitment`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `D`

### Full Question

A project leader must choose one qualified researcher from four applicants.
The selected person must satisfy all of the following requirements:

Requirements:
1. The selected candidate must be available on Monday.
2. Candidates must have experience with quality control work.
3. Prior management experience is required.
4. Only candidates with the required prior training are eligible.
5. Programming experience is required.

Candidates:
A. Wren cannot join project work on Monday, Wren lacks experience coordinating project work, Wren has no practical programming background, Wren has completed the prerequisite training, and Wren has no background in quality review work.
B. Quinn cannot participate on Monday, and Quinn has handled software implementation work. In addition, Quinn has previously handled management responsibilities, Quinn has no background in quality review work, and Quinn meets the prior training requirement.
C. Blair is available for Monday work, Blair has not managed a team or project before, Blair has handled quality review work before, Blair has practical programming experience, and Blair has not completed the prerequisite training.
D. Jules has experience with quality control processes, Jules has coordinated project work before, Jules has practical programming experience, Jules is available for Monday work, and Jules has the required training background.

Which applicant should be selected?

### Formal Constraints

- C1: The selected candidate must be available on Monday. (available_monday=True)
- C2: Candidates must have experience with quality control work. (has_quality_assurance_experience=True)
- C3: Prior management experience is required. (has_management_experience=True)
- C4: Only candidates with the required prior training are eligible. (has_prior_training=True)
- C5: Programming experience is required. (has_programming_experience=True)

### Violation Signature

- A: ['C1', 'C2', 'C3', 'C5']
- B: ['C1', 'C2']
- C: ['C3', 'C4']
- D: []

## attr_en_000043_original

- scenario: `expert_recruitment`
- option_closeness: `easy`
- structural_complexity: `high`
- Gold: `D`

### Full Question

A research lab is selecting one researcher for a new project.
The selected person must satisfy all of the following requirements:

Requirements:
1. Applicants must have experience working with machine learning systems.
2. Only candidates with sufficient domain knowledge are eligible.
3. The selected candidate must be available in the morning.
4. Candidates must have valid local work authorization.
5. Programming experience is required.

Candidates:
A. Blair has not handled coding tasks before, Blair is unavailable in the morning, Blair does not meet the local work permit requirement, Blair has no prior exposure to machine learning projects, and Blair is not familiar with the domain needed for the work.
B. Lane has not worked with machine learning before, Lane is not familiar with the domain needed for the work, Lane meets the local work permit requirement, Lane can participate during the morning, and Lane has written code for previous projects.
C. Riley has practical programming experience. Riley lacks background knowledge in the domain. Riley cannot participate during the morning. Riley has local work authorization. Riley has hands-on experience with machine learning systems.
D. Parker meets the local work permit requirement, and Parker can work in the morning time slot. In addition, Parker has handled software implementation work, Parker has worked on machine learning projects, and Parker understands the relevant project domain.

Which candidate satisfies all of the requirements?

### Formal Constraints

- C1: Applicants must have experience working with machine learning systems. (has_ml_experience=True)
- C2: Only candidates with sufficient domain knowledge are eligible. (has_domain_knowledge=True)
- C3: The selected candidate must be available in the morning. (available_morning=True)
- C4: Candidates must have valid local work authorization. (has_local_work_permit=True)
- C5: Programming experience is required. (has_programming_experience=True)

### Violation Signature

- A: ['C1', 'C2', 'C3', 'C4', 'C5']
- B: ['C1', 'C2']
- C: ['C2', 'C3']
- D: []

# medium

## attr_en_000024_original

- scenario: `project_assignment`
- option_closeness: `medium`
- structural_complexity: `low`
- Gold: `D`

### Full Question

Four team members are being considered for a project role.
The selected person must satisfy all of the following requirements:

Requirements:
1. Independent work ability is required.
2. Only candidates with valid security clearance are eligible.
3. Only candidates who can participate remotely are eligible.

Candidates:
A. Hayden meets the security clearance requirement. Hayden lacks the setup needed for remote collaboration. Hayden can complete tasks independently.
B. Jordan is able to participate through remote work, Jordan cannot complete tasks independently, and Jordan has valid security clearance.
C. Riley has the setup needed for remote collaboration, Riley does not have valid security clearance, and Riley is not able to make progress independently.
D. Sawyer has valid security clearance, Sawyer can work remotely, and Sawyer can complete tasks independently.

Which candidate should receive the project role?

### Formal Constraints

- C1: Independent work ability is required. (can_work_independently=True)
- C2: Only candidates with valid security clearance are eligible. (has_security_clearance=True)
- C3: Only candidates who can participate remotely are eligible. (can_work_remote=True)

### Violation Signature

- A: ['C3']
- B: ['C1']
- C: ['C1', 'C2']
- D: []

## attr_en_000019_original

- scenario: `expert_recruitment`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `C`

### Full Question

A project leader must choose one qualified researcher from four applicants.
The selected person must satisfy all of the following requirements:

Requirements:
1. Research experience is required.
2. A relevant certificate is required.
3. The candidate must be able to work independently.
4. Teamwork experience is required.

Candidates:
A. Milan has no valid certificate documentation, and Milan has participated in research projects. In addition, Milan can complete tasks independently, and Milan has handled collaborative team tasks.
B. Rowan can work without close guidance, and Rowan has no background in collaborative team tasks. In addition, Rowan has the required certification, and Rowan has not participated in research projects.
C. Kris can work without close guidance, Kris holds a relevant professional certificate, Kris has participated in research projects, and Kris has experience working with project teams.
D. Gray holds a relevant professional certificate, Gray has handled collaborative team tasks, Gray has participated in research projects, and Gray is not able to make progress independently.

Which candidate satisfies all of the requirements?

### Formal Constraints

- C1: Research experience is required. (has_research_experience=True)
- C2: A relevant certificate is required. (has_certificate=True)
- C3: The candidate must be able to work independently. (can_work_independently=True)
- C4: Teamwork experience is required. (has_teamwork_experience=True)

### Violation Signature

- A: ['C2']
- B: ['C1', 'C4']
- C: []
- D: ['C3']

## attr_en_000013_original

- scenario: `availability_selection`
- option_closeness: `medium`
- structural_complexity: `medium`
- Gold: `C`

### Full Question

Four candidates are being considered based on their availability and participation constraints.
The selected person must satisfy all of the following requirements:

Requirements:
1. The selected candidate must be available in the afternoon.
2. Only candidates who can participate on Monday are eligible.
3. The candidate must be available for on-site work.
4. Only candidates who can join next month are eligible.

Candidates:
A. Emerson can join the project on Monday, and Emerson can work at the project location. In addition, Emerson can join the project next month, and Emerson is unavailable in the afternoon.
B. Kris can participate on site, and Kris is unavailable next month. In addition, Kris can work in the afternoon time slot, and Kris can join the project on Monday.
C. Devon can participate during the afternoon, Devon can participate on site, Devon can join the project on Monday, and Devon can start participating next month.
D. Taylor is available next month, and Taylor cannot work at the project location. In addition, Taylor can work in the afternoon time slot, and Taylor cannot join project work on Monday.

Which candidate matches every scheduling requirement?

### Formal Constraints

- C1: The selected candidate must be available in the afternoon. (available_afternoon=True)
- C2: Only candidates who can participate on Monday are eligible. (available_monday=True)
- C3: The candidate must be available for on-site work. (can_work_onsite=True)
- C4: Only candidates who can join next month are eligible. (available_next_month=True)

### Violation Signature

- A: ['C1']
- B: ['C4']
- C: []
- D: ['C2', 'C3']

# hard

## attr_en_000012_original

- scenario: `availability_selection`
- option_closeness: `hard`
- structural_complexity: `low`
- Gold: `B`

### Full Question

The coordinator must identify the only candidate who meets all scheduling requirements.
The selected person must satisfy all of the following requirements:

Requirements:
1. On-site work capability is required.
2. Only candidates who can participate on Monday are eligible.
3. Only candidates who can adapt to flexible scheduling are eligible.

Candidates:
A. Robin can participate on Monday. Robin cannot participate on site. Robin is able to handle variable work hours.
B. Emerson can participate on Monday, Emerson can adapt to flexible scheduling, and Emerson can work at the project location.
C. Sage can work flexible hours. In addition, Sage can work at the project location, and Sage cannot participate on Monday.
D. Elliot can join the project on Monday. Elliot cannot work flexible hours. Elliot is available for on-site work.

Which candidate matches every scheduling requirement?

### Formal Constraints

- C1: On-site work capability is required. (can_work_onsite=True)
- C2: Only candidates who can participate on Monday are eligible. (available_monday=True)
- C3: Only candidates who can adapt to flexible scheduling are eligible. (accepts_flexible_hours=True)

### Violation Signature

- A: ['C1']
- B: []
- C: ['C2']
- D: ['C3']

## attr_en_000093_original

- scenario: `project_assignment`
- option_closeness: `hard`
- structural_complexity: `low`
- Gold: `C`

### Full Question

The project manager must select one person who satisfies every requirement for the assignment.
The selected person must satisfy all of the following requirements:

Requirements:
1. Only candidates who can work during the weekend are eligible.
2. Familiarity with statistics is required.
3. Relevant domain knowledge is required.

Candidates:
A. Elliot is familiar with the domain needed for the work. Elliot cannot handle statistical analysis tasks. Elliot can participate on the weekend.
B. Indigo understands common statistical methods. In addition, Indigo cannot participate in weekend work, and Indigo is familiar with the domain needed for the work.
C. Jamie is familiar with the domain needed for the work. In addition, Jamie can work with statistical analysis tasks, and Jamie can join weekend project activities.
D. Kendall has a solid statistics background, Kendall does not understand the relevant project domain, and Kendall can join weekend project activities.

Which candidate should receive the project role?

### Formal Constraints

- C1: Only candidates who can work during the weekend are eligible. (available_weekend=True)
- C2: Familiarity with statistics is required. (familiar_with_statistics=True)
- C3: Relevant domain knowledge is required. (has_domain_knowledge=True)

### Violation Signature

- A: ['C2']
- B: ['C1']
- C: []
- D: ['C3']

## attr_en_000009_original

- scenario: `expert_recruitment`
- option_closeness: `hard`
- structural_complexity: `low`
- Gold: `A`

### Full Question

A project leader must choose one qualified researcher from four applicants.
The selected person must satisfy all of the following requirements:

Requirements:
1. Independent work ability is required.
2. Only candidates with experience in project execution are eligible.
3. Anyone with a conflict of interest is ineligible.

Candidates:
A. Emerson has experience contributing to project delivery, Emerson can work without close guidance, and Emerson is free of conflicts for this project.
B. Logan has participated in completed project work. Logan can complete tasks independently. Logan would need to be recused because of a conflict.
C. Jules has no conflict of interest related to the project. Jules has not participated in project work before. Jules can work without close guidance.
D. Elliot is familiar with project execution. Elliot cannot complete tasks independently. Elliot has no project-related conflict requiring recusal.

Which applicant should be selected?

### Formal Constraints

- C1: Independent work ability is required. (can_work_independently=True)
- C2: Only candidates with experience in project execution are eligible. (has_project_experience=True)
- C3: Anyone with a conflict of interest is ineligible. (has_conflict=False)

### Violation Signature

- A: []
- B: ['C3']
- C: ['C2']
- D: ['C1']
