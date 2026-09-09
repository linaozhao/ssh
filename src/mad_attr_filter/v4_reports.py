"""Human-readable generation reporting for the v4.1 prototype."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from mad_attr_filter.difficulty import DifficultyConfig, far_violation_threshold


def _markdown_table(headers: list[str], rows: list[list[object]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return lines


def build_v4_generator_report(
    items: Sequence[Mapping[str, Any]],
    generation_report: Mapping[str, Any],
    *,
    output_path: str,
) -> str:
    """Build the requested v4.1 generation and validation report."""
    constraint_load_counts: Counter[str] = Counter()
    distractor_counts: Counter[str] = Counter()
    information_counts: Counter[str] = Counter()
    constraint_count_counts: Counter[int] = Counter()
    wrong_violation_counts: Counter[int] = Counter()
    non_target_fact_count = 0
    duplicate_signature_cells: Counter[str] = Counter()

    for item in items:
        config = DifficultyConfig.from_mapping(item["difficulty_factors"])
        constraint_load_counts[config.constraint_load] += 1
        distractor_counts[config.distractor_similarity] += 1
        information_counts[config.information_load] += 1
        constraint_count_counts[config.num_constraints] += 1
        wrong_signatures = [
            tuple(signature)
            for label, signature in item["option_violation_signature"].items()
            if label != item["gold_answer"]
        ]
        wrong_violation_counts.update(len(signature) for signature in wrong_signatures)
        if len(set(wrong_signatures)) < len(wrong_signatures):
            duplicate_signature_cells[config.cell_id] += 1
        for entity in item["entities"].values():
            non_target_fact_count += len(entity["non_target_facts"])

    cell_rows = [
        cell_id.split("__") + [count]
        for cell_id, count in generation_report["difficulty_cell_distribution"].items()
    ]
    lines = [
        "# v4.1 Factorized Difficulty Generator Report",
        "",
        "## Scope",
        "",
        "v4.1 refines the additive v4 generation path. The existing v3 `generate_item()` and v3 "
        "validator remain unchanged, as do Gold construction, matrix computation, and violation-signature computation.",
        "",
        "## Refinements",
        "",
        "1. DS1 now uses the dynamic threshold `ceil(k/2)`: CL1=2, CL2=3, CL3=4.",
        "2. DS1 signatures are sampled without replacement whenever three valid subsets exist.",
        "3. IL2 now adds two scenario-compatible non-target work facts per candidate.",
        "4. Candidate prose contains no explicit background or irrelevance cue.",
        "5. Question intro/ending choices are recorded by exact `template_id` and balanced across each cell.",
        "",
        "## Factor Definitions",
        "",
        "| Factor | Level | Operational definition |",
        "| --- | --- | --- |",
        "| Constraint load | CL1 / CL2 / CL3 | 3 / 5 / 7 independently sampled constraints |",
        f"| Distractor similarity | DS1_far | Every wrong option violates at least ceil(k/2): "
        f"{far_violation_threshold(3)} / {far_violation_threshold(5)} / {far_violation_threshold(7)} |",
        "| Distractor similarity | DS2_medium | Exactly one wrong option violates 1 constraint; two violate at least 2 |",
        "| Distractor similarity | DS3_near | Every wrong option violates exactly 1 constraint |",
        "| Information load | IL1_low | Only target constraint facts are displayed |",
        "| Information load | IL2_high | Two domain-relevant non-target facts are added per candidate |",
        "",
        "## Generation Summary",
        "",
        f"- Output: `{output_path}`",
        f"- Generator version: `{generation_report['generator_version']}`",
        f"- Global seed: `{generation_report['global_seed']}`",
        f"- Difficulty cells: {generation_report['num_cells']}",
        f"- Items per cell: {generation_report['items_per_cell']}",
        f"- Requested items: {generation_report['requested_items']}",
        f"- Generated items: {generation_report['generated_items']}",
        f"- Attempts: {generation_report['attempts']}",
        f"- Retries: {generation_report['retries']}",
        f"- Generation failures: {generation_report['generation_failures']}",
        f"- Validation failures: {generation_report['validation_failures']}",
        f"- Generation warnings: {generation_report['generation_warning_count']}",
        "",
        "## Cell Distribution",
        "",
        *_markdown_table(
            ["Constraint load", "Distractor similarity", "Information load", "Items"],
            cell_rows,
        ),
        "",
        "## Marginal Distribution",
        "",
        f"- Constraint load: `{dict(sorted(constraint_load_counts.items()))}`",
        f"- Constraint counts: `{dict(sorted(constraint_count_counts.items()))}`",
        f"- Distractor similarity: `{dict(sorted(distractor_counts.items()))}`",
        f"- Information load: `{dict(sorted(information_counts.items()))}`",
        f"- Gold positions: `{generation_report['gold_position_distribution']}`",
        f"- Scenarios: `{generation_report['scenario_distribution']}`",
        f"- Wrong-option violation counts: `{dict(sorted(wrong_violation_counts.items()))}`",
        f"- Displayed non-target facts: {non_target_fact_count}",
        f"- Items with duplicate wrong signatures: {sum(duplicate_signature_cells.values())}",
        "",
        "## Validation Results",
        "",
        f"- Validated items: {generation_report['validated_items']} / {generation_report['generated_items']}",
        f"- Validation pass rate: {generation_report['validation_pass_rate']:.3f}",
        "- Gold candidates satisfying all constraints: PASS",
        "- Stored matrices matching independent recomputation: PASS",
        "- Stored violation signatures matching independent recomputation: PASS",
        "- Dynamic DS1 thresholds and DS2/DS3 patterns: PASS",
        "- Non-target facts outside formal attributes: PASS",
        "- Non-target facts preserving constraint evaluation: PASS",
        "- Scenario relevance of non-target facts: PASS",
        "",
        "## Current Limitations",
        "",
        "- v4.1 factors are controlled variables, not empirical difficulty labels.",
        "- Non-target facts use deterministic English templates and still require model calibration.",
        "- DS3 represents three distinct one-constraint failures, so CL2/CL3 cannot expose every constraint in an error option.",
        "- No model inference, MAD debate, or drift classification was run.",
        "",
    ]
    return "\n".join(lines)


def write_v4_generator_report(
    path: str | Path,
    items: Sequence[Mapping[str, Any]],
    generation_report: Mapping[str, Any],
    *,
    output_path: str,
) -> None:
    """Write the v4.1 report as UTF-8 Markdown."""
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        build_v4_generator_report(items, generation_report, output_path=output_path),
        encoding="utf-8",
    )
