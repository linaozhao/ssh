# Single-Agent Screening Examples

Representative items for manual inspection. Reasoning text is copied from model outputs without automatic judging.

## attr_en_000001_original

- screening_category: `stable_correct`
- MAD priority: `low`
- Gold: `B`
- empirical_accuracy: `1.0000`

### Question

Four team members are being considered for a project role.
The selected person must satisfy all of the following requirements:

Requirements:
1. The selected candidate must be available on Tuesday.
2. Candidates must have experience collaborating with a team.
3. Only candidates who can participate on Monday are eligible.
4. Only candidates with prior research project experience are eligible.

Candidates:
A. Briar can participate on Monday, and Briar has no background in collaborative team tasks. In addition, Briar is familiar with research project workflows, and Briar can participate on Tuesday.
B. Jamie can join the project on Monday, and Jamie has collaborated on team projects. In addition, Jamie can join the project on Tuesday, and Jamie has participated in research projects.
C. Devon cannot participate on Tuesday. Devon can join the project on Monday. Devon has collaborated on team projects. Devon has not participated in research projects.
D. Lane has participated in research projects, Lane has collaborated on team projects, Lane cannot join project work on Monday, and Lane can join the project on Tuesday.

Which candidate should receive the project role?

### Six Runs

- `llama` run `1` seed `11`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Jamie is the only candidate who meets all the requirements. Jamie can participate on Monday, Jamie has experience collaborating with a team, Jamie can participate on Tuesday, and Jamie has participated in research projects.
- `llama` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Jamie satisfies all of the requirements. Jamie can participate on Monday, Jamie has experience collaborating with a team, Jamie can participate on Tuesday, and Jamie has prior research project experience.
- `llama` run `3` seed `33`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Jamie is the only candidate who meets all of the requirements. Jamie can participate on Monday, Jamie has experience collaborating with a team, Jamie can participate on Tuesday, and Jamie has prior research project experience.
- `qwen` run `1` seed `11`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate B satisfies all the requirements: available on Tuesday, has experience collaborating with a team, can participate on Monday, and has prior research project experience. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate B satisfies all the requirements: available on Tuesday, has experience collaborating with a team, can participate on Monday, and has prior research project experience. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate B satisfies all requirements: available on Tuesday, has team collaboration experience, can participate on Monday, and has prior research project experience. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 3, 'C': 0, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 3, 'C': 0, 'D': 0, 'invalid': 0}`
Observed wrong options: `[]`
Observed wrong violation signatures: `{}`

## attr_en_000002_original

- screening_category: `stable_correct`
- MAD priority: `low`
- Gold: `A`
- empirical_accuracy: `1.0000`

### Question

A research lab is selecting one researcher for a new project.
The selected person must satisfy all of the following requirements:

Requirements:
1. Only candidates with practical data analysis experience are eligible.
2. The candidate must be able to communicate in English.
3. Only candidates who can participate on Tuesday are eligible.
4. Candidates must have experience with quality control work.

Candidates:
A. Reese is available for Tuesday work. Reese can participate in English discussions. Reese has practical experience analyzing datasets. Reese has handled quality review work before.
B. Jordan lacks practical experience analyzing datasets, Jordan has worked on quality assurance tasks, Jordan can communicate in English for work, and Jordan can participate on Tuesday.
C. Robin has not worked on quality assurance tasks. Robin is able to handle English-language communication. Robin can participate on Tuesday. Robin has performed data analysis in previous work.
D. Kris is not able to handle English-language communication. Kris is unavailable on Tuesday. Kris has handled quality review work before. Kris has handled data analysis tasks before.

Which researcher meets every listed requirement?

### Six Runs

- `llama` run `1` seed `11`: answer=`A`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Reese meets all the requirements: Reese has practical experience analyzing datasets, Reese can communicate in English, Reese is available on Tuesday, and Reese has experience with quality control work.
- `llama` run `2` seed `22`: answer=`A`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Reese meets all the listed requirements. Reese has practical experience analyzing datasets, can communicate in English, is available on Tuesday, and has handled quality review work before.
- `llama` run `3` seed `33`: answer=`A`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Reese meets every listed requirement: Reese has practical experience analyzing datasets, Reese can communicate in English, Reese is available for Tuesday work, and Reese has handled quality review work before.
- `qwen` run `1` seed `11`: answer=`A`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate A satisfies all requirements: has practical data analysis experience, can communicate in English, can participate on Tuesday, and has experience with quality control work. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`A`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate A satisfies all the requirements: practical data analysis experience, English communication ability, availability on Tuesday, and experience with quality control work. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`A`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate A satisfies all requirements: has practical data analysis experience, can communicate in English, is available on Tuesday, and has experience with quality control work. Other candidates fail at least one requirement.

Qwen answers: `{'A': 3, 'B': 0, 'C': 0, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 3, 'B': 0, 'C': 0, 'D': 0, 'invalid': 0}`
Observed wrong options: `[]`
Observed wrong violation signatures: `{}`

## attr_en_000003_original

- screening_category: `stable_correct`
- MAD priority: `low`
- Gold: `B`
- empirical_accuracy: `1.0000`

### Question

A research lab is selecting one researcher for a new project.
The selected person must satisfy all of the following requirements:

Requirements:
1. The selected candidate must be available next month.
2. The selected candidate must have no conflict of interest.
3. Programming experience is required.

Candidates:
A. Kris has no practical programming background, Kris is free of conflicts for this project, and Kris is available next month.
B. Tatum has no conflict of interest related to the project. Tatum has practical programming experience. Tatum is available next month.
C. Quinn is available next month, Quinn has practical programming experience, and Quinn would need to be recused because of a conflict.
D. Morgan cannot join the project next month. In addition, Morgan has practical programming experience, and Morgan has an interest conflict affecting this project.

Which candidate satisfies all of the requirements?

### Six Runs

- `llama` run `1` seed `11`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all of the requirements: 1. Tatum is available next month. 2. Tatum has no conflict of interest related to the project. 3. Tatum has practical programming experience.
- `llama` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all of the requirements. Candidate B is available next month, has no conflict of interest, and has practical programming experience.
- `llama` run `3` seed `33`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all of the requirements: 1. Tatum is available next month. 2. Tatum has no conflict of interest. 3. Tatum has practical programming experience.
- `qwen` run `1` seed `11`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate B satisfies all the requirements: availability next month, no conflict of interest, and has programming experience. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate B satisfies all the requirements: available next month, no conflict of interest, and has programming experience. Candidates A, C, and D fail to meet at least one requirement.
- `qwen` run `3` seed `33`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all requirements: has no conflict of interest, has programming experience, and is available next month. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 3, 'C': 0, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 3, 'C': 0, 'D': 0, 'invalid': 0}`
Observed wrong options: `[]`
Observed wrong violation signatures: `{}`

