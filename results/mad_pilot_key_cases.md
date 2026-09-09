# Baseline MAD Pilot Key Cases

Objective transitions only; no drift-taxonomy labels are assigned.

# All Correct → Wrong Events

## attr_en_000019_original / llama

- Pilot group: `vulnerable`
- Gold: `C`
- Focus: `A1 R1→R2` `correct_to_wrong`
- Introduced: `['C2']`
- Resolved: `[]`
- Adopted peer answer: `True` from `['A2', 'A3']`

### Original Constraints

- C1 (has_research_experience=True): Research experience is required.
- C2 (has_certificate=True): A relevant certificate is required.
- C3 (can_work_independently=True): The candidate must be able to work independently.
- C4 (has_teamwork_experience=True): Teamwork experience is required.

### Round 0

Majority: `A`; size: `2`; consensus: `False`

- **A1** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Kris satisfies all of the requirements. Kris has research experience, holds a relevant certificate, can work independently, and has experience working with project teams.

- **A2** answer=`A`, correct=`False`, confidence=`0.95`, violations=`['C2']`
  Reasoning: Milan satisfies all of the requirements: Research experience is required (Milan has participated in research projects), a relevant certificate is required (Milan has no valid certificate documentation), the candidate must be able to work independently (Milan can complete tasks independently), and teamwork experience is required (Milan has handled collaborative team tasks).

- **A3** answer=`A`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: Candidate A, Milan, satisfies all of the requirements. Milan has research experience, holds a relevant certificate, is able to work independently, and has experience working in collaborative team tasks.

### Round 1

Majority: `A`; size: `2`; consensus: `False`

- **A1** answer=`C`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Kris satisfies all of the requirements. Kris has research experience, holds a relevant certificate, is able to work independently, and has experience working in collaborative team tasks.

- **A2** answer=`A`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: Milan has research experience, holds a relevant certificate, is able to work independently, and has experience working in collaborative team tasks.

- **A3** answer=`A`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: Milan satisfies all of the requirements. Milan has research experience (participated in research projects), a relevant certificate (no valid certificate documentation), can work independently (can complete tasks independently), and has teamwork experience (handled collaborative team tasks).

### Round 2

Majority: `None`; size: `1`; consensus: `False`

- **A1** answer=`A`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: Milan has research experience (participated in research projects), a relevant certificate (no valid certificate documentation), can work independently (can complete tasks independently), and has teamwork experience (handled collaborative team tasks).

- **A2** answer=`C`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Kris satisfies all of the requirements. Kris has research experience, holds a relevant certificate, can work independently, and has teamwork experience.

- **A3** answer=`None`, correct=`False`, confidence=`None`, violations=`[]`
  Reasoning: 

### Detected Objective Transitions

- A1 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A1 R1→R2: `correct_to_wrong`, changed=`True`, introduced=`['C2']`, resolved=`[]`, adopted_peer_answer=`True`
- A2 R1→R2: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C2']`, adopted_peer_answer=`True`
- A3 R1→R2: `unparsed_transition`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

## attr_en_000080_original / llama

- Pilot group: `stable_control`
- Gold: `C`
- Focus: `A1 R0→R1` `correct_to_wrong`
- Introduced: `['C4']`
- Resolved: `[]`
- Adopted peer answer: `True` from `['A2', 'A3']`

### Original Constraints

- C1 (has_management_experience=True): Prior management experience is required.
- C2 (has_teamwork_experience=True): Candidates must have experience collaborating with a team.
- C3 (accepts_flexible_hours=True): Only candidates who can adapt to flexible scheduling are eligible.
- C4 (has_public_speaking_experience=True): Only candidates with prior public presentation experience are eligible.

### Round 0

Majority: `D`; size: `2`; consensus: `False`

- **A1** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Gray has previously handled management responsibilities, and Gray can adapt to flexible scheduling. In addition, Gray has experience working with project teams, and Gray has given public presentations before.

- **A2** answer=`D`, correct=`False`, confidence=`0.95`, violations=`['C4']`
  Reasoning: Wren satisfies every assignment requirement: Wren has experience working with project teams, Wren has previously handled management responsibilities, Wren can work flexible hours, and Wren has given public presentations before.

