# CBM-Attr v1 Dataset Examples

Programmatically selected examples; no human annotation is claimed.

## attr_v4_1_000185_original

- Cell: `CL1__DS1_far__IL1_low`
- Scenario: `project_assignment`
- Gold: `A`
- Clean oracle sizes: `1 -> 1 -> 1 -> 1 -> 1`
- Update target: `D`; correction size: `3`

### Requirements

- Candidates must have the required security clearance.
- Monday availability is required.
- Only candidates who can participate remotely are eligible.

### Clean rounds

- R1 oracle `['A']`: Marley does not have valid security clearance | Avery lacks the setup needed for remote collaboration | Tatum lacks the required security authorization | Quinn meets the security clearance requirement
- R2 oracle `['A']`: Avery cannot participate on Monday | Tatum is not able to participate through remote work | Quinn can join the project on Monday | Marley has the setup needed for remote collaboration
- R3 oracle `['A']`: Tatum cannot participate on Monday | Avery meets the security clearance requirement | Quinn can work remotely | Marley cannot participate on Monday
- R4 oracle `['A']`: Quinn meets the security clearance requirement
- R5 oracle `['A']`: Quinn can work remotely

### Correction

- Replace `attr_v4_1_000185:D:has_security_clearance:v1` with: Tatum has valid security clearance
- Replace `attr_v4_1_000185:D:available_monday:v1` with: Tatum is available for Monday work
- Replace `attr_v4_1_000185:D:can_work_remote:v1` with: Tatum can work remotely

## attr_v4_1_000187_original

- Cell: `CL1__DS1_far__IL1_low`
- Scenario: `expert_recruitment`
- Gold: `C`
- Clean oracle sizes: `2 -> 1 -> 1 -> 1 -> 1`
- Update target: `A`; correction size: `2`

### Requirements

- Only candidates who can join next month are eligible.
- Candidates must have experience presenting to an audience.
- Client communication experience is required.

### Clean rounds

- R1 oracle `['C', 'D']`: Quinn has not given public presentations before | Jordan can start participating next month | Devon has no practical background in client communication | Jamie has handled client-facing discussions
- R2 oracle `['C']`: Jordan has communicated directly with clients | Quinn has not communicated directly with clients | Devon has handled formal presentation duties | Jamie cannot start participating next month
- R3 oracle `['C']`: Jordan has given public presentations before | Quinn can join the project next month | Jamie has not given public presentations before | Devon cannot start participating next month
- R4 oracle `['C']`: Jamie has handled client-facing discussions
- R5 oracle `['C']`: Devon has handled formal presentation duties

### Correction

- Replace `attr_v4_1_000187:A:available_next_month:v1` with: Devon is available next month
- Replace `attr_v4_1_000187:A:has_client_communication_experience:v1` with: Devon has practical client communication experience

## attr_v4_1_000229_original

- Cell: `CL1__DS2_medium__IL1_low`
- Scenario: `project_assignment`
- Gold: `A`
- Clean oracle sizes: `2 -> 1 -> 1 -> 1 -> 1`
- Update target: `C`; correction size: `1`

### Requirements

- Only candidates with sufficient domain knowledge are eligible.
- Independent work ability is required.
- Only candidates with prior public presentation experience are eligible.

### Clean rounds

- R1 oracle `['A', 'C']`: Quinn can work without close guidance | Blair lacks experience speaking to an audience | Rowan can complete tasks independently | Jordan is not able to make progress independently
- R2 oracle `['A']`: Rowan understands the relevant project domain | Jordan has experience speaking to an audience | Quinn has not given public presentations before | Blair is not familiar with the domain needed for the work
- R3 oracle `['A']`: Jordan does not understand the relevant project domain | Rowan has experience speaking to an audience | Quinn has background knowledge in the domain | Blair is able to make progress independently
- R4 oracle `['A']`: Quinn has background knowledge in the domain
- R5 oracle `['A']`: Blair is able to make progress independently

### Correction

- Replace `attr_v4_1_000229:C:has_public_speaking_experience:v1` with: Quinn has given public presentations before

## attr_v4_1_000226_original

- Cell: `CL1__DS2_medium__IL1_low`
- Scenario: `project_assignment`
- Gold: `B`
- Clean oracle sizes: `3 -> 2 -> 1 -> 1 -> 1`
- Update target: `C`; correction size: `2`

### Requirements

