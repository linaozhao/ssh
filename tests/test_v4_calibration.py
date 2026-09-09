from __future__ import annotations

import json
from pathlib import Path

import pytest

from mad_attr_filter.io import load_json, read_jsonl, write_jsonl
from mad_attr_filter.v4_calibration import (
    CalibrationError,
    audit_existing_records,
    build_output_record,
    expected_keys,
    parse_calibration_response,
    select_preflight_items,
)
from mad_attr_filter.v4_calibration_analysis import (
    audit_run_inventory,
    build_cell_model_statistics,
    build_item_model_analysis,
)

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "multi_constraint_v4_1_prototype.jsonl"
CONFIG = ROOT / "config" / "v4_1_calibration_config.json"


def test_missing_confidence_keeps_clear_answer_but_is_not_json_compliant() -> None:
    parsed = parse_calibration_response('{"answer":"C","reasoning":"C meets each condition."}')
    assert parsed["answer"] == "C"
    assert parsed["answer_extractable"] is True
    assert parsed["strict_json_syntax"] is True
    assert parsed["json_compliant"] is False
    assert parsed["parse_source"] == "strict_json"


def test_fallback_ignores_discussed_options_and_uses_explicit_final_answer() -> None:
    raw = "Option A fails Monday. Candidate B lacks clearance.\nFinal answer: D"
    parsed = parse_calibration_response(raw)
    assert parsed["answer"] == "D"
    assert parsed["answer_extractable"] is True
    assert parsed["parse_source"] == "explicit_final_answer"
    assert parsed["json_compliant"] is False


def test_fallback_rejects_generic_or_conflicting_answer_mentions() -> None:
    generic = parse_calibration_response("Option A fails, but Candidate B is worth checking.")
    assert generic["answer"] is None
    assert generic["answer_extractable"] is False

    conflicting = parse_calibration_response("Answer: A\nFinal answer: B")
    assert conflicting["answer"] is None
    assert conflicting["ambiguous_answer"] is True
    assert conflicting["parse_source"] == "conflicting_answers"


def test_malformed_json_answer_field_is_separate_from_json_compliance() -> None:
    parsed = parse_calibration_response(
        '{"answer":"D","reasoning":"Candidate D meets every requirement."'
    )
    assert parsed["answer"] == "D"
    assert parsed["answer_extractable"] is True
    assert parsed["json_compliant"] is False
    assert parsed["parse_source"] == "malformed_json_answer_field"

    conflicting = parse_calibration_response(
        '{"answer":"D","reasoning":"unfinished"\nFinal answer: A'
    )
    assert conflicting["answer"] is None
    assert conflicting["ambiguous_answer"] is True


def test_preflight_is_stratified_over_all_18_cells() -> None:
    samples = read_jsonl(DATASET)
    selected = select_preflight_items(samples)
    assert len(selected) == 18
    assert len({item["metadata"]["difficulty_cell"] for item in selected}) == 18
    assert selected == select_preflight_items(samples)


def test_v4_output_record_uses_factor_fields_and_separate_parse_flags() -> None:
    sample = read_jsonl(DATASET)[0]
    config = load_json(CONFIG)
    record = build_output_record(
        sample=sample,
        model_config=config["models"][0],
        run_id=1,
        seed=11,
        generation_config={"temperature": 0.7, "top_p": 0.9, "max_tokens": 512},
        experiment_id="test",
        experiment_fingerprint="fingerprint",
        raw_response=json.dumps(
            {"answer": sample["gold_answer"], "reasoning": "Checked.", "confidence": 0.8}
        ),
        api_metadata={"finish_reason": "stop", "usage": {"completion_tokens": 9}},
        request_error=None,
        phase="preflight",
    )
    assert record["difficulty_factors"] == sample["difficulty_factors"]
    assert record["difficulty_cell"] == sample["metadata"]["difficulty_cell"]
    assert "option_closeness" not in record
    assert "structural_complexity" not in record
    assert record["answer_extractable"] is True
    assert record["json_compliant"] is True
    assert record["selected_option_violation_signature"] == []


def test_resume_rejects_fingerprint_mismatch(tmp_path: Path) -> None:
    samples = read_jsonl(DATASET)[:1]
    config = load_json(CONFIG)
    allowed = expected_keys(samples, config)
    record = {
        "item_id": samples[0]["item_id"],
        "model_alias": "qwen",
        "run_id": 1,
        "experiment_fingerprint": "old",
    }
    output = tmp_path / "outputs.jsonl"
    write_jsonl(output, [record])
    with pytest.raises(CalibrationError, match="Fingerprint mismatch"):
        audit_existing_records(output, allowed, "new")


def test_model_separated_statistics_use_explicit_denominators() -> None:
    samples = read_jsonl(DATASET)
    config = load_json(CONFIG)
    outputs = []
    for sample in samples:
        for model in config["models"]:
            for run_id, seed in enumerate(config["seeds"], start=1):
                outputs.append(
                    {
                        "item_id": sample["item_id"],
                        "model_alias": model["alias"],
                        "run_id": run_id,
                        "seed": seed,
                        "experiment_fingerprint": "test",
                        "difficulty_cell": sample["metadata"]["difficulty_cell"],
                        "difficulty_factors": sample["difficulty_factors"],
                        "answer": sample["gold_answer"],
                        "answer_extractable": True,
                        "json_compliant": True,
                        "correct": True,
                        "request_error": None,
                        "truncated": False,
                        "selected_option_violation_signature": [],
                    }
                )
    inventory = audit_run_inventory(samples, outputs, config, "test")
    item_rows = build_item_model_analysis(samples, outputs, config)
    cell_rows = build_cell_model_statistics(samples, outputs, item_rows, config)
    assert inventory["complete"] is True
    assert len(item_rows) == 360
    assert len(cell_rows) == 36
    assert all(row["expected_record_count"] == 30 for row in cell_rows)
    assert all(row["valid_accuracy_denominator"] == 30 for row in cell_rows)
    assert all(row["disagreement_denominator"] == 10 for row in cell_rows)
    assert all(row["valid_answer_accuracy"] == 1.0 for row in cell_rows)

    outputs[0]["answer"] = None
    outputs[0]["answer_extractable"] = False
    outputs[0]["json_compliant"] = False
    incomplete_items = build_item_model_analysis(samples, outputs, config)
    incomplete_cells = build_cell_model_statistics(
        samples, outputs, incomplete_items, config
    )
    affected = next(
        row
        for row in incomplete_cells
        if row["model_alias"] == outputs[0]["model_alias"]
        and row["difficulty_cell"] == outputs[0]["difficulty_cell"]
    )
    assert affected["incomplete_item_count"] == 1
    assert affected["disagreement_denominator"] == 9
