from __future__ import annotations

from collections import Counter

from mad_attr_filter.attributes import (
    ATTRIBUTE_POOL,
    ATTRIBUTE_BY_KEY,
    DISABLED_CONSTRAINT_ATTRIBUTES,
    FORBIDDEN_REQUIREMENTS,
    NEGATIVE_ONLY_ATTRIBUTES,
    POSITIVE_ONLY_ATTRIBUTES,
    TIME_AVAILABILITY_ATTRIBUTES,
    attribute_constraint_templates,
    attribute_display_templates,
)
from mad_attr_filter.generator import generate_dataset, generate_item
from mad_attr_filter.io import read_jsonl, write_jsonl
from mad_attr_filter.matrix import compute_constraint_matrix, compute_violation_signatures
from mad_attr_filter.mad_analysis import build_transition_event, majority_summary
from mad_attr_filter.mad_pilot import (
    build_debate_prompt,
    build_mad_response_record,
    build_round_zero_prompt,
    select_mad_pilot_manifest,
)
from mad_attr_filter.scenarios import is_allowed_by_scenario
from mad_attr_filter.semantic_validator import collect_strict_semantic_audit, sample_chinese_character_count, validate_semantics
from mad_attr_filter.single_agent import build_output_record, build_prompt, parse_model_response
from mad_attr_filter.single_agent_analysis import (
    build_constraint_error_statistics,
    build_empirical_dataset,
    build_item_analysis,
    build_statistics_payload,
    select_candidate_items,
)
from mad_attr_filter.validation import validate_dataset, validate_sample


def _wrong_violation_counts(sample: dict) -> list[int]:
    gold = sample["gold_answer"]
    return sorted(
        len(signature)
        for label, signature in sample["option_violation_signature"].items()
        if label != gold
    )


def test_english_pilot_items_use_english_language_and_text() -> None:
    samples, _ = generate_dataset({"easy": 4, "medium": 8, "hard": 4}, global_seed=100)
    for sample in samples:
        assert sample["language"] == "en"
        assert sample["generator_version"] == "3.0-en"
        assert sample["item_id"].startswith("attr_en_")
        assert sample_chinese_character_count(sample) == 0
        assert sample["question"].strip()
        assert all(option.strip() for option in sample["options"].values())


def test_all_formal_values_have_english_realizations() -> None:
    for attribute in ATTRIBUTE_POOL:
        for value in attribute.allowed_required_values:
            if attribute.eligible_for_constraint_sampling:
                assert attribute_constraint_templates(attribute.key, value)
        assert attribute_display_templates(attribute.key, True)
        assert attribute_display_templates(attribute.key, False)


def test_negative_restrictions_are_never_required_true() -> None:
    samples, _ = generate_dataset({"easy": 20, "medium": 60, "hard": 20}, global_seed=101)
    for sample in samples:
        for constraint in sample["constraints"]:
            if constraint["attribute"] in {"has_conflict", "exceeds_budget", "has_schedule_conflict"}:
                assert constraint["required_value"] is False
            if constraint["attribute"] in NEGATIVE_ONLY_ATTRIBUTES:
                assert constraint["required_value"] is False


def test_v3_strict_positive_availability_and_work_mode_requirements() -> None:
    samples, _ = generate_dataset({"easy": 20, "medium": 60, "hard": 20}, global_seed=303)
    for sample in samples:
        for constraint in sample["constraints"]:
            attribute = constraint["attribute"]
            if attribute in TIME_AVAILABILITY_ATTRIBUTES:
                assert constraint["required_value"] is True
            if attribute in {"accepts_flexible_hours", "willing_to_travel"}:
                assert constraint["required_value"] is True
            if attribute in {"can_work_remote", "can_work_onsite"}:
                assert constraint["required_value"] is True
            assert (attribute, constraint["required_value"]) not in FORBIDDEN_REQUIREMENTS


def test_v3_disabled_attributes_never_enter_constraints() -> None:
    samples, _ = generate_dataset({"easy": 20, "medium": 60, "hard": 20}, global_seed=304)
    constrained_attributes = {
        constraint["attribute"]
        for sample in samples
        for constraint in sample["constraints"]
    }
    assert "prefers_long_term_project" not in constrained_attributes
    assert "prefers_on_site_work" not in constrained_attributes
    assert "requires_remote" not in constrained_attributes
    assert constrained_attributes.isdisjoint(DISABLED_CONSTRAINT_ATTRIBUTES)


def test_positive_ability_attributes_are_never_required_false() -> None:
    samples, _ = generate_dataset({"easy": 20, "medium": 60, "hard": 20}, global_seed=102)
    for sample in samples:
        for constraint in sample["constraints"]:
            if constraint["attribute"] in POSITIVE_ONLY_ATTRIBUTES:
                assert constraint["required_value"] is True