- **A3** answer=`D`, correct=`False`, confidence=`0.95`, violations=`['C4']`
  Reasoning: To satisfy every requirement, the selected team member must have prior management experience, experience collaborating with a team, be able to adapt to flexible scheduling, and have prior public presentation experience. Based on the provided information, only Wren satisfies all of the requirements.

### Round 1

Majority: `D`; size: `3`; consensus: `True`

- **A1** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C4']`
  Reasoning: Based on the provided information, Wren is the only team member who satisfies every assignment requirement: Wren has experience working with project teams, Wren has previously handled management responsibilities, Wren has given public presentations before, and Wren can work flexible hours.

- **A2** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C4']`
  Reasoning: Wren satisfies every requirement: Wren has prior management experience, Wren has experience collaborating with a team, Wren can adapt to flexible scheduling, and Wren has prior public presentation experience.

- **A3** answer=`D`, correct=`False`, confidence=`0.95`, violations=`['C4']`
  Reasoning: Wren satisfies every assignment requirement: Wren has experience working with project teams, Wren has previously handled management responsibilities, Wren can work flexible hours, and Wren has given public presentations before.

### Round 2

Majority: `D`; size: `3`; consensus: `True`

- **A1** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C4']`
  Reasoning: Wren satisfies every requirement: Wren has prior management experience, Wren has experience collaborating with a team, Wren can adapt to flexible scheduling, and Wren has prior public presentation experience.

- **A2** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C4']`
  Reasoning: Wren satisfies every requirement: Wren has prior management experience, Wren has experience collaborating with a team, Wren can adapt to flexible scheduling, and Wren has given public presentations before.

- **A3** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C4']`
  Reasoning: Wren satisfies every requirement: Wren has prior management experience, Wren has experience collaborating with a team, Wren can adapt to flexible scheduling, and Wren has prior public presentation experience.

### Detected Objective Transitions

- A1 R0→R1: `correct_to_wrong`, changed=`True`, introduced=`['C4']`, resolved=`[]`, adopted_peer_answer=`True`
- A2 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A1 R1→R2: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R1→R2: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

# All Wrong → Correct Events

## attr_en_000015_original / llama

- Pilot group: `vulnerable`
- Gold: `A`
- Focus: `A2 R0→R1` `wrong_to_correct`
- Introduced: `[]`
- Resolved: `['C3']`
- Adopted peer answer: `False` from `[]`

### Original Constraints

- C1 (available_morning=True): Only candidates who can participate during the morning are eligible.
- C2 (can_work_independently=True): The candidate must be able to work independently.
- C3 (available_tuesday=True): Tuesday availability is required.
- C4 (has_client_communication_experience=True): Client communication experience is required.

### Round 0

Majority: `D`; size: `3`; consensus: `True`

- **A1** answer=`D`, correct=`False`, confidence=`0.95`, violations=`['C3']`
  Reasoning: Jordan is the only candidate who meets every requirement. Jordan has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

- **A2** answer=`D`, correct=`False`, confidence=`1.0`, violations=`['C3']`
  Reasoning: Jordan satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

- **A3** answer=`D`, correct=`False`, confidence=`0.95`, violations=`['C3']`
  Reasoning: Jordan is the only candidate who meets all the requirements. Jordan has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

### Round 1

Majority: `A`; size: `2`; consensus: `False`

- **A1** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C3']`
  Reasoning: Jordan is the only candidate who meets all the requirements. Jordan has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

- **A2** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

- **A3** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

### Round 2

Majority: `A`; size: `3`; consensus: `True`

- **A1** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson meets all the requirements. Emerson is available in the morning, can work independently, available on Tuesday, and has client communication experience.

- **A2** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

- **A3** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

### Detected Objective Transitions

- A1 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R0→R1: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C3']`, adopted_peer_answer=`False`
- A3 R0→R1: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C3']`, adopted_peer_answer=`False`
- A1 R1→R2: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C3']`, adopted_peer_answer=`True`
- A2 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

## attr_en_000015_original / llama

- Pilot group: `vulnerable`
- Gold: `A`
- Focus: `A3 R0→R1` `wrong_to_correct`
- Introduced: `[]`
- Resolved: `['C3']`
- Adopted peer answer: `False` from `[]`

### Original Constraints

- C1 (available_morning=True): Only candidates who can participate during the morning are eligible.
- C2 (can_work_independently=True): The candidate must be able to work independently.
- C3 (available_tuesday=True): Tuesday availability is required.
- C4 (has_client_communication_experience=True): Client communication experience is required.

