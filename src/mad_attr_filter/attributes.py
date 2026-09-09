"""English-first boolean attribute pool with strict polarity metadata."""

from __future__ import annotations

from mad_attr_filter.models import AttributeSpec

EXPERT_RECRUITMENT = "expert_recruitment"
PROJECT_ASSIGNMENT = "project_assignment"
AVAILABILITY_SELECTION = "availability_selection"
ALL_SCENARIOS = (EXPERT_RECRUITMENT, PROJECT_ASSIGNMENT, AVAILABILITY_SELECTION)
EXPERT_AND_PROJECT = (EXPERT_RECRUITMENT, PROJECT_ASSIGNMENT)
PROJECT_AND_AVAILABILITY = (PROJECT_ASSIGNMENT, AVAILABILITY_SELECTION)

NEGATIVE_ONLY_ATTRIBUTES: tuple[str, ...] = (
    "has_conflict",
    "exceeds_budget",
    "has_schedule_conflict",
    "needs_supervision",
    "requires_extra_equipment",
)

TIME_AVAILABILITY_ATTRIBUTES: tuple[str, ...] = (
    "available_monday",
    "available_tuesday",
    "available_morning",
    "available_afternoon",
    "available_weekend",
    "available_next_month",
)

FORBIDDEN_REQUIREMENTS: frozenset[tuple[str, bool]] = frozenset(
    {
        ("available_monday", False),
        ("available_tuesday", False),
        ("available_morning", False),
        ("available_afternoon", False),
        ("available_weekend", False),
        ("available_next_month", False),
        ("accepts_flexible_hours", False),
        ("willing_to_travel", False),
    }
)

DISABLED_CONSTRAINT_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "prefers_long_term_project",
        "prefers_on_site_work",
        "requires_remote",
    }
)

POSITIVE_ONLY_ATTRIBUTES: tuple[str, ...] = (
    "has_ml_experience",
    "has_programming_experience",
    "has_management_experience",
    "speaks_english",
    "has_certificate",
    "has_research_experience",
    "has_data_analysis_experience",
    "has_project_experience",
    "has_public_speaking_experience",
    "has_quality_assurance_experience",
    "has_domain_knowledge",
    "has_security_clearance",
    "has_teamwork_experience",
    "has_client_communication_experience",
    "familiar_with_statistics",
    "can_work_independently",
    "has_local_work_permit",
    "has_prior_training",
    "can_work_remote",
    "can_work_onsite",
)


def _spec(
    *,
    key: str,
    category: str,
    allowed_required_values: tuple[bool, ...],
    compatible_scenarios: tuple[str, ...],
    constraint_true_templates: tuple[str, ...],
    constraint_false_templates: tuple[str, ...],
    candidate_true_templates: tuple[str, ...],
    candidate_false_templates: tuple[str, ...],
    eligible_for_constraint_sampling: bool = True,
) -> AttributeSpec:
    if True in allowed_required_values and len(constraint_true_templates) < 3:
        raise ValueError(f"{key} needs at least three true constraint templates")
    if False in allowed_required_values and len(constraint_false_templates) < 3:
        raise ValueError(f"{key} needs at least three false constraint templates")
    if len(candidate_true_templates) < 3 or len(candidate_false_templates) < 3:
        raise ValueError(f"{key} needs at least three candidate templates for each value")
    return AttributeSpec(
        key=key,
        category=category,
        allowed_required_values=allowed_required_values,
        compatible_scenarios=compatible_scenarios,
        constraint_true_templates=constraint_true_templates,
        constraint_false_templates=constraint_false_templates,
        candidate_true_templates=candidate_true_templates,
        candidate_false_templates=candidate_false_templates,
        eligible_for_constraint_sampling=eligible_for_constraint_sampling,
    )


