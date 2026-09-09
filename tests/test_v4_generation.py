from __future__ import annotations

from collections import Counter
from copy import deepcopy

import pytest

from mad_attr_filter.attributes import ATTRIBUTE_BY_KEY
from mad_attr_filter.difficulty import (
    DifficultyConfig,
    DifficultyConfigError,
    all_difficulty_configs,
    far_violation_threshold,
)
from mad_attr_filter.factor_audit import build_factor_audit
from mad_attr_filter.generator import generate_item
from mad_attr_filter.matrix import compute_constraint_matrix
from mad_attr_filter.non_target_facts import NON_TARGET_FACT_BY_KEY
from mad_attr_filter.v4_generator import generate_v4_item, generate_v4_pool
from mad_attr_filter.v4_validation import (
    V4ValidationError,
    validate_v4_item,
    validate_v4_pool,
)


def _wrong_signature_lengths(item: dict) -> list[int]:
    return sorted(
        len(signature)
        for label, signature in item["option_violation_signature"].items()
        if label != item["gold_answer"]
    )


def test_difficulty_config_has_18_independent_cells() -> None:
    configs = all_difficulty_configs()
    assert len(configs) == 18
    assert len({config.cell_id for config in configs}) == 18
    assert {config.constraint_load: config.num_constraints for config in configs} == {
        "CL1": 3,
        "CL2": 5,
        "CL3": 7,
    }
    with pytest.raises(DifficultyConfigError):
        DifficultyConfig("CL4", "DS1_far", "IL1_low")


def test_generate_v4_item_covers_every_factor_cell() -> None:
    for item_index, config in enumerate(all_difficulty_configs(), start=1):
        item = generate_v4_item(item_index, config, 1000 + item_index)
        validate_v4_item(item)
        assert len(item["constraints"]) == config.num_constraints
        assert item["difficulty_factors"] == config.to_dict()
        assert item["generation_metadata"]["generator_version"] == "4.1"

        counts = _wrong_signature_lengths(item)
        if config.distractor_similarity == "DS1_far":
            assert all(count >= far_violation_threshold(config.num_constraints) for count in counts)
        elif config.distractor_similarity == "DS2_medium":
            assert counts[0] == 1 and counts[1] >= 2
        else:
            assert counts == [1, 1, 1]


def test_il2_facts_are_domain_relevant_and_separate_from_formal_attributes() -> None:
    low = generate_v4_item(
        1,
        DifficultyConfig("CL2", "DS3_near", "IL1_low"),
        2001,
        gold_label="A",
    )
    high = generate_v4_item(
        2,
        DifficultyConfig("CL2", "DS3_near", "IL2_high"),
        2002,
        gold_label="A",
    )
    assert all(not entity["non_target_facts"] for entity in low["entities"].values())
    for label, entity in high["entities"].items():
        assert len(entity["non_target_facts"]) == 2
        for fact in entity["non_target_facts"]:
            assert fact["key"] not in ATTRIBUTE_BY_KEY
            assert fact["key"] in NON_TARGET_FACT_BY_KEY
            assert high["scenario"] in NON_TARGET_FACT_BY_KEY[fact["key"]].compatible_scenarios
            assert fact["text"] in high["options"][label]
        assert "As background information" not in high["options"][label]

    constraints = [type("ConstraintLike", (), raw)() for raw in high["constraints"]]
    formal_attributes = {
        label: entity["attributes"] for label, entity in high["entities"].items()
    }
    augmented_attributes = {
        label: {
            **entity["attributes"],
            **{fact["key"]: True for fact in entity["non_target_facts"]},
        }
        for label, entity in high["entities"].items()
    }
    assert compute_constraint_matrix(formal_attributes, constraints) == compute_constraint_matrix(
        augmented_attributes,
        constraints,
    )


def test_ds1_threshold_scales_and_signatures_do_not_degenerate() -> None:
    expected = {"CL1": 2, "CL2": 3, "CL3": 4}
    for item_index, (constraint_load, threshold) in enumerate(expected.items(), start=1):
        item = generate_v4_item(
            item_index,
            DifficultyConfig(constraint_load, "DS1_far", "IL1_low"),
            3000 + item_index,
            gold_label="D",
        )
        wrong_signatures = [
            tuple(signature)
            for label, signature in item["option_violation_signature"].items()
            if label != item["gold_answer"]
        ]
        assert all(len(signature) >= threshold for signature in wrong_signatures)
        assert len(set(wrong_signatures)) == 3
        validate_v4_item(item)


def test_v4_validation_rejects_tampered_signature() -> None:
    item = generate_v4_item(
        1,
        DifficultyConfig("CL3", "DS3_near", "IL2_high"),
        4001,
    )
    tampered = deepcopy(item)
    wrong_label = next(label for label in "ABCD" if label != item["gold_answer"])
    tampered["option_violation_signature"][wrong_label] = []
    with pytest.raises(V4ValidationError, match="violation_signature"):
        validate_v4_item(tampered)


def test_v4_pool_is_reproducible_and_balanced_by_cell() -> None:
    first, first_report = generate_v4_pool(2, global_seed=5001)
    second, second_report = generate_v4_pool(2, global_seed=5001)
    assert first == second
    assert first_report == second_report
    summary = validate_v4_pool(first, expected_items_per_cell=2)
    assert len(first) == 36
    assert summary["validation_pass_rate"] == 1.0
    assert set(Counter(item["difficulty_factors"]["constraint_load"] for item in first).values()) == {12}
    assert set(Counter(item["difficulty_factors"]["distractor_similarity"] for item in first).values()) == {12}
    assert set(Counter(item["difficulty_factors"]["information_load"] for item in first).values()) == {18}


def test_v4_1_prototype_has_180_fully_valid_items_and_passes_factor_audit() -> None:
    items, report = generate_v4_pool(10, global_seed=42)
    summary = validate_v4_pool(items, expected_items_per_cell=10)
    audit = build_factor_audit(items)
    assert len(items) == 180
    assert report["generator_version"] == "4.1"
    assert report["validation_failures"] == 0
    assert report["generation_warning_count"] == 0
    assert summary["validated_items"] == 180
    assert summary["validation_pass_rate"] == 1.0
    assert audit["confound_checks"]["all_ds_levels_verified"] is True
    assert audit["confound_checks"]["all_il_levels_verified"] is True
    assert audit["confound_checks"]["all_items_fully_valid"] is True


def test_v3_generation_behavior_remains_on_the_v3_schema() -> None:
    item = generate_item(1, "medium", 6001, num_constraints=4)
    assert item["generator_version"] == "3.0-en"
    assert item["option_closeness"] == "medium"
    assert item["structural_complexity"] == "medium"
    assert "difficulty_factors" not in item
    assert "generation_metadata" not in item