def test_all_constraints_are_compatible_with_current_scenario() -> None:
    sample = generate_item(1, "medium", 123, gold_label="C", num_constraints=4, scenario_key="project_assignment")
    for constraint in sample["constraints"]:
        attribute = ATTRIBUTE_BY_KEY[constraint["attribute"]]
        assert sample["scenario"] in attribute.compatible_scenarios
        assert is_allowed_by_scenario(attribute.key, attribute.category, sample["scenario"])


def test_constraint_natural_language_matches_required_value() -> None:
    sample = generate_item(1, "easy", 456, gold_label="A", num_constraints=5, scenario_key="expert_recruitment")
    for constraint in sample["constraints"]:
        assert constraint["natural_language"] in attribute_constraint_templates(
            constraint["attribute"], constraint["required_value"]
        )


def test_candidate_text_matches_structured_attributes() -> None:
    sample = generate_item(1, "hard", 789, gold_label="D", num_constraints=3, scenario_key="availability_selection")
    validate_semantics(sample)
    for label, entity in sample["entities"].items():
        option_text = sample["options"][label]
        for fact in entity["displayed_facts"]:
            attribute_key = fact["attribute"]
            value = entity["attributes"][attribute_key]
            assert fact["value"] == value
            allowed = {
                template.format(name=entity["name"]) for template in attribute_display_templates(attribute_key, value)
            }
            assert fact["text"] in allowed
            assert fact["text"] in option_text


def test_candidate_attribute_display_order_is_not_constraint_order() -> None:
    sample = generate_item(1, "medium", 987, gold_label="B", num_constraints=4, scenario_key="project_assignment")
    constraint_order = [constraint["attribute"] for constraint in sample["constraints"]]
    for entity in sample["entities"].values():
        assert entity["display_order"] != constraint_order
        assert set(entity["display_order"]) == set(constraint_order)


def test_option_closeness_patterns_match_definition() -> None:
    cases = [("easy", 11, 5), ("medium", 12, 4), ("hard", 13, 3)]
    for option_closeness, seed, num_constraints in cases:
        sample = generate_item(1, option_closeness, seed, gold_label="B", num_constraints=num_constraints)
        counts = _wrong_violation_counts(sample)
        if option_closeness == "easy":
            assert counts[0] == 2 and counts[1] == 2
        elif option_closeness == "medium":
            assert counts == [1, 1, 2]
        else:
            assert counts == [1, 1, 1]


def test_structural_complexity_matches_constraint_count() -> None:
    expected = {3: "low", 4: "medium", 5: "high"}
    for num_constraints, complexity in expected.items():
        option_closeness = "easy" if num_constraints == 5 else "medium"
        sample = generate_item(1, option_closeness, 200 + num_constraints, num_constraints=num_constraints)
        assert sample["structural_complexity"] == complexity
        assert sample["metadata"]["num_constraints"] == num_constraints


def test_gold_is_unique_and_labels_remain_correct_after_randomization() -> None:
    for label in ("A", "B", "C", "D"):
        sample = generate_item(1, "medium", 900 + ord(label), gold_label=label, num_constraints=4)
        assert sample["gold_answer"] == label
        assert sample["entities"][label]["is_gold"] is True
        valid_labels = [option for option, signature in sample["option_violation_signature"].items() if not signature]
        assert valid_labels == [label]
        validate_sample(sample)


def test_constraint_matrix_and_violation_signatures_are_accurate() -> None:
    sample = generate_item(1, "easy", 321, gold_label="A", num_constraints=5)
    candidate_attributes = {
        label: entity["attributes"] for label, entity in sample["entities"].items()
    }
    constraints = [
        type("ConstraintLike", (), constraint)()
        for constraint in sample["constraints"]
    ]
    matrix = compute_constraint_matrix(candidate_attributes, constraints)
    signatures = compute_violation_signatures(matrix)
    assert matrix == sample["option_constraint_matrix"]
    assert signatures == sample["option_violation_signature"]


def test_fixed_seed_reproduces_same_dataset() -> None:
    counts = {"easy": 2, "medium": 4, "hard": 2}
    first, first_report = generate_dataset(counts, global_seed=2024)
    second, second_report = generate_dataset(counts, global_seed=2024)
    assert first == second
    assert first_report.to_dict() == second_report.to_dict()


def test_jsonl_serialization_roundtrip(tmp_path) -> None:
    samples, _ = generate_dataset({"easy": 1, "medium": 2, "hard": 1}, global_seed=7)
    path = tmp_path / "roundtrip.jsonl"
    write_jsonl(path, samples)
    loaded = read_jsonl(path)
    assert loaded == samples
    validate_dataset(loaded)