ATTRIBUTE_POOL: tuple[AttributeSpec, ...] = (
    _spec(
        key="has_ml_experience",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Previous machine learning experience is required.",
            "Applicants must have experience working with machine learning systems.",
            "Only candidates with hands-on machine learning experience are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has worked on machine learning projects",
            "{name} has hands-on experience with machine learning systems",
            "{name} has practical machine learning experience",
        ),
        candidate_false_templates=(
            "{name} has not worked with machine learning before",
            "{name} lacks practical machine learning experience",
            "{name} has no prior exposure to machine learning projects",
        ),
    ),
    _spec(
        key="has_programming_experience",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Programming experience is required.",
            "The selected candidate must have prior coding experience.",
            "Only candidates who have worked on software implementation are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has written code for previous projects",
            "{name} has practical programming experience",
            "{name} has handled software implementation work",
        ),
        candidate_false_templates=(
            "{name} has no practical programming background",
            "{name} has not handled coding tasks before",
            "{name} lacks software implementation experience",
        ),
    ),
    _spec(
        key="has_management_experience",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Prior management experience is required.",
            "The role requires experience coordinating people or projects.",
            "Candidates must have handled management responsibilities before.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has coordinated project work before",
            "{name} has experience managing team activities",
            "{name} has previously handled management responsibilities",
        ),
        candidate_false_templates=(
            "{name} has not managed a team or project before",
            "{name} lacks experience coordinating project work",
            "{name} has no record of management responsibilities",
        ),
    ),
    _spec(
        key="speaks_english",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "The candidate must be able to communicate in English.",
            "English communication ability is required.",
            "Only candidates who can work in English are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} can communicate in English for work",
            "{name} is able to handle English-language communication",
            "{name} can participate in English discussions",
        ),
        candidate_false_templates=(
            "{name} cannot communicate in English for work",
            "{name} is not able to handle English-language communication",
            "{name} cannot participate effectively in English discussions",
        ),
    ),
    _spec(
        key="has_certificate",
        category="qualification",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "A relevant certificate is required.",
            "Candidates must hold the required professional certification.",
            "Only applicants with a valid relevant certificate are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} holds a relevant professional certificate",
            "{name} has the required certification",
            "{name} has valid certificate documentation",
        ),
        candidate_false_templates=(
            "{name} does not hold a relevant certificate",
            "{name} lacks the required certification",
            "{name} has no valid certificate documentation",
        ),
    ),
    _spec(
        key="has_research_experience",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Research experience is required.",
            "Candidates must have participated in research work before.",
            "Only candidates with prior research project experience are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has participated in research projects",
            "{name} has prior experience with research work",
            "{name} is familiar with research project workflows",
        ),
        candidate_false_templates=(
            "{name} has not participated in research projects",
            "{name} lacks prior research work experience",
            "{name} is not familiar with research project workflows",
        ),
    ),
    _spec(
        key="has_data_analysis_experience",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Data analysis experience is required.",
            "The selected candidate must have analyzed data in prior work.",
            "Only candidates with practical data analysis experience are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has performed data analysis in previous work",
            "{name} has practical experience analyzing datasets",
            "{name} has handled data analysis tasks before",
        ),
        candidate_false_templates=(
            "{name} has not performed data analysis before",
            "{name} lacks practical experience analyzing datasets",
            "{name} has no prior data analysis background",
        ),
    ),
    _spec(
        key="has_project_experience",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Prior project experience is required.",
            "Candidates must have participated in project work before.",
            "Only candidates with experience in project execution are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has participated in completed project work",
            "{name} has experience contributing to project delivery",
            "{name} is familiar with project execution",
        ),
        candidate_false_templates=(
            "{name} has not participated in project work before",
            "{name} lacks project delivery experience",
            "{name} is not familiar with project execution",
        ),
    ),
    _spec(
        key="available_monday",
        category="availability",
        allowed_required_values=(True,),
        compatible_scenarios=ALL_SCENARIOS,
        constraint_true_templates=(
            "The selected candidate must be available on Monday.",
            "Monday availability is required.",
            "Only candidates who can participate on Monday are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} can participate on Monday",
            "{name} is available for Monday work",
            "{name} can join the project on Monday",
        ),
        candidate_false_templates=(
            "{name} is unavailable on Monday",
            "{name} cannot participate on Monday",
            "{name} cannot join project work on Monday",
        ),
    ),
    _spec(
        key="available_tuesday",
        category="availability",
        allowed_required_values=(True,),
        compatible_scenarios=ALL_SCENARIOS,
        constraint_true_templates=(
            "The selected candidate must be available on Tuesday.",
            "Tuesday availability is required.",
            "Only candidates who can participate on Tuesday are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} can participate on Tuesday",
            "{name} is available for Tuesday work",
            "{name} can join the project on Tuesday",
        ),
        candidate_false_templates=(
            "{name} is unavailable on Tuesday",
            "{name} cannot participate on Tuesday",
            "{name} cannot join project work on Tuesday",
        ),
    ),
    _spec(
        key="available_morning",
        category="availability",
        allowed_required_values=(True,),
        compatible_scenarios=ALL_SCENARIOS,
        constraint_true_templates=(
            "Morning availability is required.",
            "The selected candidate must be available in the morning.",
            "Only candidates who can participate during the morning are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} is available in the morning",
            "{name} can participate during the morning",
            "{name} can work in the morning time slot",
        ),
        candidate_false_templates=(
            "{name} is unavailable in the morning",
            "{name} cannot participate during the morning",
            "{name} cannot work in the morning time slot",
        ),
    ),
    _spec(
        key="available_afternoon",
        category="availability",
        allowed_required_values=(True,),
        compatible_scenarios=ALL_SCENARIOS,
        constraint_true_templates=(
            "Afternoon availability is required.",
            "The selected candidate must be available in the afternoon.",
            "Only candidates who can participate during the afternoon are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} is available in the afternoon",
            "{name} can participate during the afternoon",
            "{name} can work in the afternoon time slot",
        ),
        candidate_false_templates=(
            "{name} is unavailable in the afternoon",
            "{name} cannot participate during the afternoon",
            "{name} cannot work in the afternoon time slot",
        ),
    ),
    _spec(
        key="available_weekend",
        category="availability",
        allowed_required_values=(True,),
        compatible_scenarios=PROJECT_AND_AVAILABILITY,
        constraint_true_templates=(
            "Weekend availability is required.",
            "The selected candidate must be able to participate on the weekend.",
            "Only candidates who can work during the weekend are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} can participate on the weekend",
            "{name} is available for weekend work",
            "{name} can join weekend project activities",
        ),
        candidate_false_templates=(
            "{name} is unavailable on the weekend",
            "{name} cannot participate in weekend work",
            "{name} cannot join weekend project activities",
        ),
    ),
    _spec(
        key="available_next_month",
        category="availability",
        allowed_required_values=(True,),
        compatible_scenarios=ALL_SCENARIOS,
        constraint_true_templates=(
            "The selected candidate must be available next month.",
            "Availability next month is required.",
            "Only candidates who can join next month are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} can join the project next month",
            "{name} is available next month",
            "{name} can start participating next month",
        ),
        candidate_false_templates=(
            "{name} cannot join the project next month",
            "{name} is unavailable next month",
            "{name} cannot start participating next month",
        ),
    ),
    _spec(
        key="has_conflict",
        category="restriction",
        allowed_required_values=(False,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(),
        constraint_false_templates=(
            "The selected candidate must have no conflict of interest.",
            "Anyone with a conflict of interest is ineligible.",
            "Candidates must be free of conflicts related to the project.",
        ),
        candidate_true_templates=(
            "{name} has a conflict of interest related to the project",
            "{name} would need to be recused because of a conflict",
            "{name} has an interest conflict affecting this project",
        ),
        candidate_false_templates=(
            "{name} has no conflict of interest related to the project",
            "{name} has no project-related conflict requiring recusal",
            "{name} is free of conflicts for this project",
        ),
    ),
    _spec(
        key="requires_remote",
        category="preference",
        allowed_required_values=(True, False),
        compatible_scenarios=PROJECT_AND_AVAILABILITY,
        constraint_true_templates=("Remote-only participation would be required.",) * 3,
        constraint_false_templates=("Remote-only participation would not be required.",) * 3,
        candidate_true_templates=(
            "{name} would require a remote-only arrangement",
            "{name} can participate only through remote work",
            "{name} cannot accept non-remote participation",
        ),
        candidate_false_templates=(
            "{name} does not require a remote-only arrangement",
            "{name} can participate without remote-only conditions",
            "{name} can accept non-remote participation",
        ),
        eligible_for_constraint_sampling=False,
    ),
    _spec(
        key="can_work_remote",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=PROJECT_AND_AVAILABILITY,
        constraint_true_templates=(
            "The candidate must be able to work remotely.",
            "Remote work capability is required.",
            "Only candidates who can participate remotely are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} can work remotely",
            "{name} is able to participate through remote work",
            "{name} has the setup needed for remote collaboration",
        ),
        candidate_false_templates=(
            "{name} cannot work remotely",
            "{name} is not able to participate through remote work",
            "{name} lacks the setup needed for remote collaboration",
        ),
    ),
    _spec(
        key="can_work_onsite",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=PROJECT_AND_AVAILABILITY,
        constraint_true_templates=(
            "The candidate must be available for on-site work.",
            "On-site work capability is required.",
            "Only candidates who can participate on site are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} can participate on site",
            "{name} is available for on-site work",
            "{name} can work at the project location",
        ),
        candidate_false_templates=(
            "{name} cannot participate on site",
            "{name} is not available for on-site work",
            "{name} cannot work at the project location",
        ),
    ),
    _spec(
        key="exceeds_budget",
        category="restriction",
        allowed_required_values=(False,),
        compatible_scenarios=(PROJECT_ASSIGNMENT,),
        constraint_true_templates=(),
        constraint_false_templates=(
            "The candidate's participation must remain within budget.",
            "Candidates whose costs exceed the project budget are ineligible.",
            "The assignment must fit within the available budget.",
        ),
        candidate_true_templates=(
            "{name}'s expected cost exceeds the project budget",
            "{name}'s participation would go beyond the budget limit",
            "{name} would require funding above the available budget",
        ),
        candidate_false_templates=(
            "{name}'s expected cost fits within the project budget",
            "{name}'s participation stays within the budget limit",
            "{name} can be supported by the available budget",
        ),
    ),
    _spec(
        key="needs_supervision",
        category="restriction",
        allowed_required_values=(False,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(),
        constraint_false_templates=(
            "The candidate must be able to work without additional supervision.",
            "Additional supervision must not be required.",
            "Only candidates who can work independently without extra oversight are eligible.",
        ),
        candidate_true_templates=(
            "{name} would need additional supervision to complete the work",
            "{name} requires extra oversight for this role",
            "{name} cannot carry out the work without additional supervision",
        ),
        candidate_false_templates=(
            "{name} can complete the work without additional supervision",
            "{name} does not require extra oversight for this role",
            "{name} can carry out the work independently",
        ),
    ),
    _spec(
        key="has_schedule_conflict",
        category="restriction",
        allowed_required_values=(False,),
        compatible_scenarios=ALL_SCENARIOS,
        constraint_true_templates=(),
        constraint_false_templates=(
            "The candidate must have no scheduling conflict.",
            "Candidates with a scheduling conflict are ineligible.",
            "The selected candidate must have a schedule that does not conflict with the project.",
        ),
        candidate_true_templates=(
            "{name} has a scheduling conflict with the project",
            "{name}'s current schedule conflicts with the required timing",
            "{name} cannot avoid a schedule conflict for this role",
        ),
        candidate_false_templates=(
            "{name} has no scheduling conflict with the project",
            "{name}'s schedule fits the required timing",
            "{name} can avoid schedule conflicts for this role",
        ),
    ),
    _spec(
        key="requires_extra_equipment",
        category="restriction",
        allowed_required_values=(False,),
        compatible_scenarios=PROJECT_AND_AVAILABILITY,
        constraint_true_templates=(),
        constraint_false_templates=(
            "The candidate must not require additional specialized equipment.",
            "Candidates who need extra equipment support are ineligible.",
            "The selected candidate must be able to participate without additional equipment.",
        ),
        candidate_true_templates=(
            "{name} would require additional specialized equipment",
            "{name} needs extra equipment support to participate",
            "{name} cannot participate without additional equipment",
        ),
        candidate_false_templates=(
            "{name} can participate without additional specialized equipment",
            "{name} does not need extra equipment support",
            "{name} can work with the equipment already available",
        ),
    ),
    _spec(
        key="has_domain_knowledge",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Relevant domain knowledge is required.",
            "Candidates must understand the project domain.",
            "Only candidates with sufficient domain knowledge are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} understands the relevant project domain",
            "{name} has background knowledge in the domain",
            "{name} is familiar with the domain needed for the work",
        ),
        candidate_false_templates=(
            "{name} does not understand the relevant project domain",
            "{name} lacks background knowledge in the domain",
            "{name} is not familiar with the domain needed for the work",
        ),
    ),
    _spec(
        key="has_teamwork_experience",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Teamwork experience is required.",
            "Candidates must have experience collaborating with a team.",
            "Only candidates with prior team collaboration experience are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has collaborated on team projects",
            "{name} has experience working with project teams",
            "{name} has handled collaborative team tasks",
        ),
        candidate_false_templates=(
            "{name} has not collaborated on team projects",
            "{name} lacks experience working with project teams",
            "{name} has no background in collaborative team tasks",
        ),
    ),
    _spec(
        key="has_client_communication_experience",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Client communication experience is required.",
            "Candidates must have experience communicating with clients.",
            "Only candidates who have handled client-facing communication are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has communicated directly with clients",
            "{name} has handled client-facing discussions",
            "{name} has practical client communication experience",
        ),
        candidate_false_templates=(
            "{name} has not communicated directly with clients",
            "{name} lacks client-facing communication experience",
            "{name} has no practical background in client communication",
        ),
    ),
    _spec(
        key="prefers_long_term_project",
        category="preference",
        allowed_required_values=(True, False),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=("A long-term project preference would be considered.",) * 3,
        constraint_false_templates=("A short-term project preference would be considered.",) * 3,
        candidate_true_templates=(
            "{name} prefers long-term projects",
            "{name} is more comfortable with extended project timelines",
            "{name} has a preference for sustained project work",
        ),
        candidate_false_templates=(
            "{name} prefers shorter project commitments",
            "{name} is not looking for a long-term project",
            "{name} is more comfortable with short-term assignments",
        ),
        eligible_for_constraint_sampling=False,
    ),
    _spec(
        key="willing_to_travel",
        category="preference",
        allowed_required_values=(True,),
        compatible_scenarios=(PROJECT_ASSIGNMENT,),
        constraint_true_templates=(
            "The candidate must be willing to travel.",
            "Travel availability is required for this assignment.",
            "Only candidates who can travel for the project are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} can travel for the project",
            "{name} is willing to travel if the assignment requires it",
            "{name} can support project-related travel",
        ),
        candidate_false_templates=(
            "{name} cannot travel for the project",
            "{name} is not willing to travel for this assignment",
            "{name} cannot support project-related travel",
        ),
    ),
    _spec(
        key="accepts_flexible_hours",
        category="preference",
        allowed_required_values=(True,),
        compatible_scenarios=PROJECT_AND_AVAILABILITY,
        constraint_true_templates=(
            "The candidate must be able to work flexible hours.",
            "Flexible-hour availability is required.",
            "Only candidates who can adapt to flexible scheduling are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} can work flexible hours",
            "{name} can adapt to flexible scheduling",
            "{name} is able to handle variable work hours",
        ),
        candidate_false_templates=(
            "{name} cannot work flexible hours",
            "{name} cannot adapt to flexible scheduling",
            "{name} is not able to handle variable work hours",
        ),
    ),
    _spec(
        key="has_security_clearance",
        category="qualification",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Security clearance is required.",
            "Candidates must have the required security clearance.",
            "Only candidates with valid security clearance are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has valid security clearance",
            "{name} meets the security clearance requirement",
            "{name} has the required security authorization",
        ),
        candidate_false_templates=(
            "{name} does not have valid security clearance",
            "{name} does not meet the security clearance requirement",
            "{name} lacks the required security authorization",
        ),
    ),
    _spec(
        key="has_prior_training",
        category="qualification",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Prior training is required.",
            "Candidates must have completed the prerequisite training.",
            "Only candidates with the required prior training are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has completed the prerequisite training",
            "{name} has the required training background",
            "{name} meets the prior training requirement",
        ),
        candidate_false_templates=(
            "{name} has not completed the prerequisite training",
            "{name} lacks the required training background",
            "{name} does not meet the prior training requirement",
        ),
    ),
    _spec(
        key="has_local_work_permit",
        category="qualification",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "A local work permit is required.",
            "Candidates must have valid local work authorization.",
            "Only candidates with a local work permit are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has a valid local work permit",
            "{name} has local work authorization",
            "{name} meets the local work permit requirement",
        ),
        candidate_false_templates=(
            "{name} does not have a valid local work permit",
            "{name} lacks local work authorization",
            "{name} does not meet the local work permit requirement",
        ),
    ),
    _spec(
        key="can_work_independently",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "The candidate must be able to work independently.",
            "Independent work ability is required.",
            "Only candidates who can complete tasks independently are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} can complete tasks independently",
            "{name} can work without close guidance",
            "{name} is able to make progress independently",
        ),
        candidate_false_templates=(
            "{name} cannot complete tasks independently",
            "{name} needs close guidance to work",
            "{name} is not able to make progress independently",
        ),
    ),
    _spec(
        key="has_public_speaking_experience",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Public speaking experience is required.",
            "Candidates must have experience presenting to an audience.",
            "Only candidates with prior public presentation experience are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has given public presentations before",
            "{name} has experience speaking to an audience",
            "{name} has handled formal presentation duties",
        ),
        candidate_false_templates=(
            "{name} has not given public presentations before",
            "{name} lacks experience speaking to an audience",
            "{name} has no background in formal presentation duties",
        ),
    ),
    _spec(
        key="familiar_with_statistics",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Familiarity with statistics is required.",
            "Candidates must understand common statistical methods.",
            "Only candidates with a statistics background are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} understands common statistical methods",
            "{name} has a solid statistics background",
            "{name} can work with statistical analysis tasks",
        ),
        candidate_false_templates=(
            "{name} does not understand common statistical methods",
            "{name} lacks a statistics background",
            "{name} cannot handle statistical analysis tasks",
        ),
    ),
    _spec(
        key="has_quality_assurance_experience",
        category="ability",
        allowed_required_values=(True,),
        compatible_scenarios=EXPERT_AND_PROJECT,
        constraint_true_templates=(
            "Quality assurance experience is required.",
            "Candidates must have experience with quality control work.",
            "Only candidates with prior quality assurance experience are eligible.",
        ),
        constraint_false_templates=(),
        candidate_true_templates=(
            "{name} has worked on quality assurance tasks",
            "{name} has experience with quality control processes",
            "{name} has handled quality review work before",
        ),
        candidate_false_templates=(
            "{name} has not worked on quality assurance tasks",
            "{name} lacks experience with quality control processes",
            "{name} has no background in quality review work",
        ),
    ),
    _spec(
        key="prefers_on_site_work",
        category="preference",
        allowed_required_values=(True, False),
        compatible_scenarios=PROJECT_AND_AVAILABILITY,
        constraint_true_templates=("An on-site work preference would be considered.",) * 3,
        constraint_false_templates=("A non-on-site work preference would be considered.",) * 3,
        candidate_true_templates=(
            "{name} prefers on-site work",
            "{name} is more comfortable working at the project location",
            "{name} has a preference for in-person project work",
        ),
        candidate_false_templates=(
            "{name} does not prefer on-site work",
            "{name} is more comfortable away from the project location",
            "{name} has a preference for non-on-site project work",
        ),
        eligible_for_constraint_sampling=False,
    ),
)

