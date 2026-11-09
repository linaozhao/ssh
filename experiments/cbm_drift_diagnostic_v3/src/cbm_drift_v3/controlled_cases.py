"""Scripted controlled diagnostic cases with an independently parsed finite language.

These are engineering reference cases, not natural model outputs or human labels.
The verifier interprets the statements and replays evidence rather than trusting
the intended mutation or expected class. Its grammar is deliberately restricted.
"""

from __future__ import annotations

import copy
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .common import LABELS, freeze_json, freeze_jsonl, sha256_json
from .state import replay_evidence, solve_candidate_set, score_answer

STRATA = ("known_fact_contradiction", "unsupported_assertion", "rule_change", "inference_error",
          "quoted_then_rejected", "hypothetical_only", "reasonable_update", "correct_answer_wrong_basis",
          "correct_answer_stale_basis", "wrong_answer_unresolved", "correct_maintenance", "multi_claim")
TIMES = (("initial_error", "newly_introduced", "persistent"),
         ("initial_error", "uncertain", "persistent"),
         ("newly_introduced", "recurrence", "uncertain"),
         ("initial_error", "persistent", "newly_introduced"),
         ("corrected", "corrected", "correct_maintenance"),
         ("correct_maintenance",) * 3, ("reasonable_update",) * 3,
         ("uncertain", "initial_error", "newly_introduced"),
         ("post_update_reversion", "post_update_reversion", "update_failure"),
         ("post_update_reversion", "update_failure", "uncertain"),
         ("correct_maintenance",) * 3, ("initial_error", "persistent", "newly_introduced"))
FACT = re.compile(r"The value of (\w+) for candidate ([ABCD]) is (true|false|unknown)\.")
RULE = re.compile(r"Rule (C\d+) requires (\w+) to be (true|false)\.")
CONCLUSION = re.compile(r"Therefore candidate ([ABCD]) should be (retained|excluded)\.")


def _state(sequence: dict[str, Any], stage: int) -> dict[str, Any]:
    events = [e for s in sequence["stages"][:stage] for e in s["events"]]
    state = replay_evidence(events)
    return {**state, **solve_candidate_set(sequence["rules"], state["active_evidence"])}


def _fact(attribute: str, candidate: str, value: bool | None) -> str:
    return f"The value of {attribute} for candidate {candidate} is {'unknown' if value is None else str(value).lower()}."


def _rule(rule: dict[str, Any], value: bool | None = None) -> str:
    return f"Rule {rule['id']} requires {rule['attribute']} to be {str(rule['required_value'] if value is None else value).lower()}."


def _message(mid: str, stage: int, round_id: int, explanation: str, answer: list[str], previous: str | None) -> dict[str, Any]:
    return {"message_id": mid, "agent_id": "agent_1", "evidence_stage": stage, "round": round_id,
            "text": json.dumps({"answer_set": answer, "explanation": explanation}, ensure_ascii=False),
            "own_previous_message_id": previous, "visible_peer_message_ids": [],
            "parent_message_ids": [previous] if previous else []}


def _span(text: str, quote: str) -> dict[str, Any]:
    if text.count(quote) != 1:
        raise ValueError("Controlled quote must have a unique exact occurrence")
    start = text.index(quote)
    return {"quote": quote, "start": start, "end": start + len(quote)}


def _observed(case: dict[str, Any], message: dict[str, Any]) -> dict[str, Any]:
    events = [e for e in case["evidence"] if e["appearance_stage"] <= message["evidence_stage"]]
    state = replay_evidence(events)
    active = {(e["candidate_id"], e["attribute"]): e for e in state["active_evidence"] if e["fact_kind"] == "target"}
    return {**state, **solve_candidate_set(case["rules"], state["active_evidence"]), "facts": active}


