from __future__ import annotations

import json
from pathlib import Path

import pytest

from mad_attr_filter.io import load_json, read_jsonl, write_jsonl
from mad_attr_filter.qwen_followup import (
    build_extension_pool,
    build_information_load_pairs,
    build_position_variants,
    normalized_content_hash,
    parse_followup_response,
)
from mad_attr_filter.qwen_followup_runner import (
    audit_output_inventory,
    build_output_record,
    materialize_experiment_config,
)
from mad_attr_filter.v4_validation import validate_v4_item, validate_v4_pool

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "data/multi_constraint_v4_1_prototype.jsonl"
ITEM_ANALYSIS = ROOT / "results/v4_1_calibration/item_model_analysis.jsonl"
CONFIG = ROOT / "config/qwen_v4_1_followup_config.json"


def _data() -> tuple[list[dict], list[dict]]:
    samples = read_jsonl(PROTOTYPE)
    rows = [
        row
        for row in read_jsonl(ITEM_ANALYSIS)
        if row["model_alias"] == "qwen"
    ]
    return samples, rows


def test_candidate_name_answer_is_semantically_scored_but_not_protocol_compliant() -> None:
    sample = read_jsonl(PROTOTYPE)[0]
    gold_name = sample["entities"][sample["gold_answer"]]["name"]
    parsed = parse_followup_response(
        json.dumps(
            {"answer": gold_name, "reasoning": "Checked every condition.", "confidence": 0.8}
        ),
        sample,
    )
    assert parsed["answer"] == sample["gold_answer"]
    assert parsed["answer_extractable"] is True
    assert parsed["semantic_name_mapping_used"] is True
    assert parsed["strict_answer_format"] is False
    assert parsed["json_compliant"] is False


def test_parser_does_not_use_first_candidate_mentioned_in_reasoning() -> None:
    sample = read_jsonl(PROTOTYPE)[0]
    parsed = parse_followup_response(
        json.dumps(
            {
                "answer": "D",
                "reasoning": "Candidate A fails first; Candidate D is the final choice.",
                "confidence": 0.7,
            }
        ),
        sample,
    )
    assert parsed["answer"] == "D"
    assert parsed["parse_source"] == "strict_json_label"


def test_unknown_or_ambiguous_name_is_not_guessed() -> None:
    sample = read_jsonl(PROTOTYPE)[0]
    parsed = parse_followup_response(
        '{"answer":"Not A Candidate","reasoning":"Option A was considered","confidence":0.5}',
        sample,
    )
    assert parsed["answer"] is None
    assert parsed["answer_extractable"] is False

    conflicting_name = sample["entities"]["B"]["name"]
    conflicting = parse_followup_response(
        json.dumps(
            {"answer": conflicting_name, "reasoning": "Checked.", "confidence": 0.5}
        )
        + "\nFinal answer: A",
        sample,
    )
    assert conflicting["answer"] is None
    assert conflicting["ambiguous_answer"] is True


def test_position_variants_preserve_candidate_identity_and_cover_all_labels() -> None:
    samples, rows = _data()
    variants, manifest = build_position_variants(samples, rows)
    assert len(variants) == 84
    assert len(manifest) == 84
    assert {item["selection_group"] for item in variants} == {
        "stable_wrong",
        "mixed",
        "stable_correct_control",
    }
    source_ids = {entry["source_item_id"] for entry in manifest}
    assert len(source_ids) == 21
    for source_id in source_ids:
        records = [entry for entry in manifest if entry["source_item_id"] == source_id]
        assert {entry["new_gold_label"] for entry in records} == set("ABCD")
    for item in variants:
        validate_v4_item(item)


def test_il_pairs_remove_only_marked_non_target_suffixes() -> None:
    samples = read_jsonl(PROTOTYPE)
    variants, manifest = build_information_load_pairs(samples)
    assert len(variants) == 72
    assert len(manifest) == 36
    by_source: dict[str, list[dict]] = {}
    for item in variants:
        by_source.setdefault(item["source_item_id"], []).append(item)
        validate_v4_item(item)
    for pair in by_source.values():
        low = next(item for item in pair if item["pair_version"] == "IL1_low")
        high = next(item for item in pair if item["pair_version"] == "IL2_high")
        for field in (
            "constraints",
            "gold_answer",
            "option_constraint_matrix",
            "option_violation_signature",
        ):
            assert low[field] == high[field]
        for label in "ABCD":
            assert high["options"][label].startswith(low["options"][label])
            assert low["entities"][label]["non_target_facts"] == []
            assert len(high["entities"][label]["non_target_facts"]) == 2


def test_extension_is_reproducible_balanced_valid_and_duplicate_free() -> None:
    prototype = read_jsonl(PROTOTYPE)
    first, first_report = build_extension_pool(prototype)
    second, second_report = build_extension_pool(prototype)
    assert first == second
    assert first_report == second_report
    assert len(first) == 360
    assert validate_v4_pool(first, expected_items_per_cell=20)["validation_pass_rate"] == 1.0
    assert validate_v4_pool([*prototype, *first], expected_items_per_cell=30)[
        "validation_pass_rate"
    ] == 1.0
    hashes = [normalized_content_hash(item) for item in [*prototype, *first]]
    assert len(hashes) == len(set(hashes)) == 540
    assert first_report["duplicate_item_id_count"] == 0


def test_output_record_maps_candidate_name_without_using_gold() -> None:
    sample = read_jsonl(PROTOTYPE)[0]
    full_config = load_json(CONFIG)
    config = materialize_experiment_config(full_config, "extension")
    name = sample["entities"]["B"]["name"]
    record = build_output_record(
        sample=sample,
        experiment_config=config,
        run_id=1,
        seed=11,
        experiment_fingerprint="fingerprint",
        raw_response=json.dumps(
            {"answer": name, "reasoning": "Checked.", "confidence": 0.9}
        ),
        api_metadata={"finish_reason": "stop", "usage": {}},
        request_error=None,
    )
    assert record["answer"] == "B"
    assert record["selected_candidate_name"] == name
    assert record["correct"] is (sample["gold_answer"] == "B")
    assert record["selected_option_violation_signature"] == sample[
        "option_violation_signature"
    ]["B"]


def test_resume_rejects_fingerprint_mismatch(tmp_path: Path) -> None:
    sample = read_jsonl(PROTOTYPE)[0]
    full_config = load_json(CONFIG)
    config = materialize_experiment_config(full_config, "extension")
    output = tmp_path / "records.jsonl"
    write_jsonl(
        output,
        [
            {
                "variant_id": sample["item_id"],
                "model_alias": "qwen",
                "run_id": 1,
                "experiment_fingerprint": "old",
            }
        ],
    )
    with pytest.raises(ValueError, match="incompatible"):
        audit_output_inventory(output, [sample], config, "new")
