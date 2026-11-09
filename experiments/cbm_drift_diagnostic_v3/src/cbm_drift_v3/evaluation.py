"""Frozen, label-independent matching and denominator-explicit pilot metrics."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .common import read_jsonl, write_json

MATCHING_VERSION = "v3-object-span-bipartite-1"
LABELS = ("F", "R", "I")
VERIFIED = {"program_verified", "human_verified"}
LABEL_ALIASES = {"factual_deviation": "F", "rule_deviation": "R",
                 "inference_application_error": "I"}
FAILURES = {"api_failure", "schema_failure", "parse_failure", "refusal",
            "truncated", "authentication_failure", "quota_failure", "not_run",
            "model_mismatch", "invalid_response"}


def _labels(row: dict[str, Any]) -> set[str]:
    values = row.get("expected_content_labels", row.get("content_labels", []))
    return {LABEL_ALIASES.get(value, value) for value in values}


def _expected(row: dict[str, Any], key: str) -> Any:
    return row.get("expected_" + key, row.get(key))


def _ratio(numerator: int | float, denominator: int | float) -> float | None:
    return numerator / denominator if denominator else None


def prf(tp: int, fp: int, fn: int) -> dict[str, Any]:
    """F1 is zero for missed positives, even when precision is undefined."""
    denominator = 2 * tp + fp + fn
    return {"tp": tp, "fp": fp, "fn": fn, "support": tp + fn,
            "precision": _ratio(tp, tp + fp), "recall": _ratio(tp, tp + fn),
            "f1": _ratio(2 * tp, denominator),
            "undefined_reason": None if denominator else "no applicable positive reference or prediction"}


def _location(row: dict[str, Any]) -> tuple[Any, ...]:
    return (row.get("case_id", row.get("trajectory_id")),
            row.get("message_id", row.get("target_message_id", row.get("event_start_message_id"))),
            row.get("agent_id"), row.get("evidence_stage"), row.get("round"))


def _object(row: dict[str, Any]) -> tuple[Any, ...]:
    return (tuple(sorted(set(row.get("candidate_ids", row.get("target_entity_ids", []))))),
            row.get("attribute"), tuple(sorted(set(row.get("rule_ids", row.get("violated_rule_ids", []))))))


def _span(row: dict[str, Any]) -> tuple[Any, ...] | None:
    quote, start, end = row.get("quote"), row.get("start"), row.get("end")
    if not isinstance(quote, str) or not quote or type(start) is not int or type(end) is not int:
        return None
    if start < 0 or end - start != len(quote):
        return None
    return quote, start, end


def _same_identity(prediction: dict[str, Any], reference: dict[str, Any]) -> bool:
    if _location(prediction) != _location(reference):
        return False
    if not any(_object(prediction)) or _span(prediction) is None:
        return False
    # Only preregistered reference alternatives are eligible, never model proposals.
    alternatives = [reference] + [dict(reference, **row) for row in reference.get("acceptable_equivalent_claims", [])]
    return any(_object(prediction) == _object(row) and _span(prediction) == _span(row)
               for row in alternatives)


def match_claims(predictions: list[dict[str, Any]], references: list[dict[str, Any]]) -> list[tuple[int, int]]:
    """Deterministic maximum-cardinality bipartite matching, without label access.

    Input row order is the frozen tie break. Evidence correctness and semantic
    categories do not choose pairs. An augmenting path avoids greedy losses
    when a preregistered equivalent span is shared by multiple references.
    """
    edges = [[j for j, reference in enumerate(references) if _same_identity(prediction, reference)]
             for prediction in predictions]
    owners: dict[int, int] = {}

    def augment(i: int, visited: set[int]) -> bool:
        for j in edges[i]:
            if j in visited:
                continue
            visited.add(j)
            if j not in owners or augment(owners[j], visited):
                owners[j] = i
                return True
        return False

    for i in range(len(predictions)):
        augment(i, set())
    return sorted((i, j) for j, i in owners.items())


def _evidence_ok(prediction: dict[str, Any], reference: dict[str, Any]) -> bool:
    expected = set(reference.get("conflicting_evidence_ids", reference.get("violated_fact_ids", [])))
    actual = set(prediction.get("conflicting_evidence_ids", prediction.get("violated_fact_ids", [])))
    alternatives = [expected]
    for alternative in reference.get("acceptable_equivalent_support", []):
        if isinstance(alternative, list):
            alternatives.append(set(alternative))
        elif isinstance(alternative, dict) and "conflicting_evidence_ids" in alternative:
            alternatives.append(set(alternative["conflicting_evidence_ids"]))
    if actual not in alternatives:
        return False
    version = reference.get("evidence_version")
    return version is None or prediction.get("evidence_version") == version


def _support_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (row.get("message_id"), _span(row))


def _prior_ok(prediction: dict[str, Any], reference: dict[str, Any]) -> bool:
    expected = {_support_key(row) for row in reference.get("prior_support", [])}
    actual = {_support_key(row) for row in prediction.get("prior_support", [])}
    alternatives = [expected]
    for alternative in reference.get("acceptable_equivalent_support", []):
        if isinstance(alternative, dict) and "prior_support" in alternative:
            alternatives.append({_support_key(row) for row in alternative["prior_support"]})
    return actual in alternatives


def evaluate_events(predictions: list[dict[str, Any]], references: list[dict[str, Any]]) -> dict[str, Any]:
    """Evaluate already normalized, applicable positive claim events.

    Explicitly pending/ambiguous/uncertain reference events are excluded.
    Missing verification metadata is allowed only by this low-level helper;
    the controlled evaluator always requires verified references.
    """
    applicable = [row for row in references
                  if row.get("verification_status", "program_verified") in VERIFIED
                  and _expected(row, "current_deviation") not in ("uncertain", "no")
                  and row.get("has_diagnostic_event") is not False]
    pairs = match_claims(predictions, applicable)
    strict = [(i, j) for i, j in pairs if _evidence_ok(predictions[i], applicable[j])
              and predictions[i].get("stance") == applicable[j].get("stance")]
    classification = {}
    for label in LABELS:
        tp = sum(label in _labels(predictions[i]) and label in _labels(applicable[j]) for i, j in strict)
        classification[label] = prf(tp, sum(label in _labels(row) for row in predictions) - tp,
                                    sum(label in _labels(row) for row in applicable) - tp)
    micro = prf(*(sum(row[key] for row in classification.values()) for key in ("tp", "fp", "fn")))
    supported = [row["f1"] for row in classification.values() if row["support"] > 0]
    temporal_pairs = [(i, j) for i, j in strict if _temporal_eligible(applicable[j])]
    temporal_support = sum(_temporal_eligible(row) for row in applicable)
    temporal_correct = sum(_expected(applicable[j], "temporal_status") == predictions[i].get("temporal_status")
                           and _prior_ok(predictions[i], applicable[j]) for i, j in temporal_pairs)
    return {"matching_version": MATCHING_VERSION,
            "matching_rule": "maximum cardinality, frozen index tie break, location + object + exact span; no labels",
            "reference_events": len(applicable), "excluded_reference_events": len(references) - len(applicable),
            "identity_pairs": [list(pair) for pair in pairs], "strict_pairs": [list(pair) for pair in strict],
            "object_and_quote": prf(len(pairs), len(predictions) - len(pairs), len(applicable) - len(pairs)),
            "strict_localization": prf(len(strict), len(predictions) - len(strict), len(applicable) - len(strict)),
            "classification": classification, "micro": micro,
            "macro_f1": sum(supported) / len(supported) if supported else None,
            "macro_supported_labels": sum(row["support"] > 0 for row in classification.values()),
            "prior_support_exact": {"correct": sum(_prior_ok(predictions[i], applicable[j]) for i, j in strict),
                                    "denominator": len(applicable)},
            "temporal": {"correct": temporal_correct, "support": temporal_support,
                         "accuracy": _ratio(temporal_correct, temporal_support)}}


def _temporal_eligible(row: dict[str, Any]) -> bool:
    status = _expected(row, "temporal_status")
    return bool(status and status != "uncertain" and
                row.get("temporal_evaluable", row.get("history_sufficient", False)))


def _prediction(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if row is None or row.get("status") in FAILURES:
        return None
    if any(row.get(key) is False for key in ("api_success", "parse_success", "schema_valid")):
        return None
    if row.get("finish_reason") in {"length", "content_filter"} or row.get("refusal"):
        return None
    value = row.get("prediction", row.get("normalized", row))
    return value if isinstance(value, dict) and value.get("current_deviation") in {"yes", "no", "uncertain"} else None


def _claims(row: dict[str, Any], reference: bool = False) -> list[dict[str, Any]]:
    inherited = {key: row[key] for key in ("case_id", "trajectory_id", "message_id", "target_message_id",
                 "agent_id", "evidence_stage", "round", "verification_status", "history_sufficient", "temporal_evaluable") if key in row}
    result = []
    for claim in row.get("claims", []):
        if not isinstance(claim, dict):
            continue
        # Non-deviating support claims stay in the diagnostic, not the event denominator.
        labels = _labels(claim)
        deviation = _expected(claim, "current_deviation")
        if deviation == "no" or (claim.get("stance") in {"quoted", "rejected", "hypothetical"} and deviation != "yes"):
            continue
        if deviation != "yes" and not labels:
            continue
        event = dict(inherited, **claim)
        if reference and event.get("verification_status", "program_verified") not in VERIFIED:
            continue
        result.append(event)
    return result


def _negative_metrics(rows: list[tuple[dict[str, Any], dict[str, Any] | None]]) -> dict[str, Any]:
    denominator = len(rows)
    judged = sum(prediction is not None and prediction["current_deviation"] in {"yes", "no"} for _, prediction in rows)
    false_positive = sum(prediction is not None and prediction["current_deviation"] == "yes" for _, prediction in rows)
    true_negative = sum(prediction is not None and prediction["current_deviation"] == "no" for _, prediction in rows)
    return {"support": denominator, "judged": judged, "false_positives": false_positive,
            "true_negatives": true_negative, "false_positive_rate_on_judged": _ratio(false_positive, judged),
            "judgment_coverage": _ratio(judged, denominator),
            "end_to_end_correct_rejection_rate": _ratio(true_negative, denominator)}


def _summarize(outputs: dict[str, dict[str, Any]], references: list[dict[str, Any]]) -> dict[str, Any]:
    usable = [row for row in references if row.get("verification_status") in VERIFIED
              and _expected(row, "current_deviation") in {"yes", "no"}]
    pairs = [(reference, _prediction(outputs.get(reference["case_id"]))) for reference in usable]
    positive_count = sum(_expected(reference, "current_deviation") == "yes" for reference in usable)
    tp = sum(_expected(reference, "current_deviation") == "yes" and prediction is not None
             and prediction["current_deviation"] == "yes" for reference, prediction in pairs)
    fp = sum(_expected(reference, "current_deviation") == "no" and prediction is not None
             and prediction["current_deviation"] == "yes" for reference, prediction in pairs)
    predicted_claims, reference_claims = [], []
    for reference, prediction in pairs:
        if _expected(reference, "current_deviation") == "yes":
            reference_claims.extend(_claims(reference, reference=True))
        if prediction is not None:
            # Routing identity comes from the frozen request, never guessed model metadata.
            predicted_claims.extend(_claims(dict(prediction, case_id=reference["case_id"])))
    events = evaluate_events(predicted_claims, reference_claims)
    classification = {}
    for label in LABELS:
        true_positive = sum(label in _labels(reference) and prediction is not None and label in _labels(prediction)
                            for reference, prediction in pairs)
        predicted = sum(prediction is not None and label in _labels(prediction) for _, prediction in pairs)
        support = sum(label in _labels(reference) for reference, _ in pairs)
        classification[label] = prf(true_positive, predicted - true_positive, support - true_positive)
    macro = [row["f1"] for row in classification.values() if row["support"]]
    positive_pairs = [(r, p) for r, p in pairs if _expected(r, "current_deviation") == "yes"]
    localization = {}
    for name, keys in {"message": (1,), "agent": (2,), "stage": (3,), "round": (4,),
                       "joint": (1, 2, 3, 4)}.items():
        applicable = [(r, p) for r, p in positive_pairs if all(_location(r)[i] is not None for i in keys)]
        correct = sum(p is not None and p["current_deviation"] == "yes"
                      and all(_location(r)[i] == _location(p)[i] for i in keys) for r, p in applicable)
        localization[name] = {"correct": correct, "support": len(applicable), "recall": _ratio(correct, len(applicable))}
    temporal = [(r, p) for r, p in pairs if _temporal_eligible(r)]
    temporal_correct = sum(p is not None and p.get("temporal_status") == _expected(r, "temporal_status") for r, p in temporal)
    no_history = [(r, p) for r, p in pairs if _expected(r, "temporal_status") == "uncertain"
                  and not r.get("history_sufficient", r.get("temporal_evaluable", False))]
    unsafe = {"initial_error", "newly_introduced", "persistent", "recurrence", "post_update_reversion"}
    judged_no_history = sum(p is not None for _, p in no_history)
    certainty_errors = sum(p is not None and p.get("temporal_status") in unsafe for _, p in no_history)
    uncertain_correct = sum(p is not None and p.get("temporal_status") == "uncertain" for _, p in no_history)
    negative_pairs = [(r, p) for r, p in pairs if _expected(r, "current_deviation") == "no"]
    strata = sorted({r.get("primary_stratum", "unspecified") for r in references})
    negative_by_stratum = {stratum: _negative_metrics([(r, p) for r, p in negative_pairs if r.get("primary_stratum", "unspecified") == stratum])
                          for stratum in strata}
    explanation_errors = [(r, p) for r, p in positive_pairs if _expected(r, "answer_status") == "correct"]
    unresolved = [(r, p) for r, p in positive_pairs if _labels(r) == {"unresolved"}]
    unresolved_correct = sum(p is not None and p["current_deviation"] == "yes" and _labels(p) == {"unresolved"} for r, p in unresolved)
    submitted = list(outputs.values())
    coverage = {key: {"passed": sum(row.get(key) is True for row in submitted), "denominator": len(references)}
                for key in ("api_success", "parse_success", "schema_valid", "quote_valid", "object_valid", "formal_valid")}
    return {"reference_count": len(references), "eligible_reference_count": len(usable),
            "excluded_references": dict(Counter(
                r.get("verification_status", "missing_verification") if r.get("verification_status") not in VERIFIED
                else "uncertain_current_deviation" for r in references if r not in usable)),
            "reference_sources": dict(Counter(r.get("reference_source", "unspecified") for r in usable)),
            "stratum_reference_coverage": {s: {"total": sum(r.get("primary_stratum", "unspecified") == s for r in references),
                                                "eligible": sum(r.get("primary_stratum", "unspecified") == s for r in usable)} for s in strata},
            "current_deviation": prf(tp, fp, positive_count - tp),
            "negative": _negative_metrics(negative_pairs), "negative_by_stratum": negative_by_stratum,
            "classification_message": {"per_label": classification,
                "micro": prf(*(sum(row[key] for row in classification.values()) for key in ("tp", "fp", "fn"))),
                "macro_f1": sum(macro) / len(macro) if macro else None,
                "macro_supported_labels": len(macro)},
            "claim_events": events, "message_localization": localization,
            "temporal": {"support": len(temporal), "correct": temporal_correct, "accuracy": _ratio(temporal_correct, len(temporal)),
                         "confusion": dict(Counter(f"{_expected(r, 'temporal_status')}->{p.get('temporal_status') if p else 'uncompleted'}" for r, p in temporal))},
            "missing_history": {"support": len(no_history), "judged": judged_no_history,
                "inappropriate_certainty": certainty_errors, "inappropriate_certainty_rate_on_judged": _ratio(certainty_errors, judged_no_history),
                "judgment_coverage": _ratio(judged_no_history, len(no_history)),
                "uncertain_correct": uncertain_correct, "uncertain_end_to_end_rate": _ratio(uncertain_correct, len(no_history))},
            "correct_answer_wrong_explanation": {"support": len(explanation_errors),
                "detection_rate": _ratio(sum(p is not None and p["current_deviation"] == "yes" for _, p in explanation_errors), len(explanation_errors))},
            "unresolved": {"support": len(unresolved), "correct": unresolved_correct, "rate": _ratio(unresolved_correct, len(unresolved)),
                           "predicted": sum(p is not None and "unresolved" in _labels(p) for _, p in pairs)},
            "abstentions": sum(p is not None and p["current_deviation"] == "uncertain" for _, p in pairs),
            "coverage": {**coverage, "requests_expected": len(references), "outputs_received": len(submitted),
                         "completed_diagnostics": sum(_prediction(row) is not None for row in submitted),
                         "status_counts": dict(Counter(row.get("status", "unspecified") for row in submitted)),
                         "missing_outputs": len(references) - len(submitted)},
            "resources": resource_summary(submitted)}


def resource_summary(outputs: list[dict[str, Any]]) -> dict[str, Any]:
    """Unknown usage/cost is null, never fabricated as zero."""
    result: dict[str, Any] = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        known = [row["usage"][key] for row in outputs if isinstance(row.get("usage"), dict)
                 and type(row["usage"].get(key)) in (int, float) and row["usage"][key] >= 0]
        result[key] = {"reported_total": sum(known) if known else None, "known_outputs": len(known), "unknown_outputs": len(outputs) - len(known)}
    latency = [row["latency_seconds"] for row in outputs if type(row.get("latency_seconds")) in (int, float)]
    result["latency_seconds"] = {"reported_total": sum(latency) if latency else None,
                                 "mean": sum(latency) / len(latency) if latency else None, "known_outputs": len(latency)}
    result["reported_cost"] = None
    return result


def evaluate_controlled(predictions: list[dict[str, Any]], references: list[dict[str, Any]], *, allow_mock: bool = False) -> dict[str, Any]:
    """Split-isolated controlled scores; mocks require explicit software mode."""
    if not references or not predictions:
        return {"status": "not_evaluated", "reason": "reference labels or online outputs absent", "scores": None}
    mock = any(row.get("is_mock") or row.get("source") in {"mock", "software_test"} for row in predictions)
    if mock and not allow_mock:
        return {"status": "not_evaluated", "reason": "mock outputs are software tests, not online evaluation", "scores": None}
    reference_map = {row["case_id"]: row for row in references}
    if len(reference_map) != len(references):
        raise ValueError("Duplicate reference case_id")
    if any(row.get("split") not in {"dev", "holdout"} for row in references):
        raise ValueError("Every reference must have an explicit dev/holdout split")
    families: dict[str, set[str]] = {}
    pair_splits: dict[str, set[str]] = {}
    for row in references:
        families.setdefault(row["base_item_id"], set()).add(row["split"])
        if row.get("pair_id"):
            pair_splits.setdefault(row["pair_id"], set()).add(row["split"])
    if any(len(splits) > 1 for splits in [*families.values(), *pair_splits.values()]):
        raise ValueError("Family or minimal pair leaks across dev/holdout")
    indexed: dict[str, dict[str, dict[str, Any]]] = {"direct": {}, "structured": {}}
    for row in predictions:
        protocol = row.get("protocol", row.get("judge_protocol"))
        if protocol not in indexed or row.get("case_id") not in reference_map:
            raise ValueError("Unknown protocol or output case_id")
        case_id = row["case_id"]
        if case_id in indexed[protocol]:
            raise ValueError("Multiple final outputs for one logical request; retries are not new samples")
        reference = reference_map[case_id]
        if row.get("split", reference["split"]) != reference["split"]:
            raise ValueError("Output/reference split mismatch")
        for key in ("case_sha256", "reference_sha256"):
            if row.get(key) is not None and reference.get(key) is not None and row[key] != reference[key]:
                raise ValueError("Output/reference version mismatch")
        indexed[protocol][case_id] = row
    splits = {}
    for split in ("dev", "holdout"):
        refs = [row for row in references if row["split"] == split]
        split_ids = {row["case_id"] for row in refs}
        summaries = {protocol: _summarize({key: row for key, row in rows.items() if key in split_ids}, refs)
                     for protocol, rows in indexed.items()}
        paired_rows = []
        for reference in refs:
            if reference.get("verification_status") not in VERIFIED or _expected(reference, "current_deviation") not in {"yes", "no"}:
                continue
            direct = _prediction(indexed["direct"].get(reference["case_id"]))
            structured = _prediction(indexed["structured"].get(reference["case_id"]))
            if direct is None or structured is None or "uncertain" in (direct["current_deviation"], structured["current_deviation"]):
                continue
            expected = _expected(reference, "current_deviation")
            paired_rows.append({"case_id": reference["case_id"], "base_item_id": reference["base_item_id"],
                                "direct_correct": direct["current_deviation"] == expected,
                                "structured_correct": structured["current_deviation"] == expected})
        deltas = [int(row["structured_correct"]) - int(row["direct_correct"]) for row in paired_rows]
        by_family = {}
        for row in paired_rows:
            by_family.setdefault(row["base_item_id"], []).append(int(row["structured_correct"]) - int(row["direct_correct"]))
        summaries["paired"] = {"both_valid_pairs": len(paired_rows), "eligible_references": summaries["direct"]["eligible_reference_count"],
            "structured_minus_direct_accuracy": sum(deltas) / len(deltas) if deltas else None,
            "family_mean_differences": {key: sum(values) / len(values) for key, values in by_family.items()},
            "rows": paired_rows, "inference": "descriptive only; families/templates are correlated"}
        splits[split] = summaries
    return {"status": "software_test_only" if mock else "evaluated", "matching_version": MATCHING_VERSION,
            "primary_split": "holdout", "splits": splits,
            "scope": "controlled pilot; not natural-MAD semantic validation; no post-hoc pass threshold"}


def evaluate_files(predictions_path: Path, references_path: Path | None, output_path: Path) -> dict[str, Any]:
    predictions = read_jsonl(predictions_path) if predictions_path.exists() else []
    references = read_jsonl(references_path) if references_path is not None and references_path.exists() else []
    result = evaluate_controlled(predictions, references)
    write_json(output_path, result)
    return result