- The candidate must not require additional specialized equipment.
- Only candidates with prior team collaboration experience are eligible.
- The candidate must be willing to travel.

### Clean rounds

- R1 oracle `['A', 'B', 'D']`: Casey has not collaborated on team projects | Ellis has handled collaborative team tasks | Payton can support project-related travel | Tatum is willing to travel if the assignment requires it
- R2 oracle `['B', 'D']`: Casey can work with the equipment already available | Tatum can work with the equipment already available | Ellis can work with the equipment already available | Payton has no background in collaborative team tasks
- R3 oracle `['B']`: Casey cannot travel for the project | Ellis is not willing to travel for this assignment | Tatum has handled collaborative team tasks | Payton cannot participate without additional equipment
- R4 oracle `['B']`: Tatum has handled collaborative team tasks
- R5 oracle `['B']`: Ellis can work with the equipment already available

### Correction

- Replace `attr_v4_1_000226:C:has_teamwork_experience:v1` with: Casey has handled collaborative team tasks
- Replace `attr_v4_1_000226:C:willing_to_travel:v1` with: Casey can travel for the project

## attr_v4_1_000227_original

- Cell: `CL1__DS2_medium__IL1_low`
- Scenario: `availability_selection`
- Gold: `C`
- Clean oracle sizes: `2 -> 2 -> 1 -> 1 -> 1`
- Update target: `D`; correction size: `2`

### Requirements

- Only candidates who can participate during the afternoon are eligible.
- The candidate must be able to work remotely.
- The candidate must have no scheduling conflict.

### Clean rounds

- R1 oracle `['A', 'C']`: Reese can avoid schedule conflicts for this role | Parker is not able to participate through remote work | Hayden cannot work remotely | Elliot can avoid schedule conflicts for this role
- R2 oracle `['A', 'C']`: Hayden can work in the afternoon time slot | Parker has no scheduling conflict with the project | Elliot is available in the afternoon | Reese has the setup needed for remote collaboration
- R3 oracle `['C']`: Reese cannot work in the afternoon time slot | Hayden cannot avoid a schedule conflict for this role | Elliot is able to participate through remote work | Parker cannot participate during the afternoon
- R4 oracle `['C']`: Elliot is available in the afternoon
- R5 oracle `['C']`: Reese has the setup needed for remote collaboration

### Correction

- Replace `attr_v4_1_000227:D:available_afternoon:v1` with: Parker can work in the afternoon time slot
- Replace `attr_v4_1_000227:D:can_work_remote:v1` with: Parker can work remotely

## attr_v4_1_000255_original

- Cell: `CL1__DS2_medium__IL2_high`
- Scenario: `availability_selection`
- Gold: `C`
- Clean oracle sizes: `3 -> 1 -> 1 -> 1 -> 1`
- Update target: `D`; correction size: `1`

### Requirements

- The selected candidate must be able to participate on the weekend.
- Monday availability is required.
- Morning availability is required.

### Clean rounds

- R1 oracle `['B', 'C', 'D']`: Emerson cannot work in the morning time slot | Skyler is available in the morning | Payton can participate on Monday | Taylor can work in the morning time slot
- R2 oracle `['C']`: Taylor cannot participate in weekend work | Skyler can participate on the weekend | Payton cannot join weekend project activities | Emerson is available for Monday work
- R3 oracle `['C']`: Emerson cannot join weekend project activities | Payton can participate during the morning | Skyler is available for Monday work | Taylor cannot join project work on Monday
- R4 oracle `['C']`: Payton can participate on Monday
- R5 oracle `['C']`: Skyler is available for Monday work

### Correction

- Replace `attr_v4_1_000255:D:available_weekend:v1` with: Payton can participate on the weekend

## attr_v4_1_000277_original

- Cell: `CL1__DS3_near__IL1_low`
- Scenario: `availability_selection`
- Gold: `A`
- Clean oracle sizes: `3 -> 2 -> 1 -> 1 -> 1`
- Update target: `C`; correction size: `1`

### Requirements

- The selected candidate must be able to participate on the weekend.
- The candidate must have no scheduling conflict.
- The candidate must not require additional specialized equipment.

### Clean rounds

