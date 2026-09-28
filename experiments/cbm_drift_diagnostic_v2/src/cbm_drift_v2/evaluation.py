"""Reference-label evaluation with category-independent one-to-one event matching."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from cbm_drift_v2.common import read_jsonl, write_json


def _location(event: dict[str, Any]) -> tuple[str, str, str]:
    return (str(event["trajectory_id"]), str(event["agent_id"]), str(event.get("message_id") or event.get("event_start_message_id")))


def evaluate_events(predictions: list[dict[str, Any]], references: list[dict[str, Any]]) -> dict[str, Any]:
    """Match once by trajectory, agent, and message; classify only after matching."""
    positive_references = [row for row in references if row.get("has_diagnostic_event", True)]
    negative_references = [row for row in references if row.get("has_diagnostic_event") is False]
    available: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for index, reference in enumerate(positive_references):
        available[_location(reference)].append(index)
    matched, unmatched_predictions, used = [], [], set()
    for prediction in predictions:
        choices = [index for index in available.get(_location(prediction), []) if index not in used]
        if not choices:
            unmatched_predictions.append(prediction)
            continue
        index = choices[0]
        used.add(index)
        matched.append((prediction, positive_references[index]))
    unmatched_references = [row for index, row in enumerate(positive_references) if index not in used]
    tp, fp, fn = len(matched), len(unmatched_predictions), len(unmatched_references)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    labels = sorted({label for row in predictions + positive_references for label in row.get("content_labels", [])})
    classification = {}
    for label in labels:
        label_tp = sum(label in p.get("content_labels", []) and label in r.get("content_labels", []) for p, r in matched)
        pred_count = sum(label in row.get("content_labels", []) for row in predictions)
        ref_count = sum(label in row.get("content_labels", []) for row in positive_references)
        matched_ref_count = sum(label in row.get("content_labels", []) for _, row in matched)
        matched_pred_count = sum(label in row.get("content_labels", []) for row, _ in matched)
        p_value = label_tp / pred_count if pred_count else None
        r_value = label_tp / ref_count if ref_count else None
        classification[label] = {
            "support": ref_count, "matched_true_positive": label_tp,
            "precision_on_matched_events": label_tp / matched_pred_count if matched_pred_count else None,
            "recall_on_matched_events": label_tp / matched_ref_count if matched_ref_count else None,
            "precision_end_to_end": p_value, "recall_end_to_end": r_value,
            "f1_end_to_end": 2 * p_value * r_value / (p_value + r_value) if p_value and r_value else None,
        }
    negative_locations = {_location(row): row for row in negative_references}
    negative_false_positives = [row for row in predictions if _location(row) in negative_locations]
    negative_by_status = {}
    for status in ("reasonable_update", "correct_maintenance"):
        keys = {key for key, row in negative_locations.items() if row.get("temporal_status") == status}
        negative_by_status[status] = {
            "reference_negative_messages": len(keys),
            "false_positive_predictions": sum(_location(row) in keys for row in predictions),
        }
    matched_localization = {
        "agent_exact": sum(p.get("agent_id") == r.get("agent_id") for p, r in matched),
        "stage_exact": sum(r.get("evidence_stage") is None or p.get("evidence_stage") == r.get("evidence_stage") for p, r in matched),
        "round_exact": sum(r.get("round") is None or p.get("round") == r.get("round") for p, r in matched),
        "message_exact": len(matched),
        "denominator": len(matched),
    }
    return {
        "status": "evaluated", "matching_rule": "one-to-one exact trajectory_id + agent_id + event start message; category independent",
        "predictions": len(predictions), "positive_references": len(positive_references),
        "explicit_negative_references": len(negative_references), "matched": tp,
        "precision": precision, "recall": recall, "f1": f1,
        "unmatched_predictions": fp, "unmatched_references": fn,
        "classification": classification,
        "matched_event_localization": matched_localization,
        "explicit_negative_false_positives": len(negative_false_positives),
        "negative_false_positives_by_status": negative_by_status,
        "uncertain_or_unresolved_predictions": sum(
            row.get("temporal_status") == "uncertain" or "unresolved" in row.get("content_labels", [])
            for row in predictions
        ),
        "quote_and_object_validation": {
            "passed": sum(bool(row.get("quote_and_id_validation_passed")) for row in predictions),
            "denominator": len(predictions),
        },
        "temporal_status_confusion": dict(Counter(
            f"{reference.get('temporal_status')}->{prediction.get('temporal_status')}" for prediction, reference in matched
        )),
    }


def evaluate_files(predictions_path: Path, references_path: Path | None, output_path: Path) -> dict[str, Any]:
    """Write an explicit not-evaluated result when independent references are absent."""
    predictions = read_jsonl(predictions_path)
    if references_path is None or not references_path.exists():
        result = {
            "status": "not_evaluated", "reason": "independent adjudicated reference labels are absent",
            "prediction_count": len(predictions), "precision": None, "recall": None, "f1": None,
        }
    else:
        references = read_jsonl(references_path)
        result = evaluate_events(predictions, references)
    write_json(output_path, result)
    return result