## attr_en_000004_original

- screening_category: `stable_correct`
- MAD priority: `low`
- Gold: `A`
- empirical_accuracy: `1.0000`

### Question

A project leader must choose one qualified researcher from four applicants.
The selected person must satisfy all of the following requirements:

Requirements:
1. Only candidates with practical data analysis experience are eligible.
2. Candidates must have the required security clearance.
3. Tuesday availability is required.

Candidates:
A. Hayden meets the security clearance requirement. In addition, Hayden can participate on Tuesday, and Hayden has performed data analysis in previous work.
B. Payton has the required security authorization. Payton can participate on Tuesday. Payton has not performed data analysis before.
C. Tatum does not meet the security clearance requirement, Tatum can join the project on Tuesday, and Tatum has handled data analysis tasks before.
D. Devon cannot join project work on Tuesday. In addition, Devon has practical experience analyzing datasets, and Devon has valid security clearance.

Which candidate satisfies all of the requirements?

### Six Runs

- `llama` run `1` seed `11`: answer=`A`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate A meets all the requirements. Candidate A has practical experience in data analysis, meets the security clearance requirement, and can participate on Tuesday.
- `llama` run `2` seed `22`: answer=`A`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Hayden meets all of the requirements. Hayden has practical data analysis experience, Hayden has the required security clearance, and Hayden can participate on Tuesday.
- `llama` run `3` seed `33`: answer=`A`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Hayden meets all of the requirements: Hayden has practical data analysis experience, Hayden has the required security clearance, and Hayden is available on Tuesday.
- `qwen` run `1` seed `11`: answer=`A`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate A meets all the requirements: practical data analysis experience, required security clearance, and Tuesday availability. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`A`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate A meets all the requirements: practical data analysis experience, required security clearance, and availability on Tuesday. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`A`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate A meets all the requirements: practical data analysis experience, required security clearance, and availability on Tuesday. Other candidates fail at least one requirement.

Qwen answers: `{'A': 3, 'B': 0, 'C': 0, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 3, 'B': 0, 'C': 0, 'D': 0, 'invalid': 0}`
Observed wrong options: `[]`
Observed wrong violation signatures: `{}`

## attr_en_000005_original

- screening_category: `stable_correct`
- MAD priority: `low`
- Gold: `D`
- empirical_accuracy: `1.0000`

### Question

The project manager must select one person who satisfies every requirement for the assignment.
The selected person must satisfy all of the following requirements:

Requirements:
1. Research experience is required.
2. The selected candidate must be available on Tuesday.
3. Only candidates who can complete tasks independently are eligible.
4. Candidates must have valid local work authorization.

Candidates:
A. Gray can participate on Tuesday. Gray lacks prior research work experience. Gray is able to make progress independently. Gray has local work authorization.
B. Avery has prior experience with research work. Avery cannot complete tasks independently. Avery can participate on Tuesday. Avery does not meet the local work permit requirement.
C. Blair has local work authorization, and Blair is unavailable on Tuesday. In addition, Blair can work without close guidance, and Blair is familiar with research project workflows.
D. Hayden is available for Tuesday work, and Hayden is familiar with research project workflows. In addition, Hayden can work without close guidance, and Hayden has local work authorization.

Which candidate should receive the project role?

### Six Runs