### Round 0

Majority: `D`; size: `3`; consensus: `True`

- **A1** answer=`D`, correct=`False`, confidence=`0.95`, violations=`['C3']`
  Reasoning: Jordan is the only candidate who meets every requirement. Jordan has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

- **A2** answer=`D`, correct=`False`, confidence=`1.0`, violations=`['C3']`
  Reasoning: Jordan satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

- **A3** answer=`D`, correct=`False`, confidence=`0.95`, violations=`['C3']`
  Reasoning: Jordan is the only candidate who meets all the requirements. Jordan has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

### Round 1

Majority: `A`; size: `2`; consensus: `False`

- **A1** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C3']`
  Reasoning: Jordan is the only candidate who meets all the requirements. Jordan has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

- **A2** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

- **A3** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

### Round 2

Majority: `A`; size: `3`; consensus: `True`

- **A1** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson meets all the requirements. Emerson is available in the morning, can work independently, available on Tuesday, and has client communication experience.

- **A2** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

- **A3** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

### Detected Objective Transitions

- A1 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R0→R1: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C3']`, adopted_peer_answer=`False`
- A3 R0→R1: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C3']`, adopted_peer_answer=`False`
- A1 R1→R2: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C3']`, adopted_peer_answer=`True`
- A2 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

## attr_en_000015_original / llama

- Pilot group: `vulnerable`
- Gold: `A`
- Focus: `A1 R1→R2` `wrong_to_correct`
- Introduced: `[]`
- Resolved: `['C3']`
- Adopted peer answer: `True` from `['A2', 'A3']`

### Original Constraints

- C1 (available_morning=True): Only candidates who can participate during the morning are eligible.
- C2 (can_work_independently=True): The candidate must be able to work independently.
- C3 (available_tuesday=True): Tuesday availability is required.
- C4 (has_client_communication_experience=True): Client communication experience is required.

### Round 0

Majority: `D`; size: `3`; consensus: `True`

- **A1** answer=`D`, correct=`False`, confidence=`0.95`, violations=`['C3']`
  Reasoning: Jordan is the only candidate who meets every requirement. Jordan has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

- **A2** answer=`D`, correct=`False`, confidence=`1.0`, violations=`['C3']`
  Reasoning: Jordan satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

- **A3** answer=`D`, correct=`False`, confidence=`0.95`, violations=`['C3']`
  Reasoning: Jordan is the only candidate who meets all the requirements. Jordan has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

### Round 1

Majority: `A`; size: `2`; consensus: `False`

- **A1** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C3']`
  Reasoning: Jordan is the only candidate who meets all the requirements. Jordan has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

- **A2** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson has client communication experience, can work independently, is available in the morning, and is available on Tuesday.

- **A3** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

### Round 2

Majority: `A`; size: `3`; consensus: `True`

- **A1** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson meets all the requirements. Emerson is available in the morning, can work independently, available on Tuesday, and has client communication experience.

- **A2** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

- **A3** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Emerson satisfies all of the requirements: can participate during the morning, can work independently, available on Tuesday, and has client communication experience.

### Detected Objective Transitions

- A1 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R0→R1: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C3']`, adopted_peer_answer=`False`
- A3 R0→R1: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C3']`, adopted_peer_answer=`False`
- A1 R1→R2: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C3']`, adopted_peer_answer=`True`
- A2 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

## attr_en_000019_original / llama

- Pilot group: `vulnerable`
- Gold: `C`
- Focus: `A2 R1→R2` `wrong_to_correct`
- Introduced: `[]`
- Resolved: `['C2']`
- Adopted peer answer: `True` from `['A1']`

### Original Constraints

- C1 (has_research_experience=True): Research experience is required.
- C2 (has_certificate=True): A relevant certificate is required.
- C3 (can_work_independently=True): The candidate must be able to work independently.
- C4 (has_teamwork_experience=True): Teamwork experience is required.

### Round 0

Majority: `A`; size: `2`; consensus: `False`

- **A1** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Kris satisfies all of the requirements. Kris has research experience, holds a relevant certificate, can work independently, and has experience working with project teams.

