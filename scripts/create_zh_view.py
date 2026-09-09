#!/usr/bin/env python3
"""Create a Chinese read-only view of the English v3 pilot dataset."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mad_attr_filter.io import read_jsonl, write_jsonl

CHINESE_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")

SCENARIO_INTROS: dict[str, str] = {
    "expert_recruitment": "某研究实验室正在为一个新项目选择一名研究人员。",
    "project_assignment": "项目团队需要为一项专门任务分配一名成员。",
    "availability_selection": "协调人需要从四名候选人中找出唯一符合日程和参与要求的人。",
}

SCENARIO_ENDINGS: dict[str, str] = {
    "expert_recruitment": "哪位候选人满足所有要求？",
    "project_assignment": "哪位候选人适合承担这项任务？",
    "availability_selection": "哪位候选人符合全部要求？",
}

CONSTRAINT_ZH: dict[tuple[str, bool], str] = {
    ("has_ml_experience", True): "候选人需要具备机器学习经验。",
    ("has_programming_experience", True): "候选人需要具备编程经验。",
    ("has_management_experience", True): "候选人需要有管理或协调经验。",
    ("speaks_english", True): "候选人需要能够使用英语进行工作沟通。",
    ("has_certificate", True): "候选人需要持有相关证书。",
    ("has_research_experience", True): "候选人需要有研究项目经验。",
    ("has_data_analysis_experience", True): "候选人需要具备数据分析经验。",
    ("has_project_experience", True): "候选人需要参与过项目执行工作。",
    ("available_monday", True): "候选人需要周一可以参与工作。",
    ("available_tuesday", True): "候选人需要周二可以参与工作。",
    ("available_morning", True): "候选人需要上午可以参与工作。",
    ("available_afternoon", True): "候选人需要下午可以参与工作。",
    ("available_weekend", True): "候选人需要周末可以参与工作。",
    ("available_next_month", True): "候选人需要下个月可以加入项目。",
    ("has_conflict", False): "候选人不能存在与项目相关的利益冲突。",
    ("requires_remote", True): "候选人只接受远程参与安排。",
    ("requires_remote", False): "候选人不应要求只能远程参与。",
    ("can_work_remote", True): "候选人需要能够远程工作。",
    ("can_work_onsite", True): "候选人需要能够现场参与工作。",
    ("exceeds_budget", False): "候选人的参与成本不能超出项目预算。",
    ("needs_supervision", False): "候选人需要能够在不需要额外监督的情况下工作。",
    ("has_schedule_conflict", False): "候选人不能存在日程冲突。",
    ("requires_extra_equipment", False): "候选人不能需要额外专用设备支持。",
    ("has_domain_knowledge", True): "候选人需要了解相关项目领域。",
    ("has_teamwork_experience", True): "候选人需要具备团队协作经验。",
    ("has_client_communication_experience", True): "候选人需要具备客户沟通经验。",
    ("prefers_long_term_project", True): "候选人偏好长期项目。",
    ("prefers_long_term_project", False): "候选人不应只偏好长期项目。",
    ("willing_to_travel", True): "候选人需要愿意出差。",
    ("accepts_flexible_hours", True): "候选人需要接受灵活工时安排。",
    ("has_security_clearance", True): "候选人需要具备安全许可。",
    ("has_prior_training", True): "候选人需要完成过相关培训。",
    ("has_local_work_permit", True): "候选人需要具有本地工作许可。",
    ("can_work_independently", True): "候选人需要能够独立工作。",
    ("has_public_speaking_experience", True): "候选人需要有公开表达或演讲经验。",
    ("familiar_with_statistics", True): "候选人需要熟悉统计方法。",
    ("has_quality_assurance_experience", True): "候选人需要具备质量保证经验。",
    ("prefers_on_site_work", True): "候选人偏好现场工作。",
    ("prefers_on_site_work", False): "候选人不应只偏好现场工作。",
}

FACT_ZH: dict[tuple[str, bool], str] = {
    ("has_ml_experience", True): "{name} 有机器学习项目经验",
    ("has_ml_experience", False): "{name} 没有机器学习方面的实践经验",
    ("has_programming_experience", True): "{name} 有实际编程经验",
    ("has_programming_experience", False): "{name} 没有处理过编程任务",
    ("has_management_experience", True): "{name} 曾经负责过项目或团队协调",
    ("has_management_experience", False): "{name} 没有管理或协调项目的经历",
    ("speaks_english", True): "{name} 能够用英语进行工作沟通",
    ("speaks_english", False): "{name} 不能用英语进行工作沟通",
    ("has_certificate", True): "{name} 持有相关专业证书",
    ("has_certificate", False): "{name} 没有相关专业证书",
    ("has_research_experience", True): "{name} 参与过研究项目",
    ("has_research_experience", False): "{name} 没有研究项目经历",
    ("has_data_analysis_experience", True): "{name} 做过数据分析工作",
    ("has_data_analysis_experience", False): "{name} 没有实际数据分析经历",
    ("has_project_experience", True): "{name} 参与过项目执行",
    ("has_project_experience", False): "{name} 没有参与过项目执行",
    ("available_monday", True): "{name} 周一可以参与工作",
    ("available_monday", False): "{name} 周一无法参与工作",
    ("available_tuesday", True): "{name} 周二可以参与工作",
    ("available_tuesday", False): "{name} 周二无法参与工作",
    ("available_morning", True): "{name} 上午可以参与工作",
    ("available_morning", False): "{name} 上午无法参与工作",
    ("available_afternoon", True): "{name} 下午可以参与工作",
    ("available_afternoon", False): "{name} 下午无法参与工作",
    ("available_weekend", True): "{name} 周末可以参与工作",
    ("available_weekend", False): "{name} 周末无法参与工作",
    ("available_next_month", True): "{name} 下个月可以加入项目",
    ("available_next_month", False): "{name} 下个月无法加入项目",
    ("has_conflict", True): "{name} 与项目存在利益冲突",
    ("has_conflict", False): "{name} 不存在项目相关的利益冲突",
    ("requires_remote", True): "{name} 只接受远程参与安排",
    ("requires_remote", False): "{name} 不要求只能远程参与",
    ("can_work_remote", True): "{name} 能够远程工作",
    ("can_work_remote", False): "{name} 不能远程工作",
    ("can_work_onsite", True): "{name} 能够现场参与工作",
    ("can_work_onsite", False): "{name} 不能现场参与工作",
    ("exceeds_budget", True): "{name} 的预计成本会超出项目预算",
    ("exceeds_budget", False): "{name} 的预计成本在项目预算内",
    ("needs_supervision", True): "{name} 需要额外监督才能完成工作",
    ("needs_supervision", False): "{name} 不需要额外监督也能完成工作",
    ("has_schedule_conflict", True): "{name} 存在与项目安排冲突的日程",
    ("has_schedule_conflict", False): "{name} 不存在日程冲突",
    ("requires_extra_equipment", True): "{name} 需要额外专用设备支持",
    ("requires_extra_equipment", False): "{name} 不需要额外专用设备支持",
    ("has_domain_knowledge", True): "{name} 熟悉相关项目领域",
    ("has_domain_knowledge", False): "{name} 不熟悉相关项目领域",
    ("has_teamwork_experience", True): "{name} 有团队协作经验",
    ("has_teamwork_experience", False): "{name} 缺少团队协作经验",
    ("has_client_communication_experience", True): "{name} 有客户沟通经验",
    ("has_client_communication_experience", False): "{name} 没有客户沟通经验",
    ("prefers_long_term_project", True): "{name} 偏好长期项目",
    ("prefers_long_term_project", False): "{name} 不偏好长期项目",
    ("willing_to_travel", True): "{name} 愿意出差",
    ("willing_to_travel", False): "{name} 不愿意出差",
    ("accepts_flexible_hours", True): "{name} 接受灵活工时安排",
    ("accepts_flexible_hours", False): "{name} 不接受灵活工时安排",
    ("has_security_clearance", True): "{name} 具备安全许可",
    ("has_security_clearance", False): "{name} 不具备安全许可",
    ("has_prior_training", True): "{name} 完成过相关培训",
    ("has_prior_training", False): "{name} 没有完成相关培训",
    ("has_local_work_permit", True): "{name} 具有本地工作许可",
    ("has_local_work_permit", False): "{name} 没有本地工作许可",
    ("can_work_independently", True): "{name} 能够独立工作",
    ("can_work_independently", False): "{name} 不能独立完成工作",
    ("has_public_speaking_experience", True): "{name} 有公开表达或演讲经验",
    ("has_public_speaking_experience", False): "{name} 没有公开表达或演讲经验",
    ("familiar_with_statistics", True): "{name} 熟悉统计方法",
    ("familiar_with_statistics", False): "{name} 不熟悉统计方法",
    ("has_quality_assurance_experience", True): "{name} 有质量保证经验",
    ("has_quality_assurance_experience", False): "{name} 没有质量保证经验",
    ("prefers_on_site_work", True): "{name} 偏好现场工作",
    ("prefers_on_site_work", False): "{name} 不偏好现场工作",
}


def _has_chinese(text: str) -> bool:
    return bool(CHINESE_RE.search(text))


def _join_facts(facts: list[str]) -> str:
    if not facts:
        return ""
    if len(facts) == 1:
        return f"{facts[0]}。"
    if len(facts) == 2:
        return f"{facts[0]}，并且{facts[1]}。"
    midpoint = len(facts) // 2
    first = "，".join(facts[:midpoint])
    second = "，".join(facts[midpoint:])
    return f"{first}。另外，{second}。"


def _translate_constraint(constraint: dict[str, Any]) -> dict[str, Any]:
    translated = dict(constraint)
    key = (str(constraint["attribute"]), bool(constraint["required_value"]))
    try:
        translated["natural_language"] = CONSTRAINT_ZH[key]
    except KeyError as exc:
        raise ValueError(f"Missing Chinese constraint translation for {key}") from exc
    return translated


def _translate_entity(label: str, entity: dict[str, Any]) -> tuple[dict[str, Any], str]:
    translated = copy.deepcopy(entity)
    name = str(entity["name"])
    attributes = entity["attributes"]
    display_order = [str(attribute) for attribute in entity["display_order"]]
    facts: list[dict[str, Any]] = []
    fact_texts: list[str] = []
    for attribute in display_order:
        value = bool(attributes[attribute])
        key = (attribute, value)
        try:
            text = FACT_ZH[key].format(name=name)
        except KeyError as exc:
            raise ValueError(f"Missing Chinese candidate translation for {label} {key}") from exc
        facts.append({"attribute": attribute, "value": value, "text": text})
        fact_texts.append(text)
    translated["displayed_facts"] = facts
    return translated, _join_facts(fact_texts)


def translate_sample(sample: dict[str, Any]) -> dict[str, Any]:
    """Translate one English sample into a Chinese view while preserving logic."""
    translated = copy.deepcopy(sample)
    source_item_id = str(sample["item_id"])
    base_item_id = str(sample["base_item_id"])
    translated["item_id"] = f"{base_item_id}_zh_view"
    translated["generator_version"] = "3.0-en-zh-view"
    translated["language"] = "zh"
    translated["variant_type"] = "zh_view"
    translated["source_item_id"] = source_item_id
    translated["constraints"] = [_translate_constraint(dict(constraint)) for constraint in sample["constraints"]]

    entities: dict[str, dict[str, Any]] = {}
    options: dict[str, str] = {}
    for label in ("A", "B", "C", "D"):
        entity, option_text = _translate_entity(label, sample["entities"][label])
        entities[label] = entity
        options[label] = option_text
    translated["entities"] = entities
    translated["options"] = options

    intro = SCENARIO_INTROS.get(str(sample["scenario"]), "请根据以下要求选择唯一符合条件的候选人。")
    ending = SCENARIO_ENDINGS.get(str(sample["scenario"]), "哪位候选人满足全部要求？")
    constraint_lines = "\n".join(
        f"{index}. {constraint['natural_language']}"
        for index, constraint in enumerate(translated["constraints"], start=1)
    )
    option_lines = "\n".join(f"{label}. {options[label]}" for label in ("A", "B", "C", "D"))
    translated["question"] = (
        f"{intro}\n"
        "被选中的人必须满足以下全部要求：\n\n"
        "要求：\n"
        f"{constraint_lines}\n\n"
        "候选人：\n"
        f"{option_lines}\n\n"
        f"{ending}"
    )
    translated.setdefault("metadata", {})
    translated["metadata"] = dict(translated["metadata"])
    translated["metadata"]["view_only"] = True
    translated["metadata"]["source_language"] = "en"
    translated["metadata"]["translation_note"] = "Chinese read-only rendering from pilot_en_v3 structured fields."
    return translated


def validate_translation_pair(source: dict[str, Any], translated: dict[str, Any]) -> None:
    """Check that translation changed only view text and preserved formal logic."""
    if translated["source_item_id"] != source["item_id"]:
        raise ValueError(f"{translated['item_id']} has wrong source_item_id")
    for field in (
        "base_item_id",
        "task_family",
        "task_type",
        "scenario",
        "option_closeness",
        "structural_complexity",
        "empirical_difficulty",
        "gold_answer",
        "option_constraint_matrix",
        "option_violation_signature",
    ):
        if translated[field] != source[field]:
            raise ValueError(f"{translated['item_id']} changed formal field {field}")
    for source_constraint, translated_constraint in zip(source["constraints"], translated["constraints"]):
        for field in ("id", "attribute", "required_value", "type"):
            if translated_constraint[field] != source_constraint[field]:
                raise ValueError(f"{translated['item_id']} changed constraint field {field}")
        if not _has_chinese(str(translated_constraint["natural_language"])):
            raise ValueError(f"{translated['item_id']} has untranslated constraint text")
    for label in ("A", "B", "C", "D"):
        if not _has_chinese(str(translated["options"][label])):
            raise ValueError(f"{translated['item_id']} option {label} has no Chinese text")
        source_entity = source["entities"][label]
        translated_entity = translated["entities"][label]
        for field in ("name", "attributes", "display_order", "expected_violation_signature", "is_gold"):
            if translated_entity[field] != source_entity[field]:
                raise ValueError(f"{translated['item_id']} changed entity {label} field {field}")
    if not _has_chinese(str(translated["question"])):
        raise ValueError(f"{translated['item_id']} question has no Chinese text")


def render_markdown(records: list[dict[str, Any]]) -> str:
    """Render all translated samples into a human-readable Markdown file."""
    lines = [
        "# Pilot English v3 Chinese View",
        "",
        "说明：这是 `pilot_en_v3.jsonl` 的中文阅读版，只用于人工查看。Gold、约束 ID、矩阵和 violation signature 均来自英文原始数据。",
        "",
    ]
    for index, record in enumerate(records, start=1):
        lines.extend(
            [
                f"## {index}. {record['item_id']}",
                "",
                f"- source: `{record['source_item_id']}`",
                f"- scenario: `{record['scenario']}`",
                f"- option_closeness: `{record['option_closeness']}`",
                f"- structural_complexity: `{record['structural_complexity']}`",
                f"- gold: `{record['gold_answer']}`",
                "",
                record["question"],
                "",
                "约束与 violation signature：",
                "",
            ]
        )
        for constraint in record["constraints"]:
            lines.append(
                f"- `{constraint['id']}` `{constraint['attribute']}={constraint['required_value']}`："
                f"{constraint['natural_language']}"
            )
        lines.append("")
        for label in ("A", "B", "C", "D"):
            signature = record["option_violation_signature"][label]
            lines.append(f"- `{label}` violation: `{signature}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a Chinese view of the English v3 pilot dataset.")
    parser.add_argument("--input", default="data/pilot_en_v3.jsonl")
    parser.add_argument("--output", default="data/pilot_en_v3_zh_view.jsonl")
    parser.add_argument("--markdown-output", default="data/pilot_en_v3_zh_view.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = ROOT / args.input
    output_path = ROOT / args.output
    markdown_path = ROOT / args.markdown_output
    sources = read_jsonl(source_path)
    translated = [translate_sample(sample) for sample in sources]
    for source, record in zip(sources, translated):
        validate_translation_pair(source, record)
    write_jsonl(output_path, translated)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(translated), encoding="utf-8")
    print(json.dumps({
        "source": args.input,
        "output": args.output,
        "markdown_output": args.markdown_output,
        "items": len(translated),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