- `llama` run `1` seed `11`: answer=`D`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate D, Hayden, meets all of the requirements. Hayden has prior research experience, is available on Tuesday, can complete tasks independently, has valid local work authorization, and meets all other requirements.
- `llama` run `2` seed `22`: answer=`D`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate D meets all the requirements. D has research experience, is available on Tuesday, can complete tasks independently, has valid local work authorization, and meets the other requirements.
- `llama` run `3` seed `33`: answer=`D`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate D, Hayden, meets all of the requirements. Hayden has prior research experience, is available to work on Tuesday, can complete tasks independently, has valid local work authorization, and meets the other requirements.
- `qwen` run `1` seed `11`: answer=`D`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate D satisfies all the requirements: has research experience (familiar with research project workflows), is available on Tuesday, can complete tasks independently (can work without close guidance), and has valid local work authorization. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`D`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate D satisfies all the requirements: has research experience (familiar with research project workflows), is available on Tuesday, can complete tasks independently (can work without close guidance), and has valid local work authorization. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`D`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate D satisfies all requirements: has research experience (familiar with research project workflows), is available on Tuesday, can complete tasks independently (can work without close guidance), and has valid local work authorization. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 0, 'C': 0, 'D': 3, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 0, 'C': 0, 'D': 3, 'invalid': 0}`
Observed wrong options: `[]`
Observed wrong violation signatures: `{}`

## attr_en_000016_original

- screening_category: `mildly_vulnerable`
- MAD priority: `medium`
- Gold: `C`
- empirical_accuracy: `0.8333`

### Question

A project leader must choose one qualified researcher from four applicants.
The selected person must satisfy all of the following requirements:

Requirements:
1. Candidates must have experience collaborating with a team.
2. The selected candidate must be available in the morning.
3. Security clearance is required.
4. Candidates must have experience with quality control work.

Candidates:
A. Casey is available in the morning. Casey has valid security clearance. Casey has no background in quality review work. Casey has experience working with project teams.
B. Rowan has not collaborated on team projects, and Rowan lacks the required security authorization. In addition, Rowan can participate during the morning, and Rowan has worked on quality assurance tasks.
C. Blair has collaborated on team projects, and Blair has the required security authorization. In addition, Blair can participate during the morning, and Blair has experience with quality control processes.
D. Ellis has the required security authorization, Ellis has experience with quality control processes, Ellis cannot work in the morning time slot, and Ellis has collaborated on team projects.

Which candidate satisfies all of the requirements?

### Six Runs

- `llama` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all of the requirements: Blair has experience collaborating with a team, Blair is available in the morning, Blair has valid security clearance, and Blair has experience with quality control work.
- `llama` run `2` seed `22`: answer=`B`, correct=`False`, confidence=`0.85`, violation=`['C1', 'C3']`
  reasoning: Candidate B satisfies all of the requirements. Candidate B has experience working on team projects, has valid security clearance, can participate during the morning, and has worked on quality assurance tasks.
- `llama` run `3` seed `33`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Blair has experience collaborating with a team, Blair is available in the morning, Blair has valid security clearance, and Blair has experience with quality control processes.
- `qwen` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: has team collaboration experience, is available in the morning, has security clearance, and has experience with quality control processes. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: has experience collaborating with a team, is available in the morning, has security clearance, and has experience with quality control work. Other candidates fail to meet at least one requirement.
- `qwen` run `3` seed `33`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all requirements: has team collaboration experience, is available in the morning, has security clearance, and has experience with quality control processes. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 0, 'C': 3, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 1, 'C': 2, 'D': 0, 'invalid': 0}`
Observed wrong options: `['B']`
Observed wrong violation signatures: `{'B': ['C1', 'C3']}`

## attr_en_000018_original

- screening_category: `mildly_vulnerable`
- MAD priority: `medium`
- Gold: `B`
- empirical_accuracy: `0.8333`

### Question

Four candidates are being considered based on their availability and participation constraints.
The selected person must satisfy all of the following requirements:

Requirements:
1. The candidate must be available for on-site work.
2. Only candidates who can participate remotely are eligible.
3. Weekend availability is required.

Candidates:
A. Jamie can join weekend project activities. Jamie can participate on site. Jamie cannot work remotely.
B. Emerson can work remotely. Emerson can participate on site. Emerson can participate on the weekend.
C. Ellis cannot work remotely, Ellis is not available for on-site work, and Ellis is available for weekend work.
D. Elliot can participate on site, Elliot cannot join weekend project activities, and Elliot can work remotely.

Which candidate matches every scheduling requirement?

### Six Runs

- `llama` run `1` seed `11`: answer=`C`, correct=`False`, confidence=`0.95`, violation=`['C1', 'C2']`
  reasoning: Candidate C matches every scheduling requirement because C can participate on the weekend, and C can participate on site. Candidate C does not require remote participation, and therefore, does not violate any requirements.
- `llama` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`1.0`, violation=`[]`
  reasoning: Candidate B satisfies all of the requirements. They can work remotely, participate on site, and are available on weekends.