- R1 oracle `['A', 'B', 'C']`: Reese would require additional specialized equipment | Wren does not need extra equipment support | Elliot can work with the equipment already available | Harper can join weekend project activities
- R2 oracle `['A', 'B']`: Harper can work with the equipment already available | Wren can participate on the weekend | Reese has no scheduling conflict with the project | Elliot cannot participate in weekend work
- R3 oracle `['A']`: Harper has a scheduling conflict with the project | Wren has no scheduling conflict with the project | Reese is available for weekend work | Elliot can avoid schedule conflicts for this role
- R4 oracle `['A']`: Elliot can work with the equipment already available
- R5 oracle `['A']`: Wren does not need extra equipment support

### Correction

- Replace `attr_v4_1_000277:C:available_weekend:v1` with: Elliot can join weekend project activities

## attr_v4_1_000271_original

- Cell: `CL1__DS3_near__IL1_low`
- Scenario: `availability_selection`
- Gold: `C`
- Clean oracle sizes: `4 -> 2 -> 1 -> 1 -> 1`
- Update target: `B`; correction size: `1`

### Requirements

- The candidate must be available for on-site work.
- Only candidates who can adapt to flexible scheduling are eligible.
- Only candidates who can participate on Monday are eligible.

### Clean rounds

- R1 oracle `['A', 'B', 'C', 'D']`: Cameron is available for Monday work | Casey can join the project on Monday | Payton can adapt to flexible scheduling | Hayden can participate on Monday
- R2 oracle `['B', 'C']`: Payton cannot participate on Monday | Cameron can adapt to flexible scheduling | Casey is not able to handle variable work hours | Hayden can work flexible hours
- R3 oracle `['C']`: Payton is available for on-site work | Cameron can participate on site | Casey can work at the project location | Hayden cannot work at the project location
- R4 oracle `['C']`: Cameron can adapt to flexible scheduling
- R5 oracle `['C']`: Cameron can participate on site

### Correction

- Replace `attr_v4_1_000271:B:can_work_onsite:v1` with: Hayden can work at the project location

## attr_v4_1_000283_original

- Cell: `CL1__DS3_near__IL2_high`
- Scenario: `project_assignment`
- Gold: `C`
- Clean oracle sizes: `4 -> 1 -> 1 -> 1 -> 1`
- Update target: `A`; correction size: `1`

### Requirements

- The candidate must be able to work without additional supervision.
- Only candidates who can adapt to flexible scheduling are eligible.
- Candidates must have experience presenting to an audience.

### Clean rounds

- R1 oracle `['A', 'B', 'C', 'D']`: Jordan can adapt to flexible scheduling | Devon can work flexible hours | Casey has given public presentations before | Payton can adapt to flexible scheduling
- R2 oracle `['C']`: Devon has no background in formal presentation duties | Casey cannot adapt to flexible scheduling | Payton can carry out the work independently | Jordan cannot carry out the work without additional supervision
- R3 oracle `['C']`: Casey can carry out the work independently | Jordan has given public presentations before | Payton has handled formal presentation duties | Devon does not require extra oversight for this role
- R4 oracle `['C']`: Devon does not require extra oversight for this role
- R5 oracle `['C']`: Devon can work flexible hours

### Correction

- Replace `attr_v4_1_000283:A:needs_supervision:v1` with: Jordan can carry out the work independently

## attr_v4_1_000317_original

- Cell: `CL2__DS1_far__IL1_low`
- Scenario: `project_assignment`
- Gold: `A`
- Clean oracle sizes: `1 -> 1 -> 1 -> 1 -> 1`
- Update target: `D`; correction size: `4`

### Requirements

- Candidates must have experience presenting to an audience.
- Teamwork experience is required.
- Flexible-hour availability is required.
- Only candidates with experience in project execution are eligible.
- The selected candidate must have no conflict of interest.

### Clean rounds

- R1 oracle `['A']`: Marley has no background in formal presentation duties | Marley has handled collaborative team tasks | Arden has collaborated on team projects | Arden lacks experience speaking to an audience | Casey is able to handle variable work hours | Briar has no background in formal presentation duties | Casey has experience speaking to an audience
- R2 oracle `['A']`: Casey is familiar with project execution | Marley cannot work flexible hours | Briar is not familiar with project execution | Casey is free of conflicts for this project | Arden lacks project delivery experience | Briar would need to be recused because of a conflict | Arden would need to be recused because of a conflict
- R3 oracle `['A']`: Briar is able to handle variable work hours | Arden is not able to handle variable work hours | Marley is familiar with project execution | Marley has a conflict of interest related to the project | Briar has experience working with project teams | Casey has collaborated on team projects
- R4 oracle `['A']`: Casey is familiar with project execution
- R5 oracle `['A']`: Casey is free of conflicts for this project

