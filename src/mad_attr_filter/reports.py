"""Human-readable markdown reports for pilot data."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

HIGH_RISK_ATTRIBUTES = (
    "has_conflict",
    "exceeds_budget",
    "has_schedule_conflict",
    "needs_supervision",
    "requires_extra_equipment",
)


def _sample_block(sample: Mapping[str, Any]) -> str:
    constraints = "\n".join(
        f"- {constraint['id']}: {constraint['natural_language']} "
        f"({constraint['attribute']}={constraint['required_value']})"
        for constraint in sample["constraints"]
    )
    signatures = "\n".join(
        f"- {label}: {sample['option_violation_signature'][label]}" for label in ("A", "B", "C", "D")
    )
    return (
        f"## {sample['item_id']}\n\n"
        f"- scenario: `{sample['scenario']}`\n"
        f"- option_closeness: `{sample['option_closeness']}`\n"
        f"- structural_complexity: `{sample['structural_complexity']}`\n"
        f"- Gold: `{sample['gold_answer']}`\n\n"
        "### Full Question\n\n"
        f"{sample['question']}\n\n"
        "### Formal Constraints\n\n"
        f"{constraints}\n\n"
        "### Violation Signature\n\n"
        f"{signatures}\n"
    )


def write_examples_report(path: str | Path, samples: Sequence[Mapping[str, Any]], *, seed: int = 42) -> None:
    """Write a report with 3 samples for each option_closeness value."""
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for sample in samples:
        grouped[str(sample["option_closeness"])].append(sample)

    rng = random.Random(seed)
    blocks = ["# English Pilot v3 Examples\n"]
    for closeness in ("easy", "medium", "hard"):
        candidates = list(grouped[closeness])
        if len(candidates) < 3:
            raise ValueError(f"Need at least 3 {closeness} samples for examples report")
        blocks.append(f"# {closeness}\n")
        for sample in rng.sample(candidates, 3):
            blocks.append(_sample_block(sample))

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(blocks), encoding="utf-8")


def write_semantic_audit_report(path: str | Path, samples: Sequence[Mapping[str, Any]]) -> None:
    """Write all samples containing high-risk negative restriction attributes."""
    blocks = ["# English Pilot v3 Semantic Audit\n"]
    matches = []
    for sample in samples:
        risky_constraints = [
            constraint
            for constraint in sample["constraints"]
            if str(constraint["attribute"]) in HIGH_RISK_ATTRIBUTES
        ]
        if risky_constraints:
            matches.append((sample, risky_constraints))

    blocks.append(f"Total high-risk samples: {len(matches)}\n")
    for sample, risky_constraints in matches:
        blocks.append(
            f"## {sample['item_id']}\n\n"
            f"- scenario: `{sample['scenario']}`\n"
            f"- option_closeness: `{sample['option_closeness']}`\n"
            f"- structural_complexity: `{sample['structural_complexity']}`\n"
            f"- Gold: `{sample['gold_answer']}`\n\n"
            "### High-Risk Constraints\n\n"
        )
        for constraint in risky_constraints:
            blocks.append(
                f"- {constraint['id']}: `{constraint['attribute']}={constraint['required_value']}` "
                f"-> {constraint['natural_language']}"
            )
        blocks.append("\n### Violation Signature\n")
        for label in ("A", "B", "C", "D"):
            blocks.append(f"- {label}: {sample['option_violation_signature'][label]}")
        blocks.append("")

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(blocks), encoding="utf-8")