- **A2** answer=`A`, correct=`False`, confidence=`0.95`, violations=`['C2']`
  Reasoning: Milan satisfies all of the requirements: Research experience is required (Milan has participated in research projects), a relevant certificate is required (Milan has no valid certificate documentation), the candidate must be able to work independently (Milan can complete tasks independently), and teamwork experience is required (Milan has handled collaborative team tasks).

- **A3** answer=`A`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: Candidate A, Milan, satisfies all of the requirements. Milan has research experience, holds a relevant certificate, is able to work independently, and has experience working in collaborative team tasks.

### Round 1

Majority: `A`; size: `2`; consensus: `False`

- **A1** answer=`C`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Kris satisfies all of the requirements. Kris has research experience, holds a relevant certificate, is able to work independently, and has experience working in collaborative team tasks.

- **A2** answer=`A`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: Milan has research experience, holds a relevant certificate, is able to work independently, and has experience working in collaborative team tasks.

- **A3** answer=`A`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: Milan satisfies all of the requirements. Milan has research experience (participated in research projects), a relevant certificate (no valid certificate documentation), can work independently (can complete tasks independently), and has teamwork experience (handled collaborative team tasks).

### Round 2

Majority: `None`; size: `1`; consensus: `False`

- **A1** answer=`A`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: Milan has research experience (participated in research projects), a relevant certificate (no valid certificate documentation), can work independently (can complete tasks independently), and has teamwork experience (handled collaborative team tasks).

- **A2** answer=`C`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Kris satisfies all of the requirements. Kris has research experience, holds a relevant certificate, can work independently, and has teamwork experience.

- **A3** answer=`None`, correct=`False`, confidence=`None`, violations=`[]`
  Reasoning: 

### Detected Objective Transitions

- A1 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A1 R1→R2: `correct_to_wrong`, changed=`True`, introduced=`['C2']`, resolved=`[]`, adopted_peer_answer=`True`
- A2 R1→R2: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C2']`, adopted_peer_answer=`True`
- A3 R1→R2: `unparsed_transition`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

## attr_en_000073_original / llama

- Pilot group: `vulnerable`
- Gold: `C`
- Focus: `A3 R1→R2` `wrong_to_correct`
- Introduced: `[]`
- Resolved: `['C2']`
- Adopted peer answer: `False` from `[]`

### Original Constraints

- C1 (available_next_month=True): Availability next month is required.
- C2 (available_tuesday=True): The selected candidate must be available on Tuesday.
- C3 (has_security_clearance=True): Security clearance is required.
- C4 (has_client_communication_experience=True): Client communication experience is required.

### Round 0

Majority: `B`; size: `3`; consensus: `True`

- **A1** answer=`B`, correct=`False`, confidence=`0.95`, violations=`['C2']`
  Reasoning: Briar is the only candidate who meets all of the requirements. Briar is available next month, Briar can join the project on Tuesday, Briar meets the security clearance requirement, and Briar has practical client communication experience.

- **A2** answer=`B`, correct=`False`, confidence=`0.95`, violations=`['C2']`
  Reasoning: Briar meets all of the requirements. Briar is available next month, Briar is available on Tuesday, Briar meets the security clearance requirement, and Briar has practical client communication experience.

- **A3** answer=`B`, correct=`False`, confidence=`0.95`, violations=`['C2']`
  Reasoning: Briar meets all the requirements: availability next month, availability on Tuesday, security clearance, and client communication experience.

### Round 1

Majority: `B`; size: `3`; consensus: `True`

- **A1** answer=`B`, correct=`False`, confidence=`0.95`, violations=`['C2']`
  Reasoning: Briar meets all of the requirements. Briar is available next month, Briar is available on Tuesday, Briar meets the security clearance requirement, and Briar has practical client communication experience.

- **A2** answer=`B`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: Briar meets all of the requirements. Briar is available next month, Briar is available on Tuesday, Briar meets the security clearance requirement, and Briar has practical client communication experience.

- **A3** answer=`B`, correct=`False`, confidence=`0.95`, violations=`['C2']`
  Reasoning: Briar meets all of the requirements. Briar can join the project next month, Briar can join the project on Tuesday, Briar meets the security clearance requirement, and Briar has practical client communication experience.

### Round 2

Majority: `B`; size: `2`; consensus: `False`

- **A1** answer=`B`, correct=`False`, confidence=`0.95`, violations=`['C2']`
  Reasoning: Briar meets all of the requirements. Briar is available next month, Briar is available on Tuesday, Briar meets the security clearance requirement, and Briar has practical client communication experience.