def inspect_message(case: dict[str, Any], message: dict[str, Any]) -> dict[str, Any]:
    """Interpret restricted statements independently of all expected references."""
    raw = message["text"]
    parsed = json.loads(raw)
    explanation = parsed["explanation"]
    state = _observed(case, message)
    rules = {r["id"]: r for r in case["rules"]}
    stance = "rejected" if "I reject that claim." in explanation else "hypothetical" if "This is only a hypothetical" in explanation else "asserted"
    claims = []
    for match in FACT.finditer(explanation):
        attr, candidate, word = match.groups()
        fact = state["facts"].get((candidate, attr))
        value = None if word == "unknown" else word == "true"
        wrong = (value is not None) if fact is None else value != fact["value"]
        if stance != "asserted":
            wrong = False
        claims.append({**_span(raw, match[0]), "candidate_ids": [candidate], "attribute": attr,
                       "rule_ids": [], "content_labels": ["F"] if wrong else [],
                       "current_deviation": "yes" if wrong else "no", "stance": stance,
                       "conflicting_evidence_ids": [fact["evidence_id"]] if fact else [],
                       "evidence_version": fact["evidence_id"] if fact else None,
                       "deviation_kind": "unsupported_assertion" if wrong and fact is None else "known_fact_contradiction" if wrong else None})
    for match in RULE.finditer(explanation):
        rid, attribute, word = match.groups()
        rule = rules.get(rid)
        wrong = rule is None or attribute != rule["attribute"] or (word == "true") != rule["required_value"]
        claims.append({**_span(raw, match[0]), "candidate_ids": [], "attribute": attribute, "rule_ids": [rid],
                       "content_labels": ["R"] if wrong else [], "current_deviation": "yes" if wrong else "no",
                       "stance": "asserted", "conflicting_evidence_ids": [], "evidence_version": None})
    for match in CONCLUSION.finditer(explanation):
        candidate, decision = match.groups()
        # An I claim requires explicit correct facts AND the corresponding fixed rule.
        premises = [c for c in claims if c["candidate_ids"] == [candidate] and not c["content_labels"] and c["stance"] == "asserted"]
        rule_premises = [c for c in claims if c["rule_ids"] and not c["content_labels"]]
        valid_premises = any(p["attribute"] == r["attribute"] for p in premises for r in rule_premises)
        wrong = valid_premises and ((decision == "retained") != (candidate in state["oracle"]))
        if wrong:
            fact_premise = next(p for p in premises if any(p["attribute"] == r["attribute"] for r in rule_premises))
            rule_premise = next(r for r in rule_premises if r["attribute"] == fact_premise["attribute"])
            claims.append({**_span(raw, match[0]), "candidate_ids": [candidate], "attribute": fact_premise["attribute"],
                           "rule_ids": rule_premise["rule_ids"], "content_labels": ["I"], "current_deviation": "yes",
                           "stance": "asserted", "conflicting_evidence_ids": fact_premise["conflicting_evidence_ids"],
                           "evidence_version": fact_premise["evidence_version"]})
    scored = score_answer(case["rules"], state["active_evidence"], parsed["answer_set"])
    labels = sorted({label for c in claims for label in c["content_labels"]})
    if scored["answer_status"] == "incorrect" and not labels:
        labels = ["unresolved"]
    return {"current_deviation": "yes" if labels else "no", "content_labels": labels,
            "answer_status": scored["answer_status"], "claims": claims, "state": state, "answer_set": parsed["answer_set"]}


def temporal_from_history(case: dict[str, Any], object_spec: dict[str, Any]) -> str:
    """Classify a single public object from explicit scripted observations only."""
    trace = case["history"] + [case["target_message"]]
    readings = []
    for message in trace:
        observed = inspect_message(case, message)
        if object_spec["kind"] == "decision":
            candidate = object_spec["candidate"]
            actual = candidate in observed["state"]["oracle"]
            wrong = (candidate in observed["answer_set"]) != actual
        elif object_spec["kind"] == "rule":
            found = [c for c in observed["claims"] if object_spec["rule_id"] in c["rule_ids"] and not c["candidate_ids"]]
            if not found:
                continue
            actual = next(r["required_value"] for r in case["rules"] if r["id"] == object_spec["rule_id"])
            wrong = bool(found[0]["content_labels"])
        else:
            found = [c for c in observed["claims"] if c["candidate_ids"] == [object_spec["candidate"]] and c["attribute"] == object_spec["attribute"] and not c["rule_ids"]]
            if not found:
                continue
            fact = observed["state"]["facts"].get((object_spec["candidate"], object_spec["attribute"]))
            actual = fact["value"] if fact else None
            wrong = any(c["current_deviation"] == "yes" for c in found)
        readings.append((actual, wrong, message["evidence_stage"]))
    if not case["history_scope"]["complete"] or not readings:
        return "uncertain"
    actual, wrong, stage = readings[-1]
    prior = readings[:-1]
    if not prior:
        return "initial_error" if wrong else "correct_maintenance"
    changes = [i for i in range(1, len(readings)) if readings[i][0] != readings[i - 1][0]]
    if changes:
        change = changes[-1]
        adapted = any(not r[1] and r[0] == actual for r in readings[change:-1])
        if wrong and adapted:
            return "post_update_reversion"
        if wrong:
            return "update_failure"
        if change == len(readings) - 1:
            return "reasonable_update"
    if wrong:
        if prior[-1][1]:
            return "persistent"
        return "recurrence" if any(r[1] for r in prior) else "newly_introduced"
    return "corrected" if prior[-1][1] and prior[-1][0] == actual else "correct_maintenance"