### Correction

- Replace `attr_v4_1_000317:D:has_public_speaking_experience:v1` with: Arden has handled formal presentation duties
- Replace `attr_v4_1_000317:D:accepts_flexible_hours:v1` with: Arden can adapt to flexible scheduling
- Replace `attr_v4_1_000317:D:has_project_experience:v1` with: Arden is familiar with project execution
- Replace `attr_v4_1_000317:D:has_conflict:v1` with: Arden has no conflict of interest related to the project

## attr_v4_1_000388_original

- Cell: `CL2__DS3_near__IL1_low`
- Scenario: `availability_selection`
- Gold: `D`
- Clean oracle sizes: `3 -> 3 -> 1 -> 1 -> 1`
- Update target: `B`; correction size: `1`

### Requirements

- Only candidates who can participate on Tuesday are eligible.
- Only candidates who can participate during the afternoon are eligible.
- Only candidates who can work during the weekend are eligible.
- Only candidates who can join next month are eligible.
- The candidate must be available for on-site work.

### Clean rounds

- R1 oracle `['A', 'B', 'D']`: Noel is available for on-site work | Jordan is available next month | Jordan can participate on Tuesday | Robin can work in the afternoon time slot | Noel cannot participate in weekend work | Skyler can participate on the weekend | Robin can join weekend project activities
- R2 oracle `['A', 'B', 'D']`: Skyler is available in the afternoon | Noel is available next month | Robin can participate on site | Skyler can participate on site | Jordan can participate on the weekend | Robin is available for Tuesday work | Jordan can work at the project location
- R3 oracle `['D']`: Jordan can work in the afternoon time slot | Noel is available in the afternoon | Skyler can join the project next month | Robin cannot join the project next month | Noel can join the project on Tuesday | Skyler is unavailable on Tuesday
- R4 oracle `['D']`: Jordan can participate on Tuesday
- R5 oracle `['D']`: Noel can join the project on Tuesday

### Correction

- Replace `attr_v4_1_000388:B:available_tuesday:v1` with: Skyler is available for Tuesday work

## attr_v4_1_000437_original

- Cell: `CL3__DS1_far__IL1_low`
- Scenario: `project_assignment`
- Gold: `A`
- Clean oracle sizes: `1 -> 1 -> 1 -> 1 -> 1`
- Update target: `B`; correction size: `4`

### Requirements

- The selected candidate must have analyzed data in prior work.
- The selected candidate must have prior coding experience.
- Only applicants with a valid relevant certificate are eligible.
- Only candidates who can travel for the project are eligible.
- Only candidates who can participate remotely are eligible.
- Availability next month is required.
- Quality assurance experience is required.

### Clean rounds

- R1 oracle `['A']`: Quinn has written code for previous projects | Quinn can start participating next month | Morgan is unavailable next month | Skyler is unavailable next month | Skyler holds a relevant professional certificate | Morgan cannot travel for the project | Morgan has experience with quality control processes | Sawyer has no practical programming background | Sawyer does not hold a relevant certificate | Quinn is willing to travel if the assignment requires it
- R2 oracle `['A']`: Morgan has practical programming experience | Sawyer lacks the setup needed for remote collaboration | Quinn is able to participate through remote work | Skyler has handled software implementation work | Skyler lacks experience with quality control processes | Sawyer has no background in quality review work | Skyler has no prior data analysis background | Morgan has not performed data analysis before | Quinn has performed data analysis in previous work
- R3 oracle `['A']`: Quinn has valid certificate documentation | Morgan is not able to participate through remote work | Morgan holds a relevant professional certificate | Sawyer can start participating next month | Sawyer is not willing to travel for this assignment | Skyler cannot work remotely | Sawyer has not performed data analysis before | Quinn has experience with quality control processes | Skyler can travel for the project
- R4 oracle `['A']`: Quinn has experience with quality control processes
- R5 oracle `['A']`: Quinn has written code for previous projects

### Correction

- Replace `attr_v4_1_000437:B:has_data_analysis_experience:v1` with: Skyler has practical experience analyzing datasets
- Replace `attr_v4_1_000437:B:can_work_remote:v1` with: Skyler can work remotely
- Replace `attr_v4_1_000437:B:available_next_month:v1` with: Skyler is available next month
- Replace `attr_v4_1_000437:B:has_quality_assurance_experience:v1` with: Skyler has worked on quality assurance tasks