ATTRIBUTE_BY_KEY: dict[str, AttributeSpec] = {attribute.key: attribute for attribute in ATTRIBUTE_POOL}


def attribute_constraint_templates(attribute_key: str, value: bool) -> tuple[str, ...]:
    """Return English constraint templates for an attribute value."""
    try:
        attribute = ATTRIBUTE_BY_KEY[attribute_key]
    except KeyError as exc:
        raise KeyError(f"Unknown attribute key: {attribute_key}") from exc
    return attribute.constraint_true_templates if value else attribute.constraint_false_templates


def attribute_display_templates(attribute_key: str, value: bool) -> tuple[str, ...]:
    """Return English candidate-display templates for an attribute value."""
    try:
        attribute = ATTRIBUTE_BY_KEY[attribute_key]
    except KeyError as exc:
        raise KeyError(f"Unknown attribute key: {attribute_key}") from exc
    return attribute.candidate_true_templates if value else attribute.candidate_false_templates


def is_attribute_compatible_with_scenario(attribute: AttributeSpec, scenario_key: str) -> bool:
    """Return whether an attribute can appear under a scenario."""
    return scenario_key in attribute.compatible_scenarios


def serialized_attribute_pool() -> list[dict[str, object]]:
    """Return the full attribute pool as JSON-ready dictionaries."""
    return [attribute.to_dict() for attribute in ATTRIBUTE_POOL]