def build_controlled(sequences: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    """Freeze 72 cases across six dev and six holdout source families."""
    by_key = {(s["family_id"], s["branch_type"]): s for s in sequences}
    families = sorted({s["family_id"] for s in sequences})
    if len(families) != 12:
        raise ValueError("Exactly twelve frozen families required")
    # Alternating sorted families is deterministic and never reads model results.
    split_families = {"dev": families[::2], "holdout": families[1::2]}
    cases, references = [], []
    for split, pool in split_families.items():
        for si, stratum in enumerate(STRATA):
            for rep in range(3):
                family = pool[(si + rep) % 6]
                temporal = TIMES[si][rep]
                updating = si in (6, 8) or (si == 9 and temporal != "uncertain")
                seq = by_key[family, "update" if updating else "clean"]
                stage = 4 if updating else 1 if si in (1, 10) else 3
                state = _state(seq, stage)
                facts = [e for e in state["active_evidence"] if e["fact_kind"] == "target"]
                rules = {r["attribute"]: r for r in seq["rules"]}
                if updating:
                    fact = next(e for e in facts if e["event_type"] == "correction")
                elif si == 3:
                    fact = next(e for e in facts if e["value"] != rules[e["attribute"]]["required_value"])
                else:
                    fact = facts[rep % len(facts)]
                candidate, attr = fact["candidate_id"], fact["attribute"]
                if si in (1, 10):
                    known = {(e["candidate_id"], e["attribute"]) for e in facts}
                    candidate, attr = next((c, r["attribute"]) for c in LABELS for r in seq["rules"] if (c, r["attribute"]) not in known)
                    fact = None
                rule = rules[attr]
                actual = fact["value"] if fact else None
                good = _fact(attr, candidate, actual)
                bad = _fact(attr, candidate, not actual if actual is not None else True)
                object_spec = {"kind": "fact", "candidate": candidate, "attribute": attr}
                answer = list(state["oracle"])
                clauses: list[tuple[str, list[str], list[str], str | None, list[str], str, str | None]] = []
                # Each tuple is a hand-specified reference, separately parsed below.
                def add(quote: str, labels: list[str], candidates: list[str], attribute: str | None,
                        rule_ids: list[str], stance: str = "asserted", evidence: str | None = None) -> None:
                    clauses.append((quote, labels, candidates, attribute, rule_ids, stance, evidence))
                if si in (0, 1, 7, 8):
                    explanation = bad
                    add(bad, ["F"], [candidate], attr, [], evidence=fact["evidence_id"] if fact else None)
                elif si == 2:
                    good, bad = _rule(rule), _rule(rule, not rule["required_value"])
                    explanation = bad
                    object_spec = {"kind": "rule", "rule_id": rule["id"]}
                    add(bad, ["R"], [], attr, [rule["id"]])
                elif si == 3:
                    conclusion = f"Therefore candidate {candidate} should be retained."
                    explanation = f"{good} {_rule(rule)} {conclusion}"
                    add(conclusion, ["I"], [candidate], attr, [rule["id"]], evidence=fact["evidence_id"])
                    answer = sorted(set(answer) | {candidate})
                    object_spec = {"kind": "decision", "candidate": candidate}
                    bad = explanation
                    good = f"{good} {_rule(rule)} Therefore candidate {candidate} should be excluded."
                elif si == 4:
                    explanation = f"Consider this claim: {bad} I reject that claim. The active evidence supports the opposite value."
                    add(bad, [], [candidate], attr, [], "rejected", fact["evidence_id"])
                    good = explanation
                elif si == 5:
                    explanation = f"Suppose the following: {bad} This is only a hypothetical; it is not a statement about the candidate."
                    add(bad, [], [candidate], attr, [], "hypothetical", fact["evidence_id"])
                    good = explanation
                elif si == 6:
                    explanation = f"{good} The named correction supersedes the previous report."
                    add(good, [], [candidate], attr, [], evidence=fact["evidence_id"])
                elif si == 9:
                    explanation = "This is my answer."
                    answer = sorted(set(answer) ^ {candidate})
                    object_spec = {"kind": "decision", "candidate": candidate}
                    good = bad = explanation
                elif si == 10:
                    explanation = f"{good} Unknown is not grounds for elimination."
                    add(good, [], [candidate], attr, [])
                    good = explanation
                else:
                    other_rule = next(r for r in seq["rules"] if r["attribute"] != attr)
                    bad_rule = _rule(other_rule, not other_rule["required_value"])
                    bad_fact = bad
                    explanation = f"{bad} {bad_rule}"
                    good = f"{good} {_rule(other_rule)}"
                    bad = explanation
                    add(bad_fact, ["F"], [candidate], attr, [], evidence=fact["evidence_id"])
                    add(bad_rule, ["R"], [], other_rule["attribute"], [other_rule["id"]])
                if si == 0:
                    answer = sorted(set(answer) ^ {candidate})
                cid = "case_" + sha256_json([family, split, si, rep, "r2-v1"])[:16]
                history = []
                def past(s: int, r: int, text: str, values: list[str] | None = None) -> None:
                    previous = history[-1]["message_id"] if history else None
                    history.append(_message(f"{cid}:m{len(history)}", s, r, text, values if values is not None else _state(seq, s)["oracle"], previous))
                target_round = 0
                if temporal in ("newly_introduced", "persistent", "corrected", "correct_maintenance"):
                    wrong_before = temporal in ("persistent", "corrected")
                    prior_answer = sorted(set(_state(seq, stage)["oracle"]) ^ {candidate}) if wrong_before and object_spec["kind"] == "decision" else None
                    past(stage, 0, bad if wrong_before else good, prior_answer)
                    target_round = 1
                elif temporal == "recurrence":
                    past(stage, 0, bad)
                    past(stage, 1, good)
                    target_round = 2
                elif temporal in ("post_update_reversion", "update_failure", "reasonable_update"):
                    old_state = _state(seq, 3)
                    old = next(e for e in old_state["active_evidence"] if e.get("candidate_id") == candidate and e.get("attribute") == attr)
                    past(3, 2, _fact(attr, candidate, old["value"]), old_state["oracle"])
                    if temporal == "post_update_reversion":
                        past(4, 0, good, state["oracle"])
                        past(4, 1, good, state["oracle"])
                        target_round = 2
                target = _message(f"{cid}:target", stage, target_round, explanation, answer,
                                  history[-1]["message_id"] if history else None)
                if split == "holdout":
                    target = _message(target["message_id"], stage, target_round,
                                      "My current assessment follows. " + explanation, answer,
                                      target["own_previous_message_id"])
                case = {"case_id": cid, "base_item_id": seq["base_item_id"], "family_id": family,
                        "split": split, "schema_version": "controlled-r2-v1", "branch_type": seq["branch_type"],
                        "task_text": seq["task_text"], "candidate_map": copy.deepcopy(seq["candidate_map"]),
                        "rules": copy.deepcopy(seq["rules"]), "evidence": [copy.deepcopy(e) for s in seq["stages"][:stage] for e in s["events"]],
                        "history_source": "scripted", "history_scope": {"complete": temporal != "uncertain",
                            "trajectory_start": history[0]["message_id"] if history else target["message_id"] if temporal != "uncertain" else None,
                            "scope": "own explicit judgments on the target object; no peer attribution"},
                        "history": history, "target_message": target}
                case["case_sha256"] = sha256_json(case)
                ref_claims = []
                for quote, labels, candidates, attribute, rids, stance, eid in clauses:
                    prior_support = []
                    for h in history:
                        text = json.loads(h["text"])["explanation"]
                        pattern = RULE if not candidates and rids else FACT
                        matches = [m[0] for m in pattern.finditer(text)
                                   if (not candidates and rids and m[1] in rids)
                                   or (candidates and m[1] == attribute and m[2] in candidates)]
                        prior_support.extend({"message_id": h["message_id"], **_span(h["text"], q)} for q in matches)
                    ref_claims.append({**_span(target["text"], quote), "stance": stance, "candidate_ids": candidates,
                                       "attribute": attribute, "rule_ids": rids, "content_labels": labels,
                                       "current_deviation": "yes" if labels else "no", "conflicting_evidence_ids": [eid] if eid else [],
                                       "evidence_version": eid, "prior_support": prior_support,
                                       "acceptable_equivalent_support": [], "temporal_status": temporal,
                                       "deviation_kind": "unsupported_assertion" if si == 1 else None})
                labels = sorted({l for c in ref_claims for l in c["content_labels"]}) or (["unresolved"] if si == 9 else [])
                reference = {"case_id": cid, "pair_id": None, "base_item_id": seq["base_item_id"], "split": split,
                             "primary_stratum": stratum, "history_source": "scripted", "source_state_id": f"{seq['sequence_id']}:T{stage}",
                             "target_message_id": target["message_id"], "agent_id": "agent_1", "evidence_stage": stage, "round": target_round,
                             "expected_current_deviation": "yes" if labels else "no", "expected_content_labels": labels,
                             "expected_temporal_status": temporal, "expected_update_response": "reverted" if temporal == "post_update_reversion" else "not_adapted" if temporal == "update_failure" else "adapted" if temporal == "reasonable_update" else "not_applicable",
                             "expected_answer_status": "incorrect" if si in (0, 3, 9) else "correct",
                             "claims": ref_claims, "temporal_object": object_spec, "history_sufficient": temporal != "uncertain",
                             "reference_source": "scripted_restricted_language_program_reference", "verification_status": "pending",
                             "reviewer_id": None, "review_notes": "Not independently human annotated; finite-language program check only.",
                             "changed_factor": "multiple_objects" if si == 11 else stratum, "changed_span": [c["quote"] for c in ref_claims],
                             "template_lineage": "finite-assertion-r2-v1", "case_sha256": case["case_sha256"], "schema_version": "controlled-r2-v1"}
                errors = _validate_one(case, reference)
                reference["verification_status"] = "program_verified" if not errors else "pending"
                reference["verification_errors"] = errors
                reference["reference_sha256"] = sha256_json(reference)
                cases.append(case)
                references.append(reference)
    report = validate_controlled(cases, references)
    freeze_jsonl(output_dir / "cases.jsonl", cases)
    freeze_jsonl(output_dir / "expected_labels.jsonl", references)
    freeze_json(output_dir / "split_manifest.json", {"families": split_families, "rule": "sorted family IDs alternated; no model outcomes used", "case_split": {c["case_id"]: c["split"] for c in cases}})
    freeze_json(output_dir / "coverage_manifest.json", report["coverage"])
    freeze_json(output_dir / "reference_validation.json", report)
    freeze_json(output_dir / "freeze_manifest.json", {"cases_sha256": sha256_json(cases), "references_sha256": sha256_json(references),
                "builder_sha256": __import__("hashlib").sha256(Path(__file__).read_bytes()).hexdigest(),
                "template_similarity_limitation": "dev and holdout share finite language; family-disjoint is not template-independent"})
    return report


def _validate_one(case: dict[str, Any], reference: dict[str, Any]) -> list[str]:
    errors = []
    target = case["target_message"]
    actual = inspect_message(case, target)
    for key in ("current_deviation", "content_labels", "answer_status"):
        if actual[key] != reference["expected_" + key]:
            errors.append(f"independent {key}: {actual[key]} != {reference['expected_' + key]}")
    temporal = temporal_from_history(case, reference["temporal_object"])
    if temporal != reference["expected_temporal_status"]:
        errors.append(f"independent temporal: {temporal}")
    by_id = {}
    for message in case["history"] + [target]:
        if message["message_id"] in by_id:
            errors.append("duplicate message identity")
        previous = message.get("own_previous_message_id")
        if previous is not None:
            prior = by_id.get(previous)
            if prior is None or (prior["evidence_stage"], prior["round"]) >= (message["evidence_stage"], message["round"]):
                errors.append("illegal own history or future reference")
        by_id[message["message_id"]] = message
    for claim in reference["claims"]:
        if target["text"][claim["start"]:claim["end"]] != claim["quote"]:
            errors.append("quote offset mismatch")
        comparable = [c for c in actual["claims"] if c["quote"] == claim["quote"]]
        if len(comparable) != 1 or any(comparable[0][k] != claim[k] for k in ("content_labels", "candidate_ids", "attribute", "rule_ids", "stance", "conflicting_evidence_ids", "evidence_version")):
            errors.append("claim object, stance or formal relation mismatch")
        if claim["content_labels"] == ["R"]:
            if temporal_from_history(case, {"kind": "rule", "rule_id": claim["rule_ids"][0]}) != claim["temporal_status"]:
                errors.append("rule claim temporal history mismatch")
        for support in claim["prior_support"]:
            prior = by_id.get(support["message_id"])
            if not prior or prior["text"][support["start"]:support["end"]] != support["quote"]:
                errors.append("invalid historical quote")
    return errors


def validate_controlled(cases: list[dict[str, Any]], references: list[dict[str, Any]]) -> dict[str, Any]:
    """Check every reference, immutable digest and independent coverage axis."""
    errors = []
    by_id = {c["case_id"]: c for c in cases}
    if len(by_id) != len(cases) or len(cases) != 72 or len(references) != 72:
        errors.append("expected72 unique cases and references")
    if len({r["case_id"] for r in references}) != 72 or set(by_id) != {r["case_id"] for r in references}:
        errors.append("reference identities do not match")
    coverage = {}
    verified = 0
    family_sets = {}
    for split in ("dev", "holdout"):
        refs = [r for r in references if r["split"] == split]
        strata = Counter(r["primary_stratum"] for r in refs)
        times = Counter(r["expected_temporal_status"] for r in refs)
        family_sets[split] = {by_id[r["case_id"]]["family_id"] for r in refs}
        coverage[split] = {"total": len(refs), "families": sorted(family_sets[split]), "strata": dict(strata), "temporal": dict(times)}
        if len(refs) != 36 or len(family_sets[split]) != 6 or any(strata[s] != 3 for s in STRATA):
            errors.append(f"{split}: primary coverage failure")
        for status in ("initial_error", "newly_introduced", "persistent", "corrected", "post_update_reversion", "update_failure", "uncertain"):
            if times[status] < 2:
                errors.append(f"{split}: time coverage missing {status}")
    if family_sets["dev"] & family_sets["holdout"]:
        errors.append("family leakage")
    for ref in references:
        case = by_id[ref["case_id"]]
        found = _validate_one(case, ref)
        if case["case_sha256"] != sha256_json({k: v for k, v in case.items() if k != "case_sha256"}):
            found.append("case hash mismatch")
        if ref.get("reference_sha256") != sha256_json({k: v for k, v in ref.items() if k != "reference_sha256"}):
            found.append("reference hash mismatch")
        if any(k.startswith("expected_") or k in {"primary_stratum", "mutation_type"} for k in case):
            found.append("reference leaked into case")
        if not found and ref["verification_status"] == "program_verified":
            verified += 1
        errors.extend(f"{ref['case_id']}: {e}" for e in found)
    return {"status": "passed" if not errors and verified == 72 else "failed", "built": len(cases), "verified": verified,
            "human_verified": 0, "errors": errors, "coverage": coverage, "reference_scope": "restricted scripted language only",
            "online_controlled_evaluation": "not_evaluated"}