- `llama` run `3` seed `33`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all of the requirements: B can participate on site, B can work remotely, and B can participate on the weekend.
- `qwen` run `1` seed `11`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all requirements: available for on-site work, can participate remotely, and is available for weekend work. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate B satisfies all the requirements: available for on-site work, can participate remotely, and is available for weekend work. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate B satisfies all requirements: available for on-site work, can participate remotely, and is available for weekend work. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 3, 'C': 0, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 2, 'C': 1, 'D': 0, 'invalid': 0}`
Observed wrong options: `['C']`
Observed wrong violation signatures: `{'C': ['C1', 'C2']}`

## attr_en_000047_original

- screening_category: `mildly_vulnerable`
- MAD priority: `high`
- Gold: `B`
- empirical_accuracy: `0.8333`

### Question

Four candidates are being considered based on their availability and participation constraints.
The selected person must satisfy all of the following requirements:

Requirements:
1. Candidates who need extra equipment support are ineligible.
2. Only candidates who can join next month are eligible.
3. The candidate must be available for on-site work.
4. Monday availability is required.

Candidates:
A. Arden is unavailable next month, and Arden can join the project on Monday. In addition, Arden can work at the project location, and Arden would require additional specialized equipment.
B. Harper does not need extra equipment support. Harper is available for Monday work. Harper can work at the project location. Harper can start participating next month.
C. Avery can work at the project location. Avery cannot join project work on Monday. Avery can join the project next month. Avery can participate without additional specialized equipment.
D. Tatum is available next month. Tatum cannot participate on site. Tatum does not need extra equipment support. Tatum can join the project on Monday.

Which participant is eligible based on the stated constraints?

### Six Runs

- `llama` run `1` seed `11`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Harper is the only participant who meets all of the requirements. Harper does not need extra equipment support, Harper is available for Monday work, Harper can work at the project location, and Harper can start participating next month.
- `llama` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Harper is eligible because Harper does not need extra equipment support, Harper is available for Monday work, Harper can work at the project location, and Harper can start participating next month.
- `llama` run `3` seed `33`: answer=`D`, correct=`False`, confidence=`0.95`, violation=`['C3']`
  reasoning: To determine the eligible participant, we must check each requirement against the candidate's characteristics. Requirement 1: Candidates who need extra equipment support are ineligible. Candidates A, C, and D do not require extra equipment support, making them eligible for this requirement. Requirement 2: Only candidates who can join next month are eligible. Candidates B, C, and D can join the project next month, making them eligible for this requirement. Requirement 3: The candidate must be available for on-site work. Candidates A, C, and D can work at the project location, making them eligible for this requirement. Requirement 4: Monday availability is required. Candidates A, B, and D can join the project on Monday, making them eligible for this requirement. Based on the analysis of all the requirements, it is clear that Candidate D is the only one who satisfies all the requirements.
- `qwen` run `1` seed `11`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate B satisfies all requirements: they do not need extra equipment support, can join next month, are available for on-site work, and are available on Monday. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all the requirements: they do not need extra equipment support, can join next month, are available for on-site work, and are available on Monday.
- `qwen` run `3` seed `33`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all requirements: does not need extra equipment support, can join next month, is available for on-site work, and is available on Monday.

Qwen answers: `{'A': 0, 'B': 3, 'C': 0, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 2, 'C': 0, 'D': 1, 'invalid': 0}`
Observed wrong options: `['D']`
Observed wrong violation signatures: `{'D': ['C3']}`

## attr_en_000063_original

- screening_category: `mildly_vulnerable`
- MAD priority: `high`
- Gold: `B`
- empirical_accuracy: `0.8333`

### Question

A project team needs to assign one member to a specialized task.
The selected person must satisfy all of the following requirements:

Requirements:
1. Only candidates who can participate on Tuesday are eligible.
2. Only candidates who have worked on software implementation are eligible.
3. Only candidates with practical data analysis experience are eligible.

Candidates:
A. Reese lacks practical experience analyzing datasets. In addition, Reese has practical programming experience, and Reese is available for Tuesday work.
B. Cameron is available for Tuesday work. In addition, Cameron has practical experience analyzing datasets, and Cameron has handled software implementation work.
C. Morgan lacks software implementation experience. In addition, Morgan has performed data analysis in previous work, and Morgan can join the project on Tuesday.
D. Taylor has handled software implementation work, Taylor has performed data analysis in previous work, and Taylor cannot participate on Tuesday.

Which team member satisfies every assignment requirement?

### Six Runs

- `llama` run `1` seed `11`: answer=`C`, correct=`False`, confidence=`0.95`, violation=`['C2']`
  reasoning: Candidate C satisfies all of the following requirements: Only candidates who can participate on Tuesday are eligible. Only candidates who have worked on software implementation are eligible. Only candidates with practical data analysis experience are eligible. Candidate C is available for Tuesday work, has handled software implementation work, and has performed data analysis in previous work.
- `llama` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all of the requirements. Candidate B can participate on Tuesday, has worked on software implementation, and has practical data analysis experience.
- `llama` run `3` seed `33`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies every requirement. Candidate B is available for Tuesday work, has practical experience analyzing datasets, and has handled software implementation work.
- `qwen` run `1` seed `11`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all three requirements: available on Tuesday, has software implementation experience, and has practical data analysis experience. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all three requirements: available on Tuesday, has software implementation experience, and has practical data analysis experience. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B satisfies all requirements: available on Tuesday, has software implementation experience, and has practical data analysis experience. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 3, 'C': 0, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 2, 'C': 1, 'D': 0, 'invalid': 0}`
Observed wrong options: `['C']`
Observed wrong violation signatures: `{'C': ['C2']}`

## attr_en_000012_original

- screening_category: `mixed_correctness`
- MAD priority: `high`
- Gold: `B`
- empirical_accuracy: `0.6667`

### Question

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

### Six Runs

- `llama` run `1` seed `11`: answer=`D`, correct=`False`, confidence=`1.0`, violation=`['C3']`
  reasoning: Candidate D meets all scheduling requirements. Candidate D can participate on Monday, can work on-site, and meets the other requirements.
- `llama` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate B meets all the requirements. B can participate on Monday, B can adapt to flexible scheduling, and B can work at the project location.
- `llama` run `3` seed `33`: answer=`D`, correct=`False`, confidence=`0.85`, violation=`['C3']`
  reasoning: Candidate D, Elliot, meets all of the scheduling requirements. Elliot can participate on Monday, Elliot can work on-site, and Elliot does not have flexible scheduling requirements.