def test_batch_generate_1000_valid_samples_without_semantic_violations() -> None:
    samples, report = generate_dataset({"easy": 200, "medium": 600, "hard": 200}, global_seed=99)
    assert len(samples) == 1000
    validate_dataset(samples)
    for sample in samples:
        validate_semantics(sample)
    assert report.generated_items == 1000
    assert report.semantic_validation_failures == 0
    assert report.invalid_polarity_failures == 0
    assert report.scenario_compatibility_failures == 0
    assert Counter(sample["option_closeness"] for sample in samples) == {"easy": 200, "medium": 600, "hard": 200}
    assert all(sample["language"] == "en" for sample in samples)
    audit = collect_strict_semantic_audit(samples)
    assert audit["forbidden_requirement_count"] == 0
    assert audit["disabled_attribute_count"] == 0
    assert audit["negative_availability_count"] == 0
    assert audit["negative_preference_count"] == 0
    assert audit["semantic_error_count"] == 0
    assert audit["semantic_validation_pass_rate"] == 1.0
    assert audit["chinese_character_count"] == 0


def test_single_agent_prompt_and_response_parser_are_english_and_strict() -> None:
    prompt = build_prompt("Which candidate satisfies all requirements?")
    assert "Solve the following multiple-choice problem independently." in prompt
    assert sample_chinese_character_count({"question": prompt, "options": {}}) == 0

    parsed = parse_model_response('{"answer": "Option B", "reasoning": "A fails; B works.", "confidence": 0.8}')
    assert parsed["parse_success"] is True
    assert parsed["strict_json_success"] is True
    assert parsed["answer"] == "B"
    assert parsed["confidence"] == 0.8

    fallback = parse_model_response("Answer: C")
    assert fallback["parse_success"] is False
    assert fallback["answer"] == "C"

    invalid_confidence = parse_model_response('{"answer": "A", "reasoning": "A works.", "confidence": 1.7}')
    assert invalid_confidence["parse_success"] is False
    assert invalid_confidence["answer"] == "A"


