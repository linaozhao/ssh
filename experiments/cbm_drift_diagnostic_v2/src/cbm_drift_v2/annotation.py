"""Independent, Judge-blind annotation package export."""

from __future__ import annotations

import csv
import html
from collections import defaultdict
from pathlib import Path
from typing import Any

from cbm_drift_v2.common import read_jsonl, write_json, write_jsonl


def _message_html(row: dict[str, Any]) -> str:
    response = html.escape(row.get("raw_response", ""))
    peers = ", ".join(row.get("visible_peer_message_ids", [])) or "none"
    return (
        f"<article><h5>{html.escape(row['message_id'])}</h5>"
        f"<p><b>Agent:</b> {row['agent_id']} &nbsp; <b>Round:</b> R{row['round']} &nbsp; "
        f"<b>Visible peer IDs:</b> {html.escape(peers)}</p><pre>{response}</pre></article>"
    )


def export_annotation_package(root: Path) -> dict[str, Any]:
    """Export all 36 complete trajectories without any Judge labels."""
    sequences = {row["variant_id"]: row for row in read_jsonl(root / "data/evidence_sequences.jsonl")}
    outputs = read_jsonl(root / "results/mad/raw_outputs.jsonl")
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in outputs:
        grouped[row["variant_id"]].append(row)
    annotation = root / "annotation"
    annotation.mkdir(parents=True, exist_ok=True)
    template_rows = [{
        "trajectory_id": variant_id, "base_item_id": sequence["base_item_id"],
        "variant_type": sequence["variant_type"], "annotator_id": "",
        "trajectory_has_deviation": None, "events": [], "notes": "",
    } for variant_id, sequence in sorted(sequences.items())]
    for annotator in ("annotator_1", "annotator_2"):
        rows = [dict(row, annotator_id=annotator) for row in template_rows]
        write_jsonl(annotation / f"{annotator}_template.jsonl", rows)
        with (annotation / f"{annotator}_template.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=[
                "trajectory_id", "base_item_id", "variant_type", "annotator_id",
                "trajectory_has_deviation", "event_start_message_id", "event_end_message_id",
                "agent_id", "temporal_status", "content_labels", "target_entity_ids",
                "violated_fact_ids", "violated_rule_ids", "exact_quote", "quote_start", "quote_end",
                "related_event_ids", "uncertain", "notes",
            ])
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in writer.fieldnames})
    write_jsonl(annotation / "adjudication_template.jsonl", template_rows)

    sections = []
    for variant_id, sequence in sorted(sequences.items()):
        messages = sorted(grouped.get(variant_id, []), key=lambda row: (row["evidence_stage"], row["round"], row["agent_id"]))
        by_stage: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in messages:
            by_stage[int(row["evidence_stage"])].append(row)
        rules = "".join(f"<li>{html.escape(rule['natural_language'])}</li>" for rule in sequence["rules"])
        stages = []
        for stage in range(1, 6):
            state = sequence["stage_states"][stage - 1]
            evidence = "".join(
                f"<li><code>{html.escape(event['evidence_id'])}</code>: {html.escape(event['text'])}</li>"
                for event in state["active_evidence"]
            )
            messages_html = "".join(_message_html(row) for row in by_stage[stage])
            stages.append(
                f"<details><summary>T{stage}: current evidence and nine public messages</summary>"
                f"<p class='warning'>Only use evidence visible through T{stage}; do not use later stages.</p>"
                f"<ul>{evidence}</ul>{messages_html}</details>"
            )
        sections.append(
            f"<section><h2>{html.escape(variant_id)}</h2><p><b>Base:</b> {sequence['base_item_id']} &nbsp; "
            f"<b>Condition:</b> {sequence['variant_type']}</p><h3>Fixed requirements</h3><ol>{rules}</ol>"
            f"{''.join(stages)}</section>"
        )
    page = """<!doctype html><html><head><meta charset='utf-8'><title>CBM MAD annotation package</title>
<style>body{font-family:system-ui,sans-serif;max-width:1200px;margin:auto;padding:24px;line-height:1.45}section{border-top:2px solid #333;margin:32px 0}details{margin:16px 0;padding:8px;border:1px solid #aaa}article{margin:12px;padding:10px;border-left:4px solid #467}pre{white-space:pre-wrap}.warning{color:#9b2c2c;font-weight:700}code{font-size:.9em}</style></head><body>
<h1>CBM MAD drift annotation package</h1><p class='warning'>Judge predictions are intentionally absent. Annotate each trajectory independently. Future evidence must not be used to evaluate earlier messages.</p>
<p>Use <code>docs/annotation_guidelines.md</code> and one annotator-specific template. You may add events that no automated system found.</p>""" + "".join(sections) + "</body></html>"
    (annotation / "trajectories.html").write_text(page, encoding="utf-8")
    manifest = {
        "trajectories": len(sequences), "messages": len(outputs),
        "judge_predictions_included": False,
        "files": ["trajectories.html", "annotator_1_template.jsonl", "annotator_2_template.jsonl", "adjudication_template.jsonl"],
    }
    write_json(annotation / "manifest.json", manifest)
    return manifest
