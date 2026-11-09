"""Program-only answer diagnostics: no inference of semantic F/R/I labels."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .common import LABELS, read_json, write_json, write_jsonl
from .parsing import parse_answer_set
from .state import candidate_rule_states, score_answer


def load_records(result_dir: Path) -> list[dict[str, Any]]:
    """Read only canonical new-run records, not legacy logs or branch views."""
    return [read_json(path) for path in sorted((result_dir / "records").glob("*.json"))]


def analyze_program(plan: list[dict[str, Any]], sequences: list[dict[str, Any]], records: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    """Compare candidate decisions against both the old and current formal states."""
    seqs = {s["sequence_id"]: s for s in sequences}
    plans = {p["message_id"]: p for p in plan}
    by_id: dict[str, Any] = {}
    for record in records:
        if record.get("is_mock"):
            raise ValueError("mock records cannot become real program results")
        mid = record.get("message_id", record.get("request_id"))
        if mid not in plans or mid in by_id or record.get("run_id") != plans[mid]["run_id"]:
            raise ValueError("Unknown, duplicate or foreign-run record")
        by_id[mid] = record
    messages, objects = [], []
    parsed_cache: dict[str, Any] = {}
    for req in plan:
        mid = req["message_id"]
        record = by_id.get(mid)
        if record is None or not record.get("api_success", record.get("status") == "success"):
            continue
        seq = seqs[req["sequence_id"]]
        state = seq["stage_states"][req["evidence_stage"] - 1]
        parsed = parse_answer_set(record.get("raw_response", ""), {c: r["name"] for c, r in seq["candidate_map"].items()})
        parsed_cache[mid] = parsed
        score = score_answer(seq["rules"], state["active_evidence"], parsed["answer_set"])
        prev_id = req["own_previous_message_id"]
        prev = parsed_cache.get(prev_id)
        prior_req = plans.get(prev_id)
        prior_state = seqs[prior_req["sequence_id"]]["stage_states"][prior_req["evidence_stage"] - 1] if prior_req else None
        row = {k: req[k] for k in ("message_id", "family_id", "branch_type", "phase", "agent_id", "evidence_stage", "round")}
        row.update({"parsed": parsed, **score, "candidate_rule_states": candidate_rule_states(seq["rules"], state["active_evidence"]),
                    "prior_answer_rescored_under_current_state": score_answer(seq["rules"], state["active_evidence"], prev["answer_set"]) if prev else None,
                    "semantic_content_labels": None, "semantic_evaluation_status": "not_evaluated"})
        messages.append(row)
        for candidate in LABELS:
            known_now = candidate in state["oracle"]
            selected = candidate in parsed["answer_set"] if parsed["recognized"] else None
            was_selected = candidate in prev["answer_set"] if prev and prev["recognized"] else None
            was_oracle = candidate in prior_state["oracle"] if prior_state else None
            changed = prior_state is not None and was_oracle != known_now
            if selected is None or was_selected is None:
                transition = "unassessable_history_or_answer"
            elif changed:
                transition = "update_adapted_proxy" if selected == known_now else "update_not_adapted_proxy"
            elif was_selected == known_now and selected != known_now:
                transition = "stable_state_decision_degradation_proxy"
            elif was_selected != known_now and selected == known_now:
                transition = "stable_state_decision_repair_proxy"
            else:
                transition = "decision_maintained_proxy"
            objects.append({"message_id": mid, "candidate_id": candidate, "current_selected": selected,
                            "current_oracle_retained": known_now, "prior_selected": was_selected,
                            "prior_oracle_retained": was_oracle, "formal_decision_changed": changed,
                            "transition": transition, "not_a_content_or_causal_drift_label": True})
    counts = Counter(m["answer_status"] for m in messages)
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in messages:
        if row["phase"] == "branch_suffix" and row["answer_status"] != "unrecognized":
            grouped[row["family_id"], row["branch_type"]].append((len(row["extra"]) + len(row["omitted"])) / 4)
    paired = []
    for family in sorted({r["family_id"] for r in plan}):
        means = {b: sum(grouped[family, b]) / len(grouped[family, b]) if len(grouped[family, b]) == 18 else None
                 for b in ("clean", "update", "noise", "update_noise")}
        complete = all(v is not None for v in means.values())
        paired.append({"family_id": family, "candidate_error_rates": means, "complete_suffixes": complete,
                       "noise_minus_clean": means["noise"] - means["clean"] if complete else None,
                       "update_noise_minus_update": means["update_noise"] - means["update"] if complete else None,
                       "interaction": (means["update_noise"] - means["update"]) - (means["noise"] - means["clean"]) if complete else None})
    summary = {"status": "completed" if len(messages) == len(plan) else "not_run" if not records else "partial",
               "planned_unique_requests": len(plan), "observed_api_success": len(messages),
               "parsed": sum(m["parsed"]["recognized"] for m in messages), "answer_status_counts": dict(counts),
               "unique_shared_messages": sum(m["phase"] == "shared_prefix" for m in messages),
               "object_transition_counts": dict(Counter(o["transition"] for o in objects)),
               "semantic_diagnostic_evaluation": "not_evaluated", "family_paired_differences": paired,
               "interpretation": "Program behavior only; shared prefix is counted once; no F/R/I or causal mechanism inferred."}
    write_jsonl(output_dir / "message_diagnostics.jsonl", messages)
    write_jsonl(output_dir / "object_transitions.jsonl", objects)
    write_json(output_dir / "summary.json", summary)
    return summary
