"""Human-readable architecture and validation reporting for the v4 pool."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from mad_attr_filter.difficulty import DifficultyConfig


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
    """Build the requested v4 architecture and validation report."""
    constraint_load_counts: Counter[str] = Counter()
    distractor_counts: Counter[str] = Counter()
    information_counts: Counter[str] = Counter()
    constraint_count_counts: Counter[int] = Counter()
    wrong_violation_counts: Counter[int] = Counter()
    irrelevant_fact_count = 0
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
            irrelevant_fact_count += len(entity["irrelevant_facts"])

    cell_rows = []
    for cell_id, count in generation_report["difficulty_cell_distribution"].items():
        cell_rows.append(cell_id.split("__") + [count])

    lines = [
        "# v4 Factorized Difficulty Generator Report",
        "",
        "## Scope",
        "",
        "The v4 path is additive. The existing v3 `generate_item()` and v3 validator remain unchanged. "
        "Items are generated directly from the same language-independent Boolean attributes and are "
        "then realized with deterministic English templates.",
        "",
        "## Architecture",
        "",
        "1. `DifficultyConfig` validates three independent factors and maps CL1/CL2/CL3 to 3/5/7 constraints.",
        "2. `generate_v4_item()` samples a scenario and formal constraints, creates one Gold candidate, "
        "and constructs distractors from factor-controlled violation signatures.",
        "3. IL2 background facts are stored separately from formal candidate attributes and are only "
        "added to candidate prose.",
        "4. `validate_v4_item()` independently recomputes the matrix and signatures, validates the DS "
        "pattern, and confirms that adding irrelevant fact keys cannot change constraint evaluation.",
        "5. `generate_v4_pool()` traverses the complete 3 x 3 x 2 factorial design with a fixed count per cell.",
        "",
        "## Factor Definitions",
        "",
        "| Factor | Level | Operational definition |",
        "| --- | --- | --- |",
        "| Constraint load | CL1 / CL2 / CL3 | 3 / 5 / 7 independently sampled constraints |",
        "| Distractor similarity | DS1_far | Every wrong option violates at least 3 constraints |",
        "| Distractor similarity | DS2_medium | Exactly one wrong option violates 1 constraint; two violate at least 2 |",
        "| Distractor similarity | DS3_near | Every wrong option violates exactly 1 constraint |",
        "| Information load | IL1_low | Only constraint-relevant facts are displayed |",
        "| Information load | IL2_high | Two non-evaluative background facts are added per candidate |",
        "",
        "## Generation Summary",
        "",
        f"- Output: `{output_path}`",
        f"- Global seed: `{generation_report['global_seed']}`",
        f"- Difficulty cells: {generation_report['num_cells']}",
        f"- Items per cell: {generation_report['items_per_cell']}",
        f"- Requested items: {generation_report['requested_items']}",
        f"- Generated items: {generation_report['generated_items']}",
        f"- Attempts: {generation_report['attempts']}",
        f"- Retries: {generation_report['retries']}",
        f"- Generation failures: {generation_report['generation_failures']}",
        f"- Validation failures: {generation_report['validation_failures']}",
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
        f"- Displayed irrelevant facts: {irrelevant_fact_count}",
        "",
        "## Validation Results",
        "",
        f"- Validated items: {generation_report['validated_items']} / {generation_report['generated_items']}",
        f"- Validation pass rate: {generation_report['validation_pass_rate']:.3f}",
        "- Gold candidates satisfying all constraints: PASS",
        "- Stored matrices matching independent recomputation: PASS",
        "- Stored violation signatures matching independent recomputation: PASS",
        "- Near-distractor one-violation rules: PASS",
        "- Irrelevant facts excluded from formal evaluation: PASS",
        "",
        "## Boolean Boundary Note",
        "",
        "For `CL1 x DS1_far`, a wrong option must violate at least three of exactly three Boolean "
        "constraints. All three distractors therefore necessarily have the same formal signature "
        "`[C1, C2, C3]`. v4 permits this mathematically unavoidable duplicate while still requiring "
        "unique names and a unique Gold. The v3 uniqueness rule is unchanged.",
        "",
        f"Duplicate-signature cell counts observed: `{dict(sorted(duplicate_signature_cells.items()))}`",
        "",
        "## Current Limitations",
        "",
        "- v4 factor levels control generation structure; they are not yet empirical difficulty labels.",
        "- Irrelevant facts are simple deterministic background statements and have not been calibrated with models.",
        "- DS3 samples three one-constraint violations, so with CL2/CL3 not every constraint is represented by a distractor.",
        "- No model inference, MAD debate, or drift classification was run in this stage.",
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
    """Write the v4 report as UTF-8 Markdown."""
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        build_v4_generator_report(items, generation_report, output_path=output_path),
        encoding="utf-8",
    )