- `qwen` run `1` seed `11`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate B satisfies all requirements: on-site work capability, participation on Monday, and flexibility in scheduling. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate B satisfies all the requirements: on-site work capability, participation on Monday, and adaptability to flexible scheduling. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`B`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate B satisfies all requirements: on-site work capability, participation on Monday, and adaptability to flexible scheduling. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 3, 'C': 0, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 1, 'C': 0, 'D': 2, 'invalid': 0}`
Observed wrong options: `['D']`
Observed wrong violation signatures: `{'D': ['C3']}`

## attr_en_000014_original

- screening_category: `mixed_correctness`
- MAD priority: `high`
- Gold: `C`
- empirical_accuracy: `0.5000`

### Question

The project manager must select one person who satisfies every requirement for the assignment.
The selected person must satisfy all of the following requirements:

Requirements:
1. The selected candidate must be able to participate on the weekend.
2. Applicants must have experience working with machine learning systems.
3. Morning availability is required.
4. Remote work capability is required.

Candidates:
A. Kris is unavailable on the weekend. Kris can work remotely. Kris has practical machine learning experience. Kris is available in the morning.
B. Milan has not worked with machine learning before, Milan can work in the morning time slot, Milan has the setup needed for remote collaboration, and Milan can join weekend project activities.
C. Finley can work remotely. Finley has worked on machine learning projects. Finley is available in the morning. Finley is available for weekend work.
D. Casey has hands-on experience with machine learning systems, Casey is available for weekend work, Casey is not able to participate through remote work, and Casey is unavailable in the morning.

Which person is eligible for the assignment?

### Six Runs

- `llama` run `1` seed `11`: answer=`B`, correct=`False`, confidence=`0.95`, violation=`['C2']`
  reasoning: Milan satisfies all of the given requirements. Milan can participate on the weekend, has experience working with machine learning systems, is available in the morning, and can work remotely.
- `llama` run `2` seed `22`: answer=`B`, correct=`False`, confidence=`0.95`, violation=`['C2']`
  reasoning: Milan satisfies all of the requirements for the assignment. Milan can participate on the weekend, has experience working with machine learning systems, is available in the morning, and has the capability to work remotely.
- `llama` run `3` seed `33`: answer=`B`, correct=`False`, confidence=`0.95`, violation=`['C2']`
  reasoning: Milan satisfies every requirement for the assignment. Milan can work on the weekend, has experience working with machine learning systems, is available in the morning, and has the capability to work remotely.
- `qwen` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: they can participate on the weekend, have experience with machine learning systems, are available in the morning, and can work remotely. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: they can participate on the weekend, have experience with machine learning systems, are available in the morning, and can work remotely. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all requirements: they can participate on the weekend, have experience with machine learning systems, are available in the morning, and can work remotely. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 0, 'C': 3, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 3, 'C': 0, 'D': 0, 'invalid': 0}`
Observed wrong options: `['B']`
Observed wrong violation signatures: `{'B': ['C2']}`

## attr_en_000015_original

- screening_category: `mixed_correctness`
- MAD priority: `high`
- Gold: `A`
- empirical_accuracy: `0.5000`

### Question

The project manager must select one person who satisfies every requirement for the assignment.
The selected person must satisfy all of the following requirements:

Requirements:
1. Only candidates who can participate during the morning are eligible.
2. The candidate must be able to work independently.
3. Tuesday availability is required.
4. Client communication experience is required.

Candidates:
A. Emerson has practical client communication experience. Emerson can complete tasks independently. Emerson is available in the morning. Emerson can participate on Tuesday.
B. Briar can join the project on Tuesday, and Briar has not communicated directly with clients. In addition, Briar can participate during the morning, and Briar can work without close guidance.
C. Riley has communicated directly with clients. Riley needs close guidance to work. Riley is unavailable in the morning. Riley is available for Tuesday work.
D. Jordan has handled client-facing discussions, and Jordan is unavailable on Tuesday. In addition, Jordan can work in the morning time slot, and Jordan can work without close guidance.

Which team member satisfies every assignment requirement?

### Six Runs

- `llama` run `1` seed `11`: answer=`D`, correct=`False`, confidence=`0.95`, violation=`['C3']`
  reasoning: Jordan is the only candidate who satisfies every requirement. Jordan has client communication experience, can work independently, is available in the morning, and can participate on Tuesday.
- `llama` run `2` seed `22`: answer=`D`, correct=`False`, confidence=`0.85`, violation=`['C3']`
  reasoning: Emerson (A) and Jordan (D) are the only candidates available in the morning. Among them, Jordan is the only one who has handled client-facing discussions, which is a required skill. Therefore, Jordan is the only candidate who satisfies every assignment requirement.
- `llama` run `3` seed `33`: answer=`None`, correct=`False`, confidence=`None`, violation=`[]`
  reasoning: 
- `qwen` run `1` seed `11`: answer=`A`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate A satisfies all the requirements: they can participate during the morning, can work independently, are available on Tuesday, and have client communication experience. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`A`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate A satisfies all the requirements: they can participate during the morning, can work independently, are available on Tuesday, and have client communication experience. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`A`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate A satisfies all requirements: can participate during the morning, can work independently, is available on Tuesday, and has client communication experience.

Qwen answers: `{'A': 3, 'B': 0, 'C': 0, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 0, 'C': 0, 'D': 2, 'invalid': 1}`
Observed wrong options: `['D']`
Observed wrong violation signatures: `{'D': ['C3']}`

## attr_en_000019_original

- screening_category: `mixed_correctness`
- MAD priority: `high`
- Gold: `C`
- empirical_accuracy: `0.6667`

### Question

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

### Six Runs