def test_single_agent_analysis_builds_stage_3b_artifacts() -> None:
    sample = generate_item(1, "hard", 4242, gold_label="A", num_constraints=3, scenario_key="project_assignment")
    wrong_label = next(label for label in ("B", "C", "D") if label != sample["gold_answer"])
    outputs = []
    run_plan = [
        ("qwen", 11, sample["gold_answer"]),
        ("qwen", 22, sample["gold_answer"]),
        ("qwen", 33, wrong_label),
        ("llama", 11, sample["gold_answer"]),
        ("llama", 22, wrong_label),
        ("llama", 33, wrong_label),
    ]
    for alias, seed, answer in run_plan:
        outputs.append(
            build_output_record(
                sample=sample,
                model_config={
                    "alias": alias,
                    "model_name": f"{alias}-local",
                    "base_url": "http://127.0.0.1:8000/v1",
                },
                run_id=(seed // 11),
                seed=seed,
                generation_config={"temperature": 0.7, "top_p": 0.9, "max_tokens": 512},
                raw_response=f'{{"answer": "{answer}", "reasoning": "A, B, C, and D were checked.", "confidence": 0.75}}',
                api_metadata={"usage": None},
                request_error=None,
            )
        )

    analyses = build_item_analysis([sample], outputs)
    candidates = select_candidate_items([sample], outputs, analyses)
    constraint_stats = build_constraint_error_statistics([sample], outputs, expected_runs_per_item=6)
    statistics = build_statistics_payload(
        [sample],
        outputs,
        analyses,
        candidates,
        constraint_stats,
        expected_model_aliases=("qwen", "llama"),
        expected_run_ids=(1, 2, 3),
    )
    empirical = build_empirical_dataset([sample], analyses)

    assert analyses[0]["num_runs"] == 6
    assert analyses[0]["num_correct"] == 3
    assert analyses[0]["has_cross_model_disagreement"] is True
    assert analyses[0]["has_within_model_disagreement"] is True
    assert analyses[0]["screening_category"] == "mixed_correctness"
    assert candidates[0]["mad_priority"] == "high"
    assert statistics["overall"]["expected_runs"] == 6
    assert statistics["overall"]["missing_run_count"] == 0
    assert constraint_stats["wrong_option_violation_count_distribution"]["1_constraint"] == 3
    assert empirical[0]["empirical_difficulty"] == "medium"
    assert empirical[0]["metadata"]["screening_category"] == "mixed_correctness"


def test_mad_manifest_keeps_vulnerable_items_and_stratifies_controls() -> None:
    candidates = []
    for index in range(3):
        candidates.append(
            {
                "item_id": f"v{index}",
                "screening_category": "mixed_correctness" if index < 2 else "mildly_vulnerable",
                "mad_priority": "high",
                "empirical_accuracy": 0.5,
                "observed_wrong_options": ["B"],
                "observed_wrong_violation_signatures": {"B": ["C1"]},
                "scenario": "project_assignment",
                "structural_complexity": "medium",
                "option_closeness": "hard",
                "num_constraints": 4,
            }
        )
    scenarios = ("expert_recruitment", "project_assignment", "availability_selection")
    complexities = ("low", "medium", "high")
    for index, (scenario, complexity) in enumerate(
        (scenario, complexity) for scenario in scenarios for complexity in complexities
    ):
        candidates.append(
            {
                "item_id": f"s{index}",
                "screening_category": "stable_correct",
                "mad_priority": "low",
                "empirical_accuracy": 1.0,
                "observed_wrong_options": [],
                "observed_wrong_violation_signatures": {},
                "scenario": scenario,
                "structural_complexity": complexity,
                "option_closeness": "easy",
                "num_constraints": {"low": 3, "medium": 4, "high": 5}[complexity],
            }
        )
    manifest = select_mad_pilot_manifest(candidates, stable_control_count=9, seed=12)
    assert len(manifest) == 12
    assert sum(record["pilot_group"] == "vulnerable" for record in manifest) == 3
    controls = [record for record in manifest if record["pilot_group"] == "stable_control"]
    assert {record["scenario"] for record in controls} == set(scenarios)
    assert {record["structural_complexity"] for record in controls} == set(complexities)


def test_mad_prompts_expose_peers_only_after_round_zero() -> None:
    round_zero = build_round_zero_prompt("Question body")
    assert "Question body" in round_zero
    assert "other agents" not in round_zero.lower()
    previous = {
        "A1": {"answer": "A", "reasoning": "A meets the conditions."},
        "A2": {"answer": "B", "reasoning": "B appears eligible."},
        "A3": {"answer": "A", "reasoning": "A passes each condition."},
    }
    debate, peers = build_debate_prompt("Question body", own_agent_id="A1", previous_round=previous)
    assert "Your previous answer:\nA" in debate
    assert "Agent A2:" in debate and "Agent A3:" in debate
    assert len(peers) == 2
    assert {peer["agent_id"] for peer in peers} == {"A2", "A3"}


def test_mad_response_and_transition_use_deterministic_violation_sets() -> None:
    sample = generate_item(1, "hard", 6060, gold_label="A", num_constraints=3)
    wrong_labels = [label for label in ("B", "C", "D") if label != sample["gold_answer"]]
    first_wrong, second_wrong = wrong_labels[:2]
    model_config = {
        "alias": "llama",
        "model_name": "llama-local",
        "base_url": "http://127.0.0.1:8002/v1",
    }
    manifest = {"pilot_group": "vulnerable"}
    response = build_mad_response_record(
        sample=sample,
        manifest_record=manifest,
        model_config=model_config,
        agent_id="A1",
        round_number=0,
        seed=11,
        prompt="prompt",
        peer_context=[],
        generation_config={"temperature": 0.7, "top_p": 0.9, "max_tokens": 512},
        raw_response=f'{{"answer":"{first_wrong}","reasoning":"test","confidence":0.8}}',
        api_metadata={},
        request_error=None,
    )
    assert response["violation_signature"] == sample["option_violation_signature"][first_wrong]
    assert response["correct"] is False

    correct = {"answer": "A", "correct": True, "violation_signature": [], "reasoning": "A works."}
    wrong_one = {
        "answer": first_wrong,
        "correct": False,
        "violation_signature": sample["option_violation_signature"][first_wrong],
        "reasoning": "First wrong answer.",
    }
    wrong_two = {
        "answer": second_wrong,
        "correct": False,
        "violation_signature": sample["option_violation_signature"][second_wrong],
        "reasoning": "Second wrong answer.",
    }
    before = {"A1": correct, "A2": wrong_one, "A3": wrong_one}
    after = {"A1": wrong_one, "A2": correct, "A3": wrong_two}
    event = build_transition_event(
        item_id=sample["item_id"],
        model_family="llama",
        pilot_group="vulnerable",
        agent_id="A1",
        from_round=0,
        from_agents=before,
        to_agents=after,
    )
    assert event["transition_type"] == "correct_to_wrong"
    assert event["introduced_violations"] == sample["option_violation_signature"][first_wrong]
    assert event["adopted_peer_answer"] is True
    assert event["source_agents"] == ["A2", "A3"]
    assert event["moved_toward_previous_majority"] is True
    assert majority_summary(before)["majority_answer"] == first_wrong
