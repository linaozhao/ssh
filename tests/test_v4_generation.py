from __future__ import annotations

from collections import Counter
from copy import deepcopy

import pytest

from mad_attr_filter.attributes import ATTRIBUTE_BY_KEY
from mad_attr_filter.difficulty import (
    DifficultyConfig,
    DifficultyConfigError,
    all_difficulty_configs,
)
from mad_attr_filter.generator import generate_item
from mad_attr_filter.matrix import compute_constraint_matrix
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
        assert item["generation_metadata"]["generator_version"] == "4.0"

        counts = _wrong_signature_lengths(item)
        if config.distractor_similarity == "DS1_far":
            assert all(count >= 3 for count in counts)
        elif config.distractor_similarity == "DS2_medium":
            assert counts[0] == 1 and counts[1] >= 2
        else:
            assert counts == [1, 1, 1]


def test_information_load_is_separate_from_formal_attributes() -> None:
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
    assert all(not entity["irrelevant_facts"] for entity in low["entities"].values())
    for label, entity in high["entities"].items():
        assert len(entity["irrelevant_facts"]) == 2
        assert all(fact["key"] not in ATTRIBUTE_BY_KEY for fact in entity["irrelevant_facts"])
        assert all(fact["text"] in high["options"][label] for fact in entity["irrelevant_facts"])

    constraints = [type("ConstraintLike", (), raw)() for raw in high["constraints"]]
    formal_attributes = {
        label: entity["attributes"] for label, entity in high["entities"].items()
    }
    augmented_attributes = {
        label: {
            **entity["attributes"],
            **{fact["key"]: True for fact in entity["irrelevant_facts"]},
        }
        for label, entity in high["entities"].items()
    }
    assert compute_constraint_matrix(formal_attributes, constraints) == compute_constraint_matrix(
        augmented_attributes,
        constraints,
    )


def test_cl1_ds1_boolean_boundary_is_valid_and_explicit() -> None:
    item = generate_v4_item(
        1,
        DifficultyConfig("CL1", "DS1_far", "IL1_low"),
        3001,
        gold_label="D",
    )
    wrong_signatures = [
        tuple(signature)
        for label, signature in item["option_violation_signature"].items()
        if label != item["gold_answer"]
    ]
    assert len(set(wrong_signatures)) == 1
    assert wrong_signatures[0] == ("C1", "C2", "C3")
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


def test_v3_generation_behavior_remains_on_the_v3_schema() -> None:
    item = generate_item(1, "medium", 6001, num_constraints=4)
    assert item["generator_version"] == "3.0-en"
    assert item["option_closeness"] == "medium"
    assert item["structural_complexity"] == "medium"
    assert "difficulty_factors" not in item
    assert "generation_metadata" not in item