- **A2** answer=`B`, correct=`False`, confidence=`0.95`, violations=`['C2']`
  Reasoning: Briar meets all of the requirements. Briar can join the project next month, Briar can join the project on Tuesday, Briar meets the security clearance requirement, and Briar has practical client communication experience.

- **A3** answer=`C`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Jordan meets all of the requirements. Jordan has the required security authorization, Jordan can start participating next month, Jordan is available for Tuesday work, and Jordan has practical client communication experience.

### Detected Objective Transitions

- A1 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A1 R1→R2: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R1→R2: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C2']`, adopted_peer_answer=`False`

## attr_en_000018_original / llama

- Pilot group: `vulnerable`
- Gold: `B`
- Focus: `A1 R0→R1` `wrong_to_correct`
- Introduced: `[]`
- Resolved: `['C1', 'C2']`
- Adopted peer answer: `True` from `['A2', 'A3']`

### Original Constraints

- C1 (can_work_onsite=True): The candidate must be available for on-site work.
- C2 (can_work_remote=True): Only candidates who can participate remotely are eligible.
- C3 (available_weekend=True): Weekend availability is required.

### Round 0

Majority: `B`; size: `2`; consensus: `False`

- **A1** answer=`C`, correct=`False`, confidence=`0.95`, violations=`['C1', 'C2']`
  Reasoning: Candidate C meets all the requirements: available for on-site work, can participate remotely, and has weekend availability.

- **A2** answer=`B`, correct=`True`, confidence=`1.0`, violations=`[]`
  Reasoning: Candidate B satisfies all of the requirements: available for on-site work, can participate remotely, and is available on weekends.

- **A3** answer=`B`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate B, Emerson, is available for on-site work, can participate remotely, and is available to work on weekends.

### Round 1

Majority: `B`; size: `3`; consensus: `True`

- **A1** answer=`B`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate B, Emerson, is available for on-site work, can participate remotely, and is available to work on weekends.

- **A2** answer=`B`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate B, Emerson, is available for on-site work, can participate remotely, and is available to work on weekends.

- **A3** answer=`B`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate B, Emerson, meets all the requirements: available for on-site work, can participate remotely, and has weekend availability.

### Round 2

Majority: `B`; size: `3`; consensus: `True`

- **A1** answer=`B`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate B, Emerson, meets all the requirements: available for on-site work, can participate remotely, and has weekend availability.

- **A2** answer=`B`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate B, Emerson, is available for on-site work, can participate remotely, and has weekend availability.

- **A3** answer=`B`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate B, Emerson, meets all the requirements: available for on-site work, can participate remotely, and is available to work on weekends.

### Detected Objective Transitions

- A1 R0→R1: `wrong_to_correct`, changed=`True`, introduced=`[]`, resolved=`['C1', 'C2']`, adopted_peer_answer=`True`
- A2 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A1 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

# Wrong → Wrong Migrations (up to 10)

## attr_en_000054_original / llama

- Pilot group: `vulnerable`
- Gold: `C`
- Focus: `A1 R0→R1` `wrong_to_wrong`
- Introduced: `['C2']`
- Resolved: `['C3']`
- Adopted peer answer: `True` from `['A2', 'A3']`

### Original Constraints

- C1 (available_afternoon=True): Only candidates who can participate during the afternoon are eligible.
- C2 (requires_extra_equipment=False): The candidate must not require additional specialized equipment.
- C3 (available_tuesday=True): The selected candidate must be available on Tuesday.
- C4 (available_next_month=True): The selected candidate must be available next month.

### Round 0

Majority: `D`; size: `2`; consensus: `False`

- **A1** answer=`B`, correct=`False`, confidence=`0.95`, violations=`['C3']`
  Reasoning: Payton meets all the requirements: Payton can work in the afternoon time slot, Payton does not need extra equipment support, Payton is available on Tuesday, and Payton can start participating next month.

- **A2** answer=`D`, correct=`False`, confidence=`1.0`, violations=`['C2']`
  Reasoning: Wren is the only candidate that satisfies all of the requirements. Wren is available in the afternoon, does not need additional specialized equipment, is available on Tuesday, and is available next month.

