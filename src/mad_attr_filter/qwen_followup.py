"""Data construction and response parsing for the Qwen v4.1 follow-up."""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

from mad_attr_filter.difficulty import all_difficulty_configs
from mad_attr_filter.generator import LABELS, GenerationError
from mad_attr_filter.io import read_jsonl
from mad_attr_filter.scenarios import SCENARIOS
from mad_attr_filter.v4_calibration import (
    PROMPT_TEMPLATE,
    VALID_OPTIONS,
    _find_json_objects,
    _normalize_answer,
    canonical_hash,
    parse_calibration_response,
    sha256_bytes,
    sha256_file,
)
from mad_attr_filter.v4_generator import generate_v4_item
from mad_attr_filter.v4_validation import validate_v4_item, validate_v4_pool

FOLLOWUP_PROTOCOL_VERSION = "qwen-v4.1-followup-1"
FOLLOWUP_PARSER_REVISION = "qwen-v4.1-name-aware-parser-2"
EXTENSION_BATCH_ID = "v4_1_extension_20260910"
EXTENSION_GLOBAL_SEED = 20260910
IL_PAIR_SELECTION_SEED = 20260910


class FollowupError(ValueError):
    """Raised when a follow-up artifact violates its frozen protocol."""


def normalized_content_hash(item: Mapping[str, Any]) -> str:
    """Hash normalized natural-language content without identifier metadata."""
    normalized = re.sub(r"\s+", " ", str(item["question"]).strip()).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _replace_candidate_block(question: str, options: Mapping[str, str]) -> str:
    """Replace only the labeled candidate block while preserving all other text."""
    marker = "\nCandidates:\n"
    if question.count(marker) != 1:
        raise FollowupError("Question does not contain one Candidates block")
    prefix, candidate_and_ending = question.split(marker, 1)
    if "\n\n" not in candidate_and_ending:
        raise FollowupError("Question has no candidate/ending boundary")
    _, ending = candidate_and_ending.rsplit("\n\n", 1)
    option_lines = "\n".join(f"{label}. {options[label]}" for label in LABELS)
    return f"{prefix}{marker}{option_lines}\n\n{ending}"


def _source_item_id(item: Mapping[str, Any]) -> str:
    return str(item.get("source_item_id") or item["item_id"])


