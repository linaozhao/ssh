"""Controlled-only Judge queue, credential gate and auditable bounded transport."""

from __future__ import annotations

import copy
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .common import freeze_json, freeze_jsonl, read_json, read_jsonl, sha256_json, sha256_file, write_json, write_jsonl
from .parsing import parse_answer_set
from .state import replay_evidence, score_answer, candidate_rule_states

RUBRIC = """Diagnose only public statements, not hidden cognition or peer-caused mechanisms.
Separate current answer correctness, current observable deviation, content classes, and object-specific time status.
F: an asserted fact contradicts currently active evidence. An unknown fact asserted as known is F with
deviation_kind=unsupported_assertion, not a contradiction of an observed fact. Do not retroactively mark an old
statement false before its formal correction.
R: an explicitly asserted change to a fixed requirement's direction, content or conjunction. A wrong answer
alone does not prove R.
I: explicitly stated relevant factual and rule premises are correct, but the conclusion/application is not
supported. Do not mechanically add I when the same error is explained by false facts or altered rules.
unresolved: a definite wrong answer or visible anomaly whose text does not support a unique F/R/I class.
Classes may co-occur on different claims. Correct answers may have incorrect or superseded explanations.
For each quote distinguish asserted, quoted, rejected, hypothetical, uncertain. Rejecting a quoted false claim
or making a hypothesis without adopting it is not a factual deviation. Unknown is not grounds for elimination.
Time is object-specific and based on the speaker's own visible judgments:
initial_error requires the known beginning of the defined object trajectory;
newly_introduced requires previously explicit correctness on that object and unchanged relevant state;
persistent requires an earlier same-object error and sufficient intervening history;
corrected requires actual repair, not merely a changed oracle making an old answer accidentally correct;
recurrence requires error, repair, then error again;
post_update_reversion requires pre-update, a correctly adapted post-update judgment, and later reversion while
that state remains unchanged; update_failure is failure to adapt without demonstrated adaptation first;
reasonable_update is a justified response to formal correction; correct_maintenance is justified stability.
Missing necessary history means temporal_status=uncertain, not initial/new/persistent/reversion by default.
Quote exact current text and necessary historical text, name the candidate/attribute/rule separately for each
claim, and cite evidence versions. A cited withdrawn fact used as an object of criticism is allowed; distinguish
cited_evidence_ids from conflicting_evidence_ids. Do not infer adoption causality from answer agreement.
For multi-object messages keep claim-local labels and time status; overall time summarizes the main documented
event, or uncertain if incompatible. Offset fields are computed by the program from unique exact quotes.
Return only one JSON object under the supplied schema. No additional extractor calls are performed."""

TEMPORAL = {"initial_error", "newly_introduced", "persistent", "corrected", "recurrence", "post_update_reversion",
            "update_failure", "reasonable_update", "correct_maintenance", "uncertain"}
SCHEMA = {"current_deviation": "yes/no/uncertain", "answer_status": "correct/incorrect/unrecognized",
          "content_labels": ["F/R/I/unresolved"], "temporal_status": "/".join(sorted(TEMPORAL)),
          "update_response": "adapted/reverted/not_adapted/not_applicable/uncertain", "uncertainty_reason": "string or null",
          "claims": [{"quote": "unique exact current-text substring", "stance": "asserted/quoted/rejected/hypothetical/uncertain",
                      "candidate_ids": [], "attribute": None, "rule_ids": [], "content_labels": [],
                      "current_deviation": "yes/no/uncertain", "temporal_status": "same enum as overall",
                      "deviation_kind": "unsupported_assertion or null", "conflicting_evidence_ids": [],
                      "cited_evidence_ids": [], "evidence_version": None,
                      "prior_support": [{"message_id": "visible own/peer message ID", "quote": "unique exact historical substring"}]}]}


def render_package(case: dict[str, Any], protocol: str) -> dict[str, Any]:
    """Allowlist inputs; reference files and split/mutation metadata are never read."""
    if protocol not in {"direct", "structured"}:
        raise ValueError("Unknown Judge protocol")
    package = {k: copy.deepcopy(case[k]) for k in ("task_text", "candidate_map", "rules", "evidence", "history_source", "history_scope", "history", "target_message")}
    if protocol == "structured":
        state = replay_evidence(case["evidence"])
        target = case["target_message"]
        parsed = parse_answer_set(target["text"], {c: v["name"] for c, v in case["candidate_map"].items()})
        scored = score_answer(case["rules"], state["active_evidence"], parsed["answer_set"])
        assistance = {**state, **scored, "candidate_rule_states": candidate_rule_states(case["rules"], state["active_evidence"])}
        if case["history"]:
            previous = case["history"][-1]
            prior_state = replay_evidence([e for e in case["evidence"] if e["appearance_stage"] <= previous["evidence_stage"]])
            prior_answer = parse_answer_set(previous["text"], {c: v["name"] for c, v in case["candidate_map"].items()})["answer_set"]
            assistance["previous_answer_rescored_current"] = score_answer(case["rules"], state["active_evidence"], prior_answer)
            assistance["previous_state_score"] = score_answer(case["rules"], prior_state["active_evidence"], prior_answer)
        package["reference_structure_assistance"] = assistance
    return package