- `llama` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all of the requirements: Research experience is required (C has participated in research projects), A relevant certificate is required (C holds a relevant professional certificate), The candidate must be able to work independently (C can work without close guidance), and Teamwork experience is required (C has experience working with project teams).
- `llama` run `2` seed `22`: answer=`A`, correct=`False`, confidence=`0.95`, violation=`['C2']`
  reasoning: Milan has research experience, holds a relevant certificate, can work independently, and has teamwork experience. Therefore, Milan satisfies all of the requirements.
- `llama` run `3` seed `33`: answer=`A`, correct=`False`, confidence=`0.85`, violation=`['C2']`
  reasoning: Milan has research experience, a relevant certificate, and the ability to work independently. Milan also has experience working in teams, making Milan the candidate who satisfies all of the requirements.
- `qwen` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: has research experience, holds a relevant certificate, can work independently, and has teamwork experience. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: has research experience, holds a relevant certificate, can work independently, and has teamwork experience. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: has research experience, holds a relevant certificate, can work independently, and has teamwork experience. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 0, 'C': 3, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 2, 'B': 0, 'C': 1, 'D': 0, 'invalid': 0}`
Observed wrong options: `['A']`
Observed wrong violation signatures: `{'A': ['C2']}`

## attr_en_000022_original

- screening_category: `mixed_correctness`
- MAD priority: `medium`
- Gold: `C`
- empirical_accuracy: `0.5000`

### Question

A team is selecting one participant whose availability matches all project requirements.
The selected person must satisfy all of the following requirements:

Requirements:
1. Monday availability is required.
2. Remote work capability is required.
3. Only candidates who can participate on site are eligible.
4. Tuesday availability is required.
5. The candidate must be able to work flexible hours.

Candidates:
A. Hayden lacks the setup needed for remote collaboration, Hayden is available for Tuesday work, Hayden is available for Monday work, Hayden can participate on site, and Hayden is not able to handle variable work hours.
B. Skyler is unavailable on Monday, Skyler cannot work flexible hours, Skyler cannot work remotely, Skyler is unavailable on Tuesday, and Skyler is not available for on-site work.
C. Sage is available for Tuesday work, Sage is available for on-site work, Sage is available for Monday work, Sage can adapt to flexible scheduling, and Sage is able to participate through remote work.
D. Arden cannot join project work on Tuesday. Arden can work remotely. Arden can work flexible hours. Arden is available for Monday work. Arden cannot work at the project location.

Which participant is eligible based on the stated constraints?

### Six Runs

- `llama` run `1` seed `11`: answer=`D`, correct=`False`, confidence=`0.95`, violation=`['C3', 'C4']`
  reasoning: Arden is the only participant who meets all the requirements: remote work capability, flexible hours, and no on-site work requirement.
- `llama` run `2` seed `22`: answer=`D`, correct=`False`, confidence=`0.95`, violation=`['C3', 'C4']`
  reasoning: To determine the eligible participant, we must carefully evaluate each requirement. Candidate D, Arden, meets the following requirements: remote work capability, flexible hours, Monday availability, and Tuesday unavailability. Therefore, based on the stated constraints, Arden is the eligible participant.
- `llama` run `3` seed `33`: answer=`D`, correct=`False`, confidence=`0.95`, violation=`['C3', 'C4']`
  reasoning: Arden meets all of the stated constraints: available on Monday, able to work remotely, able to work flexible hours, and unable to work at the project location.
- `qwen` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: availability on Monday and Tuesday, remote work capability, on-site participation eligibility, and flexible hours. Other candidates fail one or more requirements.
- `qwen` run `2` seed `22`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: Monday availability, remote work capability, on-site participation eligibility, Tuesday availability, and flexible hours capability. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all requirements: availability on Monday and Tuesday, remote work capability, on-site participation eligibility, and flexible hours capability. Other candidates fail one or more requirements.

Qwen answers: `{'A': 0, 'B': 0, 'C': 3, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 0, 'C': 0, 'D': 3, 'invalid': 0}`
Observed wrong options: `['D']`
Observed wrong violation signatures: `{'D': ['C3', 'C4']}`

## attr_en_000040_original

- screening_category: `mixed_correctness`
- MAD priority: `high`
- Gold: `C`
- empirical_accuracy: `0.5000`

### Question

Four candidates are being considered based on their availability and participation constraints.
The selected person must satisfy all of the following requirements:

Requirements:
1. The candidate must have no scheduling conflict.
2. The selected candidate must be able to participate on the weekend.
3. The candidate must be available for on-site work.

Candidates:
A. Sage can participate on the weekend. Sage has a scheduling conflict with the project. Sage is available for on-site work.
B. Logan can join weekend project activities. Logan is not available for on-site work. Logan can avoid schedule conflicts for this role.
C. Indigo can participate on site, Indigo's schedule fits the required timing, and Indigo can participate on the weekend.
D. Taylor is unavailable on the weekend, Taylor has no scheduling conflict with the project, and Taylor can work at the project location.

Which participant is eligible based on the stated constraints?

### Six Runs

- `llama` run `1` seed `11`: answer=`D`, correct=`False`, confidence=`0.95`, violation=`['C2']`
  reasoning: Taylor has no scheduling conflict with the project, Taylor is available to work at the project location, and Taylor can avoid working on the weekend.
- `llama` run `2` seed `22`: answer=`D`, correct=`False`, confidence=`1.0`, violation=`['C2']`
  reasoning: Taylor has no scheduling conflict with the project, can work at the project location, and is available on the weekend.
- `llama` run `3` seed `33`: answer=`D`, correct=`False`, confidence=`0.95`, violation=`['C2']`
  reasoning: Taylor has no scheduling conflict, can participate on-site, and is available to work at the project location. Additionally, Taylor is unavailable on the weekend, which does not disqualify Taylor from the role since the requirement is to participate on the weekend, which Taylor is not available to do.
- `qwen` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: no scheduling conflict, able to participate on the weekend, and available for on-site work. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: no scheduling conflict, able to participate on the weekend, and available for on-site work. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all requirements: no scheduling conflict, able to participate on the weekend, and available for on-site work. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 0, 'C': 3, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 0, 'C': 0, 'D': 3, 'invalid': 0}`
Observed wrong options: `['D']`
Observed wrong violation signatures: `{'D': ['C2']}`