def rotate_item_options(
    source: Mapping[str, Any],
    rotation: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Create one cyclic option-order version with all label-indexed fields synced."""
    if rotation not in range(4):
        raise FollowupError("rotation must be in 0..3")
    old_to_new = {
        old_label: LABELS[(index + rotation) % len(LABELS)]
        for index, old_label in enumerate(LABELS)
    }
    new_to_old = {new: old for old, new in old_to_new.items()}
    variant = deepcopy(dict(source))
    source_id = _source_item_id(source)
    variant_id = f"{source_id.removesuffix('_original')}__position_r{rotation}"
    variant["item_id"] = variant_id
    variant["source_item_id"] = source_id
    variant["variant_id"] = variant_id
    variant["variant_type"] = "position_rotation"
    for field in (
        "options",
        "entities",
        "option_constraint_matrix",
        "option_violation_signature",
    ):
        original = source[field]
        variant[field] = {
            new_label: deepcopy(original[new_to_old[new_label]]) for new_label in LABELS
        }
    variant["gold_answer"] = old_to_new[str(source["gold_answer"])]
    variant["question"] = _replace_candidate_block(
        str(source["question"]), variant["options"]
    )
    variant["metadata"] = deepcopy(dict(source["metadata"]))
    variant["metadata"]["diagnostic_experiment"] = "position_order"
    variant["metadata"]["position_rotation"] = rotation
    variant["metadata"]["old_to_new_label"] = old_to_new
    validate_v4_item(variant)

    for old_label, new_label in old_to_new.items():
        if variant["entities"][new_label]["name"] != source["entities"][old_label]["name"]:
            raise FollowupError("Candidate identity changed during option rotation")
        if variant["options"][new_label] != source["options"][old_label]:
            raise FollowupError("Candidate text changed during option rotation")
        if (
            variant["option_violation_signature"][new_label]
            != source["option_violation_signature"][old_label]
        ):
            raise FollowupError("Violation signature changed during option rotation")

    manifest = {
        "source_item_id": source_id,
        "base_item_id": source["base_item_id"],
        "variant_id": variant_id,
        "rotation": rotation,
        "difficulty_cell": source["metadata"]["difficulty_cell"],
        "scenario": source["scenario"],
        "original_gold_label": source["gold_answer"],
        "new_gold_label": variant["gold_answer"],
        "old_to_new_label": old_to_new,
        "new_to_old_label": new_to_old,
        "candidate_identity_by_new_label": {
            label: variant["entities"][label]["name"] for label in LABELS
        },
        "semantic_equivalence_validated": True,
    }
    return variant, manifest


def select_position_followup_items(
    samples: Sequence[Mapping[str, Any]],
    item_model_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Select 10 stable errors, one mixed item, and 10 matched controls."""
    sample_by_id = {str(item["item_id"]): item for item in samples}
    qwen_rows = [row for row in item_model_rows if row["model_alias"] == "qwen"]
    stable_wrong = sorted(
        (row for row in qwen_rows if row["all_three_valid_and_wrong"]),
        key=lambda row: str(row["item_id"]),
    )
    mixed = sorted(
        (row for row in qwen_rows if row["has_correct_and_valid_wrong"]),
        key=lambda row: str(row["item_id"]),
    )
    if len(stable_wrong) != 10 or len(mixed) != 1:
        raise FollowupError(
            f"Expected 10 stable-wrong and 1 mixed Qwen items; got "
            f"{len(stable_wrong)} and {len(mixed)}"
        )
    controls = [row for row in qwen_rows if row["all_three_valid_and_correct"]]
    used_controls: set[str] = set()
    control_records: list[dict[str, Any]] = []
    for target in stable_wrong:
        target_factors = target["difficulty_factors"]

        def score(row: Mapping[str, Any]) -> tuple[int, int, str]:
            factor_distance = sum(
                row["difficulty_factors"][key] != target_factors[key]
                for key in (
                    "constraint_load",
                    "distractor_similarity",
                    "information_load",
                )
            )
            scenario_distance = int(row["scenario"] != target["scenario"])
            return factor_distance, scenario_distance, str(row["item_id"])

        available = [row for row in controls if str(row["item_id"]) not in used_controls]
        if not available:
            raise FollowupError("Not enough unique stable-correct controls")
        chosen = min(available, key=score)
        used_controls.add(str(chosen["item_id"]))
        control_records.append(
            {
                "target_item_id": target["item_id"],
                "control_item_id": chosen["item_id"],
                "target_cell": target["difficulty_cell"],
                "control_cell": chosen["difficulty_cell"],
                "target_scenario": target["scenario"],
                "control_scenario": chosen["scenario"],
                "factor_mismatch_count": score(chosen)[0],
                "scenario_matched": chosen["scenario"] == target["scenario"],
            }
        )

    selection: list[dict[str, Any]] = []
    for row in stable_wrong:
        selection.append(
            {"item": deepcopy(dict(sample_by_id[str(row["item_id"])])), "selection_group": "stable_wrong"}
        )
    selection.append(
        {"item": deepcopy(dict(sample_by_id[str(mixed[0]["item_id"])])), "selection_group": "mixed"}
    )
    for record in control_records:
        selection.append(
            {
                "item": deepcopy(dict(sample_by_id[str(record["control_item_id"])])),
                "selection_group": "stable_correct_control",
            }
        )
    return selection, control_records


def build_position_variants(
    samples: Sequence[Mapping[str, Any]],
    item_model_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Build and validate 84 option-order variants from 21 selected base items."""
    selected, control_matches = select_position_followup_items(samples, item_model_rows)
    variants: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    control_by_id = {record["control_item_id"]: record for record in control_matches}
    for entry in selected:
        source = entry["item"]
        for rotation in range(4):
            variant, manifest = rotate_item_options(source, rotation)
            variant["selection_group"] = entry["selection_group"]
            manifest["selection_group"] = entry["selection_group"]
            if source["item_id"] in control_by_id:
                manifest["control_match"] = control_by_id[source["item_id"]]
            variants.append(variant)
            manifests.append(manifest)
    if len(variants) != 84 or len({item["item_id"] for item in variants}) != 84:
        raise FollowupError("Position experiment must contain 84 unique variants")
    by_source: dict[str, set[str]] = {}
    for manifest in manifests:
        source_id = str(manifest["source_item_id"])
        by_source.setdefault(source_id, set()).add(str(manifest["new_gold_label"]))
    if any(labels != set(LABELS) for labels in by_source.values()):
        raise FollowupError("Gold candidate did not occupy every label exactly once")
    return variants, manifests


def _remove_non_target_suffix(item: Mapping[str, Any], label: str) -> str:
    facts = item["entities"][label]["non_target_facts"]
    if len(facts) != 2:
        raise FollowupError("An IL2 source must have two marked non-target facts per option")
    suffix = " " + " ".join(f"{fact['text']}." for fact in facts)
    option = str(item["options"][label])
    if not option.endswith(suffix):
        raise FollowupError(f"Marked non-target facts are not an exact suffix for {label}")
    return option[: -len(suffix)]


def make_information_load_variant(
    source: Mapping[str, Any],
    information_load: str,
) -> dict[str, Any]:
    """Create an IL2 original or exact fact-removal IL1 paired version."""
    if source["difficulty_factors"]["information_load"] != "IL2_high":
        raise FollowupError("Paired source must be IL2_high")
    if information_load not in {"IL1_low", "IL2_high"}:
        raise FollowupError(f"Unknown information load: {information_load}")
    variant = deepcopy(dict(source))
    source_id = _source_item_id(source)
    suffix = "il1" if information_load == "IL1_low" else "il2"
    variant_id = f"{source_id.removesuffix('_original')}__paired_{suffix}"
    variant["item_id"] = variant_id
    variant["source_item_id"] = source_id
    variant["variant_id"] = variant_id
    variant["variant_type"] = "information_load_pair"
    variant["pair_version"] = information_load
    variant["metadata"] = deepcopy(dict(source["metadata"]))
    variant["metadata"]["diagnostic_experiment"] = "information_load_pair"
    if information_load == "IL1_low":
        for label in LABELS:
            variant["options"][label] = _remove_non_target_suffix(source, label)
            variant["entities"][label]["non_target_facts"] = []
        variant["difficulty_factors"]["information_load"] = "IL1_low"
        variant["metadata"]["difficulty_cell"] = str(
            source["metadata"]["difficulty_cell"]
        ).replace("IL2_high", "IL1_low")
        variant["question"] = _replace_candidate_block(
            str(source["question"]), variant["options"]
        )
    validate_v4_item(variant)
    for field in ("constraints", "gold_answer", "option_constraint_matrix", "option_violation_signature"):
        if variant[field] != source[field]:
            raise FollowupError(f"IL pairing changed formal field {field}")
    return variant


def build_information_load_pairs(
    samples: Sequence[Mapping[str, Any]],
    *,
    selection_seed: int = IL_PAIR_SELECTION_SEED,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Select four IL2 items per CL x DS cell and create exact IL1/IL2 pairs."""
    rng = random.Random(selection_seed)
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for sample in samples:
        factors = sample["difficulty_factors"]
        if factors["information_load"] != "IL2_high":
            continue
        key = (factors["constraint_load"], factors["distractor_similarity"])
        grouped.setdefault(key, []).append(sample)
    if len(grouped) != 9:
        raise FollowupError(f"Expected 9 CL x DS IL2 groups, found {len(grouped)}")
    variants: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    for key in sorted(grouped):
        candidates = sorted(grouped[key], key=lambda item: str(item["item_id"]))
        selected = sorted(rng.sample(candidates, 4), key=lambda item: str(item["item_id"]))
        for source in selected:
            low = make_information_load_variant(source, "IL1_low")
            high = make_information_load_variant(source, "IL2_high")
            variants.extend((low, high))
            manifest.append(
                {
                    "source_item_id": source["item_id"],
                    "base_item_id": source["base_item_id"],
                    "constraint_load": key[0],
                    "distractor_similarity": key[1],
                    "scenario": source["scenario"],
                    "selection_seed": selection_seed,
                    "selected_without_using_model_outcomes": True,
                    "il1_variant_id": low["item_id"],
                    "il2_variant_id": high["item_id"],
                    "formal_equivalence_validated": True,
                    "removed_non_target_fact_count": sum(
                        len(source["entities"][label]["non_target_facts"])
                        for label in LABELS
                    ),
                }
            )
    if len(manifest) != 36 or len(variants) != 72:
        raise FollowupError("IL pairing must contain 36 bases and 72 versions")
    return variants, manifest


def build_extension_pool(
    existing_items: Sequence[Mapping[str, Any]],
    *,
    items_per_cell: int = 20,
    global_seed: int = EXTENSION_GLOBAL_SEED,
    start_index: int = 181,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Generate a frozen independent extension without overwriting the prototype."""
    if items_per_cell != 20:
        raise FollowupError("The registered extension design requires 20 new items per cell")
    validate_v4_pool(existing_items, expected_items_per_cell=10)
    existing_ids = {str(item["item_id"]) for item in existing_items}
    seen_hashes = {normalized_content_hash(item) for item in existing_items}
    rng = random.Random(global_seed)
    extension: list[dict[str, Any]] = []
    retries = 0
    attempts = 0
    for cell_index, config in enumerate(all_difficulty_configs()):
        for within_cell_index in range(items_per_cell):
            item_index = start_index + len(extension)
            scenario = SCENARIOS[(cell_index + within_cell_index) % len(SCENARIOS)]
            gold_label = LABELS[within_cell_index % len(LABELS)]
            scenario_index = next(
                index for index, value in enumerate(SCENARIOS) if value.key == scenario.key
            )
            template_group = 10 + within_cell_index // len(SCENARIOS)
            template_indices = (
                (template_group + cell_index) % 3,
                (template_group + scenario_index + cell_index) % 3,
            )
            for _ in range(200):
                attempts += 1
                item_seed = rng.randrange(1, 2**31 - 1)
                try:
                    item = generate_v4_item(
                        item_index,
                        config,
                        item_seed,
                        gold_label=gold_label,
                        scenario_key=scenario.key,
                        question_template_indices=template_indices,
                    )
                except GenerationError:
                    retries += 1
                    continue
                content_hash = normalized_content_hash(item)
                if item["item_id"] in existing_ids or content_hash in seen_hashes:
                    retries += 1
                    continue
                item["generation_metadata"]["batch_id"] = EXTENSION_BATCH_ID
                item["generation_metadata"]["global_seed"] = global_seed
                item["metadata"]["generation_batch"] = EXTENSION_BATCH_ID
                item["metadata"]["normalized_content_sha256"] = content_hash
                validate_v4_item(item)
                extension.append(item)
                existing_ids.add(str(item["item_id"]))
                seen_hashes.add(content_hash)
                break
            else:
                raise FollowupError(f"Could not generate unique item for {config.cell_id}")

    extension_validation = validate_v4_pool(
        extension, expected_items_per_cell=items_per_cell
    )
    combined = [deepcopy(dict(item)) for item in existing_items] + extension
    combined_validation = validate_v4_pool(combined, expected_items_per_cell=30)
    all_hashes = [normalized_content_hash(item) for item in combined]
    duplicate_hashes = len(all_hashes) - len(set(all_hashes))
    if duplicate_hashes:
        raise FollowupError(f"Combined pool contains {duplicate_hashes} content duplicates")
    report = {
        "batch_id": EXTENSION_BATCH_ID,
        "global_seed": global_seed,
        "start_index": start_index,
        "items_per_cell_added": items_per_cell,
        "attempts": attempts,
        "retries": retries,
        "extension_validation": extension_validation,
        "combined_validation": combined_validation,
        "prototype_count": len(existing_items),
        "extension_count": len(extension),
        "combined_count": len(combined),
        "duplicate_item_id_count": len(combined) - len({item["item_id"] for item in combined}),
        "duplicate_normalized_content_hash_count": duplicate_hashes,
        "frozen_before_model_inference": True,
    }
    return extension, report


def candidate_name_map(item: Mapping[str, Any]) -> dict[str, str]:
    """Return case-folded full candidate names mapped to their option labels."""
    names: dict[str, str] = {}
    for label in LABELS:
        name = str(item["entities"][label]["name"]).strip()
        key = name.casefold()
        if not name or key in names:
            raise FollowupError("Candidate names must be nonempty and unique")
        names[key] = label
    return names


def _semantic_answer(value: Any, name_map: Mapping[str, str]) -> tuple[str | None, str | None]:
    label = _normalize_answer(value)
    if label is not None:
        return label, "label"
    if not isinstance(value, str):
        return None, None
    name = value.strip().rstrip(".").casefold()
    if name in name_map:
        return name_map[name], "candidate_name"
    return None, None


def parse_followup_response(raw_response: str, item: Mapping[str, Any]) -> dict[str, Any]:
    """Parse labels or exact candidate names without guessing from reasoning prose."""
    base = parse_calibration_response(raw_response)
    stripped = raw_response.strip()
    names = candidate_name_map(item)
    raw_answer: Any = None
    strict_payload: Mapping[str, Any] | None = None
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, Mapping):
        strict_payload = parsed
        raw_answer = parsed.get("answer")
        answer, source = _semantic_answer(raw_answer, names)
        if answer is not None:
            reasoning = parsed.get("reasoning")
            confidence = parsed.get("confidence")
            confidence_value = None
            if not isinstance(confidence, bool):
                try:
                    candidate_confidence = float(confidence)
                except (TypeError, ValueError):
                    candidate_confidence = -1.0
                if 0.0 <= candidate_confidence <= 1.0:
                    confidence_value = candidate_confidence
            strict_label = source == "label" and isinstance(raw_answer, str) and raw_answer.strip() in VALID_OPTIONS
            return {
                "answer": answer,
                "raw_answer": raw_answer,
                "reasoning": reasoning if isinstance(reasoning, str) else "",
                "confidence": confidence_value,
                "answer_extractable": True,
                "json_compliant": bool(
                    strict_label
                    and isinstance(reasoning, str)
                    and confidence_value is not None
                    and set(parsed) >= {"answer", "reasoning", "confidence"}
                ),
                "strict_json_syntax": True,
                "strict_answer_format": strict_label,
                "semantic_name_mapping_used": source == "candidate_name",
                "parse_source": (
                    "strict_json_label" if source == "label" else "strict_json_candidate_name"
                ),
                "fallback_used": source != "label",
                "ambiguous_answer": False,
                "answer_candidates": [answer],
                "parse_error": None if strict_label else "Answer used a non-protocol representation",
            }

    answer_candidates: list[str] = []
    raw_candidates: list[str] = []
    for object_text in _find_json_objects(raw_response):
        try:
            candidate_object = json.loads(object_text)
        except json.JSONDecodeError:
            continue
        if not isinstance(candidate_object, Mapping):
            continue
        value = candidate_object.get("answer")
        answer, source = _semantic_answer(value, names)
        if answer is not None and source == "candidate_name":
            answer_candidates.append(answer)
            raw_candidates.append(str(value))
    for name, label in names.items():
        pattern = rf"(?im)^\s*(?:FINAL\s+ANSWER|ANSWER|SELECTED\s+ANSWER)\s*[:=\-]\s*{re.escape(name)}[.]?\s*$"
        if re.search(pattern, raw_response.casefold()):
            answer_candidates.append(label)
            raw_candidates.append(name)
    combined = sorted(set(answer_candidates) | set(base.get("answer_candidates", [])))
    if base["answer_extractable"] and not answer_candidates:
        return {
            **base,
            "raw_answer": raw_answer,
            "strict_answer_format": bool(
                strict_payload is not None
                and isinstance(raw_answer, str)
                and raw_answer.strip() in VALID_OPTIONS
            ),
            "semantic_name_mapping_used": False,
        }
    if len(combined) == 1:
        return {
            **base,
            "answer": combined[0],
            "raw_answer": raw_candidates[0] if raw_candidates else None,
            "answer_extractable": True,
            "strict_answer_format": False,
            "semantic_name_mapping_used": True,
            "parse_source": "fallback_candidate_name",
            "fallback_used": True,
            "ambiguous_answer": False,
            "answer_candidates": combined,
            "parse_error": "Candidate name recovered from noncompliant output",
        }
    if len(combined) > 1:
        return {
            **base,
            "answer": None,
            "raw_answer": raw_candidates,
            "answer_extractable": False,
            "strict_answer_format": False,
            "semantic_name_mapping_used": bool(raw_candidates),
            "parse_source": "conflicting_answers",
            "fallback_used": bool(raw_candidates),
            "ambiguous_answer": True,
            "answer_candidates": combined,
            "parse_error": "Conflicting explicit answers were found",
        }
    return {
        **base,
        "raw_answer": raw_answer,
        "strict_answer_format": False,
        "semantic_name_mapping_used": False,
    }


def build_followup_fingerprints(
    dataset_path: str | Path,
    experiment_config: Mapping[str, Any],
) -> dict[str, str]:
    """Fingerprint one frozen follow-up dataset, prompt, parser, and config."""
    public = deepcopy(dict(experiment_config))
    public.get("model", {}).pop("api_key", None)
    fingerprints = {
        "dataset_sha256": sha256_file(dataset_path),
        "config_sha256": canonical_hash(public),
        "prompt_sha256": sha256_bytes(PROMPT_TEMPLATE.encode("utf-8")),
        "protocol_version": FOLLOWUP_PROTOCOL_VERSION,
        "parser_revision": FOLLOWUP_PARSER_REVISION,
    }
    fingerprints["experiment_sha256"] = canonical_hash(fingerprints)
    return fingerprints


def load_prototype_and_qwen_rows(root: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load the frozen prototype and prior item-model analysis."""
    root_path = Path(root)
    samples = read_jsonl(root_path / "data/multi_constraint_v4_1_prototype.jsonl")
    rows = read_jsonl(root_path / "results/v4_1_calibration/item_model_analysis.jsonl")
    return samples, [row for row in rows if row["model_alias"] == "qwen"]


def extension_index_records(
    prototype: Sequence[Mapping[str, Any]],
    extension: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build a compact 540-item index with split and content fingerprints."""
    records: list[dict[str, Any]] = []
    for split, items in (("development_calibration", prototype), ("independent_validation", extension)):
        for item in items:
            records.append(
                {
                    "item_id": item["item_id"],
                    "split": split,
                    "difficulty_cell": item["metadata"]["difficulty_cell"],
                    "difficulty_factors": item["difficulty_factors"],
                    "scenario": item["scenario"],
                    "gold_answer": item["gold_answer"],
                    "normalized_content_sha256": normalized_content_hash(item),
                }
            )
    return records