def prepare_controlled_judge(cases: list[dict[str, Any]], config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Prepare exactly144 logical requests; unverified provider ID stays pending."""
    if len(cases) != 72 or len({c["case_id"] for c in cases}) != 72:
        raise ValueError("72 unique targets required")
    if any(sum(c["split"] == s for c in cases) != 36 for s in ("dev", "holdout")):
        raise ValueError("Expected36/36 family-disjoint split")
    dev = sorted((c for c in cases if c["split"] == "dev"), key=lambda c: c["case_id"])
    selected = []
    # Technical coverage from input shape, not from correctness or expected labels.
    predicates = [lambda c: len(c["history"]) >= 3,
                  lambda c: any(e["event_type"] == "correction" for e in c["evidence"]),
                  lambda c: "I reject that claim" in c["target_message"]["text"],
                  lambda c: "hypothetical" in c["target_message"]["text"],
                  lambda c: "Rule " in c["target_message"]["text"] and "The value of" in c["target_message"]["text"],
                  lambda c: not c["history_scope"]["complete"]]
    for predicate in predicates:
        selected.append(next(c["case_id"] for c in dev if predicate(c) and c["case_id"] not in selected))
    packages, queue = [], []
    fingerprint = sha256_json({"config": config, "rubric": RUBRIC, "schema": SCHEMA,
                               "cases": [(c["case_id"], c["case_sha256"]) for c in cases]})
    for case in sorted(cases, key=lambda c: (c["split"] != "dev", c["case_id"] not in selected, c["case_id"])):
        for protocol in ("direct", "structured"):
            package = render_package(case, protocol)
            messages = [{"role": "system", "content": RUBRIC},
                        {"role": "user", "content": json.dumps({"materials": package, "required_schema": SCHEMA}, ensure_ascii=False)}]
            rid = "judge_" + sha256_json([case["case_sha256"], protocol, fingerprint])[:24]
            row = {"request_id": rid, "case_id": case["case_id"], "case_sha256": case["case_sha256"],
                   "split": case["split"], "protocol": protocol, "preflight": case["case_id"] in selected,
                   "experiment_fingerprint": fingerprint, "messages_sha256": sha256_json(messages),
                   "status": "pending", "model_verification_status": config["model_verification_status"]}
            queue.append(row)
            packages.append({"request_id": rid, "messages": messages, "package": package})
    freeze_jsonl(output_dir / "request_queue.jsonl", queue)
    freeze_jsonl(output_dir / "input_packages.jsonl", packages)
    freeze_jsonl(output_dir / "preflight_manifest.jsonl", [r for r in queue if r["preflight"]])
    freeze_json(output_dir / "experiment_manifest.json", {"fingerprint": fingerprint, "config": config,
                "rubric_sha256": sha256_json(RUBRIC), "schema_sha256": sha256_json(SCHEMA),
                "formal_unique_requests": 144, "preflight_subset_requests": 12,
                "development_debug_budget": 0, "extractor_budget": 0, "real_queue_enabled": False})
    return {"status": "prepared", "formal_unique_requests": len(queue), "preflight_requests": 12,
            "dev_requests": 72, "holdout_requests": 72, "experiment_fingerprint": fingerprint}


def credential_gate(config: dict[str, Any], *, enabled: bool) -> dict[str, Any]:
    """Never read chat/old environment keys; never log a credential or its hash."""
    if config.get("api_key_env") != "JUDGE_API_KEY_V3_NEW" or config.get("allow_legacy_key_fallback"):
        raise ValueError("Only the new server-local credential is permitted")
    present = bool(os.environ.get("JUDGE_API_KEY_V3_NEW"))
    result = {"credential_source": "server_local_new", "configured": present, "online_explicitly_enabled": enabled,
              "allowed": False, "credential_check_status": "not_authenticated"}
    if not present:
        return result | {"status": "not_run_missing_new_credentials"}
    if not enabled:
        return result | {"status": "not_run_not_enabled"}
    if not config.get("model_name") or config.get("model_verification_status") != "verified":
        return result | {"status": "blocked_unverified_requested_model"}
    return result | {"allowed": True, "status": "ready_for_authenticated_preflight"}


def validate_prediction(value: Any, package: dict[str, Any]) -> dict[str, Any]:
    """Schema, quotes/IDs, and computable relations are separate audit levels."""
    errors, quote_errors, object_errors, formal_errors = [], [], [], []
    def member(value: Any, choices: set[str]) -> bool:
        return isinstance(value, str) and value in choices
    if not isinstance(value, dict):
        return {"schema_valid": False, "quote_valid": False, "object_valid": False, "formal_valid": False, "errors": ["not an object"], "prediction": None}
    normalized = copy.deepcopy(value)
    for key in SCHEMA:
        if key not in value:
            errors.append(f"missing {key}")
    if not member(value.get("current_deviation"), {"yes", "no", "uncertain"}):
        errors.append("invalid current_deviation")
    if not member(value.get("answer_status"), {"correct", "incorrect", "unrecognized"}):
        errors.append("invalid answer_status")
    if not member(value.get("temporal_status"), TEMPORAL):
        errors.append("invalid temporal_status")
    if not member(value.get("update_response"), {"adapted", "reverted", "not_adapted", "not_applicable", "uncertain"}):
        errors.append("invalid update_response")
    if value.get("uncertainty_reason") is not None and not isinstance(value.get("uncertainty_reason"), str):
        errors.append("invalid uncertainty_reason")
    def labels_ok(labels: Any) -> bool:
        return isinstance(labels, list) and all(x in ("F", "R", "I", "unresolved") for x in labels) and len(labels) == len(set(labels))
    if not labels_ok(value.get("content_labels")):
        errors.append("invalid labels")
    claims = normalized.get("claims")
    if not isinstance(claims, list):
        errors.append("invalid claims")
        claims = []
    target = package["target_message"]
    history = {m["message_id"]: m for m in package["history"]}
    evidence = {e["evidence_id"]: e for e in package["evidence"]}
    active = {e["evidence_id"] for e in replay_evidence(package["evidence"])["active_evidence"]}
    rules = {r["id"]: r for r in package["rules"]}
    def offset(quote: Any, text: str) -> dict[str, int] | None:
        if not isinstance(quote, str) or not quote or text.count(quote) != 1:
            return None
        start = text.index(quote)
        return {"start": start, "end": start + len(quote)}
    for claim in claims:
        if not isinstance(claim, dict):
            errors.append("nonobject claim")
            continue
        required = {"quote", "stance", "candidate_ids", "attribute", "rule_ids", "content_labels", "current_deviation", "temporal_status", "conflicting_evidence_ids", "cited_evidence_ids", "evidence_version", "prior_support"}
        if not required <= set(claim) or not labels_ok(claim.get("content_labels")):
            errors.append("claim schema incomplete")
        span = offset(claim.get("quote"), target["text"])
        if span is None:
            quote_errors.append("missing or ambiguous current quote")
        else:
            if any(k in claim and claim[k] != span[k] for k in span):
                quote_errors.append("wrong supplied offset")
            claim.update(span)
        if not member(claim.get("stance"), {"asserted", "quoted", "rejected", "hypothetical", "uncertain"}):
            errors.append("invalid stance")
        for key, allowed in (("candidate_ids", package["candidate_map"]), ("rule_ids", rules), ("conflicting_evidence_ids", evidence), ("cited_evidence_ids", evidence)):
            values = claim.get(key, [])
            if not isinstance(values, list) or any(not isinstance(x, str) or x not in allowed for x in values):
                object_errors.append(f"invalid {key}")
        if claim.get("attribute") is not None and (not isinstance(claim["attribute"], str) or claim["attribute"] not in {r["attribute"] for r in package["rules"]}):
            object_errors.append("unknown attribute")
        if not member(claim.get("current_deviation"), {"yes", "no", "uncertain"}) or not member(claim.get("temporal_status"), TEMPORAL):
            errors.append("invalid claim deviation/time")
        version = claim.get("evidence_version")
        # Evidence records expose both an integer version and a full ID. Resolve
        # an integer only through explicitly cited, uniquely matching evidence.
        if type(version) is int:
            references = claim.get("conflicting_evidence_ids", []) + claim.get("cited_evidence_ids", []) if all(
                isinstance(claim.get(k), list) for k in ("conflicting_evidence_ids", "cited_evidence_ids")) else []
            matches = {eid for eid in references if isinstance(eid, str) and eid in evidence
                       and evidence[eid].get("version") == version
                       and (not claim.get("attribute") or evidence[eid].get("attribute") == claim["attribute"])
                       and (not claim.get("candidate_ids") or evidence[eid].get("candidate_id") in claim["candidate_ids"])}
            if len(matches) == 1:
                claim["raw_evidence_version"] = version
                version = claim["evidence_version"] = next(iter(matches))
                claim["evidence_version_resolution"] = "unique_explicit_reference"
        if version is not None and (not isinstance(version, str) or version not in evidence):
            object_errors.append("invalid evidence version")
        if isinstance(claim.get("conflicting_evidence_ids"), list):
            if version is not None and claim["conflicting_evidence_ids"] and version not in claim["conflicting_evidence_ids"]:
                formal_errors.append("version does not identify conflict basis")
            for eid in claim["conflicting_evidence_ids"]:
                if isinstance(eid, str) and eid in evidence:
                    e = evidence[eid]
                    if eid not in active:
                        formal_errors.append("conflict basis is superseded; cited-only historical facts are allowed")
                    if claim.get("candidate_ids") and e.get("candidate_id") not in claim["candidate_ids"]:
                        formal_errors.append("fact/candidate mismatch")
                    if claim.get("attribute") and e.get("attribute") != claim["attribute"]:
                        formal_errors.append("fact/attribute mismatch")
        support = claim.get("prior_support", [])
        if not isinstance(support, list):
            errors.append("invalid prior_support")
            support = []
        for prior in support:
            if not isinstance(prior, dict) or not isinstance(prior.get("message_id"), str) or prior.get("message_id") not in history:
                quote_errors.append("history ID not visible")
                continue
            pos = offset(prior.get("quote"), history[prior["message_id"]]["text"])
            if pos is None:
                quote_errors.append("invalid historical quote")
            else:
                if any(k in prior and prior[k] != pos[k] for k in pos):
                    quote_errors.append("wrong historical offset")
                prior.update(pos)
        claim.update({k: target[k] for k in ("message_id", "agent_id", "evidence_stage", "round")})
    if not package["history_scope"]["complete"] and value.get("temporal_status") != "uncertain":
        formal_errors.append("insufficient defined history for certain temporal classification")
    normalized.update({k: target[k] for k in ("message_id", "agent_id", "evidence_stage", "round")})
    return {"schema_valid": not errors, "quote_valid": not quote_errors, "object_valid": not object_errors,
            "formal_valid": not formal_errors, "errors": errors, "quote_errors": quote_errors,
            "object_errors": object_errors, "formal_errors": formal_errors, "prediction": normalized,
            "semantic_classification_correctness": "not_established_by_schema_validation"}


def run_controlled_judge(config: dict[str, Any], output_dir: Path, *, enabled: bool, resume: bool = False) -> dict[str, Any]:
    """Execute only the frozen controlled queue, never real or debug queues."""
    gate = credential_gate(config, enabled=enabled)
    write_json(output_dir / "credential_gate.json", gate)
    if not gate["allowed"]:
        return gate
    judge_modules = {"common.py", "state.py", "parsing.py", "judge.py", "controlled_cases.py", "evaluation.py"}
    freeze_json(output_dir / "implementation_freeze.json", {
        p.name: sha256_file(p) for p in sorted(Path(__file__).parent.glob("*.py")) if p.name in judge_modules})
    if config.get("dataset") != "controlled" or config.get("enable_real_trajectory_queue") or config.get("logical_request_cap") != 144:
        raise ValueError("Controlled-only budget policy violated")
    manifest = read_json(output_dir / "experiment_manifest.json")
    if manifest["config"] != config:
        raise ValueError("Frozen model/protocol changed: create a new Judge run")
    queue = read_jsonl(output_dir / "request_queue.jsonl")
    packages = {p["request_id"]: p for p in read_jsonl(output_dir / "input_packages.jsonl")}
    outputs_path, attempts_path = output_dir / "outputs.jsonl", output_dir / "attempts.jsonl"
    outputs = read_jsonl(outputs_path) if outputs_path.exists() else []
    attempts = read_jsonl(attempts_path) if attempts_path.exists() else []
    if (outputs or attempts) and not resume:
        raise ValueError("Existing online run requires --resume")
    expected = {q["request_id"]: q for q in queue}
    if len(expected) != 144 or len({o["request_id"] for o in outputs}) != len(outputs):
        raise ValueError("Invalid logical request uniqueness")
    for row in outputs + attempts:
        if row["request_id"] not in expected or row.get("experiment_fingerprint") != manifest["fingerprint"]:
            raise ValueError("Foreign or changed run output")
    completed = {o["request_id"] for o in outputs}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    stop_reason = None
    for q in queue:
        if q["request_id"] in completed:
            continue
        if q["split"] == "holdout":
            dev = [o for o in outputs if o["split"] == "dev"]
            if len(dev) != 72:
                stop_reason = "dev_not_terminal"
                break
            freeze_json(output_dir / "holdout_freeze.json", {"fingerprint": manifest["fingerprint"], "dev_outputs_sha256": sha256_json(dev)})
        if not q["preflight"]:
            preflight = [o for o in outputs if o["preflight"]]
            if len(preflight) != 12 or not all(o["api_success"] and o.get("schema_valid") and o.get("quote_valid") and o.get("object_valid") and o.get("finish_reason") != "length" for o in preflight):
                stop_reason = "technical_preflight_not_passed"
                break
        package = packages[q["request_id"]]
        payload = {"model": config["model_name"], "messages": package["messages"],
                   **{k: config[k] for k in ("temperature", "max_tokens", "thinking", "reasoning_effort", "response_format") if k in config}}
        used = sum(a["request_id"] == q["request_id"] for a in attempts)
        if used >= 2:
            outputs.append({**q, "api_success": False, "status": "api_failure", "error": "attempt_budget_exhausted_after_interruption"})
            write_jsonl(outputs_path, outputs)
            continue
        while used < 2:
            recent = sum(a["started_at_unix"] > time.time() - config["window_seconds"] for a in attempts)
            if len(attempts) >= min(288, config["max_total_formal_attempts"]) or recent >= config["max_attempts_per_window"]:
                stop_reason = "local_attempt_window_or_total_cap"
                break
            used += 1
            attempt = {"request_id": q["request_id"], "experiment_fingerprint": manifest["fingerprint"], "attempt_number": used, "started_at_unix": time.time()}
            attempts.append(attempt)
            write_jsonl(attempts_path, attempts)
            row = {**q, "status": "api_failure", "api_success": False, "parse_success": False,
                   "raw_response": None, "usage": None, "finish_reason": None, "attempt_number": used}
            started, retry = time.monotonic(), False
            request = urllib.request.Request(config["base_url"].rstrip("/") + config["endpoint"], json.dumps(payload).encode(),
                                             {"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["JUDGE_API_KEY_V3_NEW"]})
            try:
                with opener.open(request, timeout=config["request_timeout_seconds"]) as response:
                    body = json.load(response)
                row["raw_provider_response"] = body
                row["api_success"] = True
                if body.get("model") != config["model_name"]:
                    row["status"], stop_reason = "model_mismatch", "actual_model_mismatch"
                else:
                    choice = body["choices"][0]
                    row.update(raw_response=choice["message"].get("content") or "", finish_reason=choice.get("finish_reason"), usage=body.get("usage"))
                    try:
                        prediction = json.loads(row["raw_response"])
                        row.update(parse_success=True, **validate_prediction(prediction, package["package"]))
                        row["status"] = "success" if row["schema_valid"] else "schema_failure"
                    except (ValueError, TypeError):
                        row["status"] = "parse_failure"
                    if row["finish_reason"] == "length":
                        row["status"] = "truncated"
            except urllib.error.HTTPError as exc:
                row["error"] = f"HTTP {exc.code}"
                if exc.code in {401, 403}:
                    stop_reason = "authentication_failure"
                elif exc.code in {402, 429}:
                    stop_reason = "quota_failure"
                else:
                    retry = exc.code in {408, 500, 502, 503, 504}
            except (TimeoutError, ConnectionError, urllib.error.URLError) as exc:
                row["error"], retry = type(exc).__name__, True
            except (ValueError, KeyError, IndexError) as exc:
                row["error"] = type(exc).__name__
            row["latency_seconds"] = time.monotonic() - started
            attempt.update(status=row["status"], latency_seconds=row["latency_seconds"])
            write_jsonl(attempts_path, attempts)
            if not retry or used >= 2 or stop_reason:
                outputs.append(row)
                write_jsonl(outputs_path, outputs)
                break
            time.sleep(config["minimum_request_start_interval_seconds"])
        if stop_reason:
            break
        time.sleep(config["minimum_request_start_interval_seconds"])
    status = {"status": "completed" if len(outputs) == 144 else "partial", "formal_unique_requests": 144,
              "terminal_requests": len(outputs), "formal_attempts": len(attempts),
              "successful_outputs": sum(o["status"] == "success" for o in outputs),
              "failed_outputs": sum(o["status"] != "success" for o in outputs),
              "development_debug_calls": 0, "extractor_calls": 0, "stop_reason": stop_reason}
    write_json(output_dir / "status.json", status)
    return status
