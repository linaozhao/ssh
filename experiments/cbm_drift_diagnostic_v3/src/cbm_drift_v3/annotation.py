"""Deferred real-trajectory sampling and blind annotation, never synthetic completion."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from .common import AGENTS, BRANCHES, atomic_text, freeze_jsonl, stable_seed, write_json, read_jsonl, sha256_json


def prepare_deferred_real(plan: list[dict[str, Any]], sequences: list[dict[str, Any]], records: list[dict[str, Any]], output_dir: Path, seed: int = 20261109) -> dict[str, Any]:
    """Choose 132 unique targets independently of answers and Judge predictions."""
    lookup = {(r["family_id"], r["branch_type"], r["evidence_stage"], r["round"], r["agent_id"]): r for r in plan}
    by_id = {r.get("message_id", r.get("request_id")): r for r in records}
    seqs = {s["sequence_id"]: s for s in sequences}
    targets, materials, templates = [], [], []
    families = sorted({p["family_id"] for p in plan})
    offset = stable_seed(seed, "blind_selection") % 9
    for fi, family in enumerate(families):
        for stage in range(1, 6):
            position = (offset + fi + stage - 1) % 9
            agent, round_id = AGENTS[position % 3], position // 3
            for branch in ([None] if stage <= 3 else list(BRANCHES)):
                req = lookup[family, branch, stage, round_id, agent]
                rid = req["message_id"]
                seq = seqs[req["sequence_id"]]
                row = {k: req[k] for k in ("message_id", "family_id", "base_item_id", "branch_type", "evidence_stage", "round", "agent_id", "own_previous_message_id", "visible_peer_message_ids")}
                row.update({"sampling_seed": seed, "status": "deferred", "response_available": rid in by_id,
                            "selection_uses_outcomes": False})
                targets.append(row)
                record = by_id.get(rid)
                materials.append({"target_id": rid, "task_text": seq["task_text"], "rules": seq["rules"],
                                  "formal_evidence": [e for s in seq["stages"][:stage] for e in s["events"]],
                                  "visible_history": record.get("messages", []) if record else [],
                                  "target_text": record.get("raw_response") if record else None,
                                  "availability": "available" if record else "not_generated",
                                  "agent_id": agent, "evidence_stage": stage, "round": round_id})
                templates.append({"target_id": rid, "annotation_status": "not_annotated", "current_deviation": None,
                                  "content_labels": [], "temporal_status": None, "claims": [], "notes": ""})
    original_dir = output_dir
    existing = output_dir / "blind_materials.jsonl"
    if existing.exists() and read_jsonl(existing) != materials:
        output_dir = output_dir / "releases" / sha256_json(materials)[:16]
    freeze_jsonl(output_dir / "sampling_manifest.jsonl", targets)
    freeze_jsonl(output_dir / "blind_materials.jsonl", materials)
    for name in ("annotator_1", "annotator_2", "adjudication"):
        freeze_jsonl(output_dir / f"{name}_template.jsonl", templates)
    # Local, self-contained file: no remote scripts, predictions or standard answers.
    blob = json.dumps({"materials": materials, "annotations": templates}, ensure_ascii=False).replace("<", "\\u003c")
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Blind annotation</title>
<style>body{font:15px system-ui;margin:24px;max-width:1100px}select{max-width:100%}pre{white-space:pre-wrap;overflow-wrap:anywhere}textarea{width:100%;height:210px}button{padding:6px 12px}</style>
<h1>Blind annotation</h1><select id="targets"></select><button id="save">Download annotations</button><pre id="material"></pre><textarea id="entry"></textarea>
<script>const data=DATA; const sel=document.querySelector('#targets');let current=0;
data.materials.forEach((m,i)=>{const o=document.createElement('option');o.value=i;o.textContent=m.target_id+' ['+m.availability+']';sel.appendChild(o)});
function show(){document.querySelector('#material').textContent=JSON.stringify(data.materials[current],null,2);document.querySelector('#entry').value=JSON.stringify(data.annotations[current],null,2)}
function store(){data.annotations[current]=JSON.parse(document.querySelector('#entry').value)}
sel.onchange=()=>{try{store();current=Number(sel.value);show()}catch(e){alert('Invalid annotation JSON');sel.value=current}};
document.querySelector('#save').onclick=()=>{try{store();const a=document.createElement('a');const u=URL.createObjectURL(new Blob([data.annotations.map(x=>JSON.stringify(x)).join('\\n')+'\\n'],{type:'application/jsonl'}));a.href=u;a.download='annotations.jsonl';a.click();URL.revokeObjectURL(u)}catch(e){alert('Invalid annotation JSON')}};show();</script></html>'''.replace("DATA", blob)
    atomic_text(output_dir / "blind_annotation.html", page)
    summary = {"status": "deferred", "planned_unique_messages": len(targets),
               "available_messages": sum(r["response_available"] for r in targets),
               "missing_messages": sum(not r["response_available"] for r in targets),
               "future_logical_judge_requests": 264, "online_enabled": False,
               "real_annotation": "deferred", "real_diagnostic_evaluation": "not_evaluated"}
    summary["materials_directory"] = str(output_dir)
    write_json(output_dir / "status.json", summary)
    if output_dir != original_dir:
        write_json(original_dir / "status.json", summary)
    return summary


def flatten_annotation(rows: list[dict[str, Any]], allowed_targets: set[str]) -> list[dict[str, Any]]:
    """Keep explicit negative, uncertain and unannotated states distinct."""
    output, seen = [], set()
    for row in rows:
        target = row["target_id"]
        if target not in allowed_targets or target in seen:
            raise ValueError("Duplicate or unknown annotation target")
        seen.add(target)
        status = row.get("annotation_status")
        if status not in {"not_annotated", "uncertain", "annotated", "adjudicated"}:
            raise ValueError("Invalid annotation scope/status")
        if status in {"annotated", "adjudicated"} and row.get("current_deviation") not in {"yes", "no", "uncertain"}:
            raise ValueError("Annotated reference needs an explicit current-deviation value")
        base = {k: row.get(k) for k in ("target_id", "annotation_status", "current_deviation", "temporal_status")}
        claims = row.get("claims", [])
        if not isinstance(claims, list):
            raise ValueError("claims must be a list")
        if not claims:
            output.append({**base, "claim": None, "reference_kind": "unannotated" if status == "not_annotated" else "explicit_negative" if row.get("current_deviation") == "no" else "uncertain"})
        for claim in claims:
            if not isinstance(claim, dict) or not isinstance(claim.get("quote"), str):
                raise ValueError("Each claim needs an exact quote")
            output.append({**base, "claim": claim, "reference_kind": "claim"})
    return output