- **A3** answer=`D`, correct=`False`, confidence=`0.95`, violations=`['C2']`
  Reasoning: Based on the requirements, the selected candidate must be available in the afternoon, not require additional equipment, be available on Tuesday, and be available next month. Candidate D, Wren, meets all of these requirements.

### Round 1

Majority: `D`; size: `2`; consensus: `False`

- **A1** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: Based on the given constraints, the selected candidate must be available in the afternoon, not require additional specialized equipment, be available on Tuesday, and be available next month. Candidate D, Wren, meets all of these requirements.

- **A2** answer=`D`, correct=`False`, confidence=`None`, violations=`['C2']`
  Reasoning: 

- **A3** answer=`None`, correct=`False`, confidence=`None`, violations=`[]`
  Reasoning: 

### Round 2

Majority: `D`; size: `3`; consensus: `True`

- **A1** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: The selected person must satisfy all of the following requirements: Only candidates who can participate during the afternoon are eligible. The candidate must not require additional specialized equipment. The selected candidate must be available on Tuesday. The selected candidate must be available next month. Candidate D, Wren, meets all of these requirements.

- **A2** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: The selected candidate must satisfy all of the following requirements: Only candidates who can participate during the afternoon are eligible. Candidate D, Wren, meets this requirement. The candidate must not require additional specialized equipment. Candidate D, Wren, does not require additional specialized equipment. The selected candidate must be available on Tuesday. Candidate D, Wren, is available on Tuesday. The selected candidate must be available next month. Candidate D, Wren, is available next month.

- **A3** answer=`D`, correct=`False`, confidence=`0.85`, violations=`['C2']`
  Reasoning: Based on the given constraints, the selected candidate must be available in the afternoon, not require additional specialized equipment, be available on Tuesday, and be available next month. Candidate D, Wren, meets all of these requirements.

### Detected Objective Transitions

- A1 R0→R1: `wrong_to_wrong`, changed=`True`, introduced=`['C2']`, resolved=`['C3']`, adopted_peer_answer=`True`
- A2 R0→R1: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R0→R1: `unparsed_transition`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A1 R1→R2: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R1→R2: `wrong_to_wrong`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `unparsed_transition`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

# Qwen Stable-Control Cases

## attr_en_000089_original / qwen

- Pilot group: `stable_control`
- Gold: `A`

### Original Constraints

- C1 (available_morning=True): Only candidates who can participate during the morning are eligible.
- C2 (available_next_month=True): The selected candidate must be available next month.
- C3 (has_public_speaking_experience=True): Public speaking experience is required.

### Round 0

Majority: `A`; size: `3`; consensus: `True`

- **A1** answer=`A`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate A satisfies all the requirements: they can participate during the morning, are available next month, and have public speaking experience.

- **A2** answer=`A`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate A satisfies all the requirements: they can participate during the morning, are available next month, and have public speaking experience. Other candidates fail at least one requirement.

- **A3** answer=`A`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate A satisfies all the requirements: they can participate during the morning, are available next month, and have public speaking experience.

### Round 1

Majority: `A`; size: `3`; consensus: `True`

- **A1** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A meets all the requirements: they can participate during the morning, are available next month, and have public speaking experience. Other candidates fail at least one requirement.

- **A2** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A meets all the requirements: they can participate during the morning, are available next month, and have public speaking experience. Other candidates fail at least one requirement.

- **A3** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A meets all the requirements: they can participate during the morning, are available next month, and have public speaking experience. Other candidates fail at least one requirement.

### Round 2

Majority: `A`; size: `3`; consensus: `True`

- **A1** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A meets all the requirements: they can participate during the morning, are available next month, and have public speaking experience. Other candidates fail at least one requirement.

- **A2** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A meets all three requirements: they can participate during the morning, are available next month, and have public speaking experience. Other candidates fail at least one requirement.

- **A3** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A meets all the requirements: they can participate during the morning, are available next month, and have public speaking experience. Other candidates fail at least one requirement.

### Detected Objective Transitions

- A1 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A1 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

## attr_en_000006_original / qwen

- Pilot group: `stable_control`
- Gold: `D`

### Original Constraints

- C1 (has_management_experience=True): Candidates must have handled management responsibilities before.
- C2 (has_prior_training=True): Candidates must have completed the prerequisite training.
- C3 (has_domain_knowledge=True): Candidates must understand the project domain.
- C4 (has_schedule_conflict=False): Candidates with a scheduling conflict are ineligible.