## attr_en_000054_original

- screening_category: `mixed_correctness`
- MAD priority: `high`
- Gold: `C`
- empirical_accuracy: `0.6667`

### Question

A team is selecting one participant whose availability matches all project requirements.
The selected person must satisfy all of the following requirements:

Requirements:
1. Only candidates who can participate during the afternoon are eligible.
2. The candidate must not require additional specialized equipment.
3. The selected candidate must be available on Tuesday.
4. The selected candidate must be available next month.

Candidates:
A. Kris can participate on Tuesday. Kris cannot work in the afternoon time slot. Kris does not need extra equipment support. Kris cannot start participating next month.
B. Payton does not need extra equipment support, and Payton cannot join project work on Tuesday. In addition, Payton can start participating next month, and Payton can work in the afternoon time slot.
C. Tatum can work with the equipment already available. Tatum is available for Tuesday work. Tatum can work in the afternoon time slot. Tatum can join the project next month.
D. Wren needs extra equipment support to participate, Wren is available in the afternoon, Wren is available next month, and Wren is available for Tuesday work.

Which participant is eligible based on the stated constraints?

### Six Runs

- `llama` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Tatum can work in the afternoon time slot, does not need extra equipment support, is available on Tuesday, and can join the project next month.
- `llama` run `2` seed `22`: answer=`B`, correct=`False`, confidence=`0.95`, violation=`['C3']`
  reasoning: The selected candidate must be available on Tuesday and in the afternoon. The candidate must not require additional specialized equipment. The selected candidate must be available next month. Payton meets all of these requirements, making Payton eligible.
- `llama` run `3` seed `33`: answer=`B`, correct=`False`, confidence=`0.85`, violation=`['C3']`
  reasoning: The selected candidate must be available on Tuesday and in the afternoon time slot. The candidate must also not require additional specialized equipment. Candidate B satisfies all of these requirements.