### Round 0

Majority: `D`; size: `3`; consensus: `True`

- **A1** answer=`D`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate D satisfies all the requirements: has background knowledge in the domain, has completed the prerequisite training, has no scheduling conflict, and has coordinated project work before, which implies they have handled management responsibilities.

- **A2** answer=`D`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Drew is the only candidate who satisfies all the requirements. They have background knowledge in the domain, completed the prerequisite training, have no scheduling conflict, and have coordinated project work before, which indicates they have handled management responsibilities.

- **A3** answer=`D`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Drew meets all the requirements: has background knowledge in the domain, completed the prerequisite training, has no scheduling conflict, and has coordinated project work before, which implies management experience. Other candidates fail to meet one or more requirements.

### Round 1

Majority: `D`; size: `3`; consensus: `True`

- **A1** answer=`D`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Drew (D) is the only candidate who meets all the requirements: has background knowledge in the domain, has completed the prerequisite training, has no scheduling conflict, and has coordinated project work before, which indicates they have handled management responsibilities.

- **A2** answer=`D`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate D satisfies all the requirements: has background knowledge in the domain, has completed the prerequisite training, has no scheduling conflict, and has coordinated project work before, which implies they have handled management responsibilities. Other candidates fail to meet one or more requirements.

- **A3** answer=`D`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Drew (D) satisfies all the requirements: has background knowledge in the domain, completed the prerequisite training, has no scheduling conflict, and has coordinated project work before, which implies management experience. Other candidates fail to meet one or more requirements.

### Round 2

Majority: `D`; size: `3`; consensus: `True`

- **A1** answer=`D`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Drew (D) is the only candidate who meets all the requirements: has handled management responsibilities (coordinated project work before), has completed the prerequisite training, has background knowledge in the domain, and has no scheduling conflict.

- **A2** answer=`D`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Drew (D) meets all the requirements: has background knowledge in the domain, has completed the prerequisite training, has no scheduling conflict, and has coordinated project work before, which indicates they have handled management responsibilities. Other candidates fail to meet one or more requirements.

- **A3** answer=`D`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Drew (D) meets all the requirements: has background knowledge in the domain, has completed the prerequisite training, has no scheduling conflict, and has coordinated project work before, which implies management experience. Other candidates fail to meet one or more requirements.

### Detected Objective Transitions

- A1 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A1 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

## attr_en_000070_original / qwen

- Pilot group: `stable_control`
- Gold: `C`

### Original Constraints

- C1 (has_client_communication_experience=True): Candidates must have experience communicating with clients.
- C2 (has_public_speaking_experience=True): Public speaking experience is required.
- C3 (has_ml_experience=True): Applicants must have experience working with machine learning systems.
- C4 (has_quality_assurance_experience=True): Candidates must have experience with quality control work.
- C5 (has_local_work_permit=True): Candidates must have valid local work authorization.

### Round 0

Majority: `C`; size: `3`; consensus: `True`

- **A1** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C meets all the requirements: experience communicating with clients, public speaking experience, machine learning systems experience, quality control work experience, and valid local work authorization.

- **A2** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C meets all the requirements: experience communicating with clients, public speaking experience, machine learning systems experience, quality control work experience, and valid local work authorization.

- **A3** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C meets all the requirements: experience communicating with clients, public speaking experience, machine learning systems experience, quality control work experience, and valid local work authorization.

### Round 1

Majority: `C`; size: `3`; consensus: `True`

- **A1** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C meets all the requirements: experience communicating with clients, public speaking experience, machine learning systems experience, quality control work experience, and valid local work authorization.

- **A2** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C meets all the requirements: experience communicating with clients, public speaking experience, machine learning systems experience, quality control work experience, and valid local work authorization.

- **A3** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C meets all the requirements: experience communicating with clients, public speaking experience, machine learning systems experience, quality control work experience, and valid local work authorization.

### Round 2

Majority: `C`; size: `3`; consensus: `True`

- **A1** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C meets all the requirements: experience communicating with clients, public speaking experience, machine learning systems experience, quality control work experience, and valid local work authorization.

- **A2** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C meets all the requirements: experience communicating with clients, public speaking experience, machine learning systems experience, quality control work experience, and valid local work authorization.

- **A3** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C meets all the requirements: experience communicating with clients, public speaking experience, machine learning systems experience, quality control work experience, and valid local work authorization.

### Detected Objective Transitions

- A1 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A1 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

## attr_en_000051_original / qwen

- Pilot group: `stable_control`
- Gold: `A`

### Original Constraints

- C1 (available_next_month=True): Only candidates who can join next month are eligible.
- C2 (needs_supervision=False): The candidate must be able to work without additional supervision.
- C3 (requires_extra_equipment=False): The candidate must not require additional specialized equipment.

### Round 0

Majority: `A`; size: `3`; consensus: `True`

- **A1** answer=`A`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate A satisfies all the requirements: they can join next month, can work without additional supervision, and do not require additional specialized equipment.

- **A2** answer=`A`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate A satisfies all the requirements: can join next month, works without additional supervision, and does not require specialized equipment.

- **A3** answer=`A`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate A satisfies all the requirements: they can join next month, can work without additional supervision, and do not require additional specialized equipment.

### Round 1

Majority: `A`; size: `3`; consensus: `True`

- **A1** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A meets all the requirements: they can join next month, can work without additional supervision, and do not require additional specialized equipment.

- **A2** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A satisfies all the requirements: they can join next month, can work without additional supervision, and do not require additional specialized equipment.

- **A3** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A meets all the requirements: they can join next month, can work without additional supervision, and do not require additional specialized equipment.

### Round 2

Majority: `A`; size: `3`; consensus: `True`

- **A1** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A meets all the requirements: they can join next month, can work without additional supervision, and do not require additional specialized equipment.

- **A2** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A satisfies all the requirements: they can join next month, can work without additional supervision, and do not require additional specialized equipment.

- **A3** answer=`A`, correct=`True`, confidence=`0.85`, violations=`[]`
  Reasoning: Candidate A meets all the requirements: they can join next month, can work without additional supervision, and do not require additional specialized equipment.

### Detected Objective Transitions

- A1 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A1 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`

## attr_en_000080_original / qwen

- Pilot group: `stable_control`
- Gold: `C`

### Original Constraints

- C1 (has_management_experience=True): Prior management experience is required.
- C2 (has_teamwork_experience=True): Candidates must have experience collaborating with a team.
- C3 (accepts_flexible_hours=True): Only candidates who can adapt to flexible scheduling are eligible.
- C4 (has_public_speaking_experience=True): Only candidates with prior public presentation experience are eligible.

### Round 0

Majority: `C`; size: `3`; consensus: `True`

- **A1** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C satisfies all the requirements: prior management experience, experience collaborating with a team, ability to adapt to flexible scheduling, and prior public presentation experience.

- **A2** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C has prior management experience, can adapt to flexible scheduling, has experience collaborating with a team, and has prior public presentation experience, satisfying all requirements.

- **A3** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C satisfies all the requirements: prior management experience, experience collaborating with a team, ability to adapt to flexible scheduling, and prior public presentation experience.

### Round 1

Majority: `C`; size: `3`; consensus: `True`

- **A1** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C meets all the requirements: prior management experience, experience collaborating with a team, ability to adapt to flexible scheduling, and prior public presentation experience.

- **A2** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C satisfies all the requirements: prior management experience, experience collaborating with a team, ability to adapt to flexible scheduling, and prior public presentation experience.

- **A3** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C satisfies all the requirements: prior management experience, experience collaborating with a team, ability to adapt to flexible scheduling, and prior public presentation experience.

### Round 2

Majority: `C`; size: `3`; consensus: `True`

- **A1** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C satisfies all the requirements: prior management experience, experience collaborating with a team, ability to adapt to flexible scheduling, and prior public presentation experience.

- **A2** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C satisfies all the requirements: prior management experience, experience collaborating with a team, ability to adapt to flexible scheduling, and prior public presentation experience.

- **A3** answer=`C`, correct=`True`, confidence=`0.95`, violations=`[]`
  Reasoning: Candidate C meets all the requirements: prior management experience, experience collaborating with a team, ability to adapt to flexible scheduling, and prior public presentation experience.

### Detected Objective Transitions

- A1 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R0→R1: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A1 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A2 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
- A3 R1→R2: `correct_to_correct`, changed=`False`, introduced=`[]`, resolved=`[]`, adopted_peer_answer=`False`