- `qwen` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all requirements: available on Tuesday, can participate during the afternoon, does not require additional specialized equipment, and is available next month. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: available on Tuesday, can participate in the afternoon, does not require additional equipment, and is available next month. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all requirements: can participate during the afternoon, does not require additional equipment, is available on Tuesday, and is available next month. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 0, 'C': 3, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 2, 'C': 1, 'D': 0, 'invalid': 0}`
Observed wrong options: `['B']`
Observed wrong violation signatures: `{'B': ['C3']}`

## attr_en_000064_original

- screening_category: `mixed_correctness`
- MAD priority: `high`
- Gold: `C`
- empirical_accuracy: `0.5000`

### Question

A project leader must choose one qualified researcher from four applicants.
The selected person must satisfy all of the following requirements:

Requirements:
1. Client communication experience is required.
2. Candidates must have valid local work authorization.
3. The candidate must be able to work without additional supervision.
4. The selected candidate must have no conflict of interest.

Candidates:
A. Marley does not require extra oversight for this role, Marley has a valid local work permit, Marley has a conflict of interest related to the project, and Marley has handled client-facing discussions.
B. Elliot does not have a valid local work permit, and Elliot cannot carry out the work without additional supervision. In addition, Elliot is free of conflicts for this project, and Elliot has handled client-facing discussions.
C. Jules does not require extra oversight for this role, and Jules is free of conflicts for this project. In addition, Jules has communicated directly with clients, and Jules has a valid local work permit.
D. Kris has no project-related conflict requiring recusal. Kris meets the local work permit requirement. Kris lacks client-facing communication experience. Kris can carry out the work independently.

Which candidate satisfies all of the requirements?

### Six Runs

- `llama` run `1` seed `11`: answer=`B`, correct=`False`, confidence=`0.95`, violation=`['C2', 'C3']`
  reasoning: Candidate B satisfies all of the requirements: Client communication experience is required, and Candidate B has handled client-facing discussions. Additionally, Candidate B has a valid local work permit, and Candidate B is able to carry out the work independently. Furthermore, Candidate B is free of conflicts for this project.
- `llama` run `2` seed `22`: answer=`B`, correct=`False`, confidence=`0.95`, violation=`['C2', 'C3']`
  reasoning: Candidate B satisfies all of the requirements. They have valid local work authorization, can work independently, and have no conflict of interest.
- `llama` run `3` seed `33`: answer=`D`, correct=`False`, confidence=`0.95`, violation=`['C1']`
  reasoning: Candidate D, Kris, meets all of the requirements. Kris has client communication experience, has a valid local work permit, is able to work without additional supervision, and has no conflict of interest. Therefore, Kris is the only candidate who satisfies all of the requirements.
- `qwen` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: they do not require extra oversight, have a valid local work permit, have no conflict of interest, and have client communication experience.
- `qwen` run `2` seed `22`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: they do not require extra oversight, have a valid local work permit, have no conflict of interest, and have client communication experience.
- `qwen` run `3` seed `33`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all requirements: has no need for extra oversight, has valid local work authorization, has no conflict of interest, and has client communication experience.

Qwen answers: `{'A': 0, 'B': 0, 'C': 3, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 2, 'C': 0, 'D': 1, 'invalid': 0}`
Observed wrong options: `['B', 'D']`
Observed wrong violation signatures: `{'B': ['C2', 'C3'], 'D': ['C1']}`

## attr_en_000066_original

- screening_category: `mixed_correctness`
- MAD priority: `high`
- Gold: `C`
- empirical_accuracy: `0.5000`

### Question

A project team needs to assign one member to a specialized task.
The selected person must satisfy all of the following requirements:

Requirements:
1. The candidate must be able to work flexible hours.
2. The candidate must be available for on-site work.
3. Candidates must have handled management responsibilities before.

Candidates:
A. Jordan can work at the project location, Jordan is able to handle variable work hours, and Jordan has no record of management responsibilities.
B. Jamie cannot participate on site. Jamie has experience managing team activities. Jamie is able to handle variable work hours.
C. Jules can work at the project location. Jules has experience managing team activities. Jules can adapt to flexible scheduling.
D. Milan can participate on site, Milan has previously handled management responsibilities, and Milan is not able to handle variable work hours.

Which candidate should receive the project role?

### Six Runs

- `llama` run `1` seed `11`: answer=`D`, correct=`False`, confidence=`0.95`, violation=`['C1']`
  reasoning: Milan meets all the requirements. Milan can participate on-site, has previously handled management responsibilities, and can adapt to flexible scheduling.
- `llama` run `2` seed `22`: answer=`D`, correct=`False`, confidence=`0.95`, violation=`['C1']`
  reasoning: Candidate D (Milan) satisfies all the requirements. Milan can participate on site, has previously handled management responsibilities, and is able to work flexible hours.
- `llama` run `3` seed `33`: answer=`D`, correct=`False`, confidence=`0.95`, violation=`['C1']`
  reasoning: Candidate D, Milan, meets all of the requirements. Milan is able to work on-site, has experience handling management responsibilities, and can adapt to flexible scheduling.
- `qwen` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all three requirements: can work on-site, has management experience, and can handle flexible hours. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all three requirements: can work on-site, can handle flexible hours, and has management experience. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all three requirements: can work on-site, has management experience, and can handle flexible hours. The other candidates fail to meet at least one requirement.

Qwen answers: `{'A': 0, 'B': 0, 'C': 3, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 0, 'C': 0, 'D': 3, 'invalid': 0}`
Observed wrong options: `['D']`
Observed wrong violation signatures: `{'D': ['C1']}`

## attr_en_000073_original

- screening_category: `mixed_correctness`
- MAD priority: `high`
- Gold: `C`
- empirical_accuracy: `0.5000`

### Question

A research lab is selecting one researcher for a new project.
The selected person must satisfy all of the following requirements:

Requirements:
1. Availability next month is required.
2. The selected candidate must be available on Tuesday.
3. Security clearance is required.
4. Client communication experience is required.

Candidates:
A. Payton does not meet the security clearance requirement, and Payton lacks client-facing communication experience. In addition, Payton can join the project on Tuesday, and Payton can join the project next month.
B. Briar is unavailable on Tuesday, Briar meets the security clearance requirement, Briar can join the project next month, and Briar has practical client communication experience.
C. Jordan has the required security authorization, Jordan can start participating next month, Jordan is available for Tuesday work, and Jordan has practical client communication experience.
D. Drew meets the security clearance requirement. Drew can join the project on Tuesday. Drew is unavailable next month. Drew has communicated directly with clients.

Which applicant should be selected?

### Six Runs

- `llama` run `1` seed `11`: answer=`B`, correct=`False`, confidence=`0.95`, violation=`['C2']`
  reasoning: Briar meets all of the requirements. Briar is available next month, Briar can join the project on Tuesday, Briar meets the security clearance requirement, and Briar has practical client communication experience.
- `llama` run `2` seed `22`: answer=`B`, correct=`False`, confidence=`0.95`, violation=`['C2']`
  reasoning: Briar meets all of the requirements: Briar can join the project next month, Briar is available on Tuesday, Briar meets the security clearance requirement, and Briar has practical client communication experience.
- `llama` run `3` seed `33`: answer=`B`, correct=`False`, confidence=`0.95`, violation=`['C2']`
  reasoning: Briar meets all of the requirements: Briar is available next month, Briar is available on Tuesday, Briar meets the security clearance requirement, and Briar has practical client communication experience.
- `qwen` run `1` seed `11`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: availability next month, availability on Tuesday, security clearance, and client communication experience. Other candidates fail at least one requirement.
- `qwen` run `2` seed `22`: answer=`C`, correct=`True`, confidence=`0.85`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: availability next month, availability on Tuesday, security clearance, and client communication experience. Other candidates fail at least one requirement.
- `qwen` run `3` seed `33`: answer=`C`, correct=`True`, confidence=`0.95`, violation=`[]`
  reasoning: Candidate C satisfies all the requirements: availability next month, availability on Tuesday, security clearance, and client communication experience. Other candidates fail at least one requirement.

Qwen answers: `{'A': 0, 'B': 0, 'C': 3, 'D': 0, 'invalid': 0}`
Llama answers: `{'A': 0, 'B': 3, 'C': 0, 'D': 0, 'invalid': 0}`
Observed wrong options: `['B']`
Observed wrong violation signatures: `{'B': ['C2']}`
