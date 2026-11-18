# 逐例诊断差异审计

这是自动比对后的输出文本审计，不是独立人工标注或模型内部机制解释。
主评分规则未变；一例可以出现在多个差异类别，数量不可相加作总错误数。

|划分|方法|差异|数量|
|---|---|---|---|
|dev|M0|attribute_binding|4|
|dev|M0|evidence_rule_or_version_binding|6|
|dev|M0|message_classification|6|
|dev|M0|missing_valid_diagnostic|6|
|dev|M0|quote_span|1|
|dev|M1|attribute_binding|5|
|dev|M1|evidence_rule_or_version_binding|5|
|dev|M1|message_classification|7|
|dev|M1|missing_valid_diagnostic|7|
|dev|M1|quote_span|1|
|dev|M2|evidence_rule_or_version_binding|1|
|dev|M2|message_classification|7|
|dev|M2|missing_valid_diagnostic|7|

## dev / M0 / A2 / t_5e770ba85db79e4d
差异：evidence_rule_or_version_binding
公开发言：
- m_4379aa010f54e4 agent_1 T1 R0: Candidate A is unavailable on Tuesday. For candidate A, I apply C3 as requiring available_tuesday = false. Therefore I retain candidate A.
参考主张：
```json
[
  {
    "active_version": 1,
    "agent_id": "agent_1",
    "attribute": "available_tuesday",
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "end": 106,
    "evidence_stage": 1,
    "kind": "rule",
    "labels": [
      "R"
    ],
    "message_id": "m_4379aa010f54e4",
    "offset_repaired": false,
    "quote": "For candidate A, I apply C3 as requiring available_tuesday = false.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": "C3",
    "stance": "asserted",
    "start": 39,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null,
    "value": false
  }
]
```
Judge 主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_1",
    "attribute": "available_tuesday",
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "end": 106,
    "evidence_stage": 1,
    "kind": "rule",
    "labels": [
      "R"
    ],
    "message_id": "m_4379aa010f54e4",
    "offset_repaired": false,
    "quote": "For candidate A, I apply C3 as requiring available_tuesday = false.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": "C3",
    "stance": "asserted",
    "start": 39,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null
  }
]
```

## dev / M1 / A2 / t_5e770ba85db79e4d
差异：evidence_rule_or_version_binding
公开发言：
- m_4379aa010f54e4 agent_1 T1 R0: Candidate A is unavailable on Tuesday. For candidate A, I apply C3 as requiring available_tuesday = false. Therefore I retain candidate A.
参考主张：
```json
[
  {
    "active_version": 1,
    "agent_id": "agent_1",
    "attribute": "available_tuesday",
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "end": 106,
    "evidence_stage": 1,
    "kind": "rule",
    "labels": [
      "R"
    ],
    "message_id": "m_4379aa010f54e4",
    "offset_repaired": false,
    "quote": "For candidate A, I apply C3 as requiring available_tuesday = false.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": "C3",
    "stance": "asserted",
    "start": 39,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null,
    "value": false
  }
]
```
Judge 主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_1",
    "attribute": "available_tuesday",
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "end": 106,
    "evidence_stage": 1,
    "kind": "rule",
    "labels": [
      "R"
    ],
    "message_id": "m_4379aa010f54e4",
    "offset_repaired": false,
    "quote": "For candidate A, I apply C3 as requiring available_tuesday = false.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": "C3",
    "stance": "asserted",
    "start": 39,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null
  }
]
```

## dev / M1 / A3 / t_79126c8888f190c1
差异：attribute_binding
公开发言：
- m_9f681f7c5cb7d9 agent_1 T1 R0: Candidate A is unavailable on Tuesday. For candidate A, I apply C3 as requiring available_tuesday = true. Therefore I retain candidate A.
参考主张：
```json
[
  {
    "active_version": 1,
    "agent_id": "agent_1",
    "attribute": "available_tuesday",
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000184:A:available_tuesday:v1"
    ],
    "current_error": true,
    "decision": "retain",
    "end": 137,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "I"
    ],
    "message_id": "m_9f681f7c5cb7d9",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate A.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "stance": "asserted",
    "start": 106,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null
  }
]
```
Judge 主张：
```json
[
  {
    "active_version": 1,
    "agent_id": "agent_1",
    "attribute": null,
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000184:A:available_tuesday:v1"
    ],
    "current_error": true,
    "end": 137,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "I"
    ],
    "message_id": "m_9f681f7c5cb7d9",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate A.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": null,
    "stance": "asserted",
    "start": 106,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null
  }
]
```

## dev / M0 / A4 / t_8bc3d9af903caac4
差异：attribute_binding
公开发言：
- m_367f420551d784 agent_1 T1 R0: Therefore I retain candidate A.
参考主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_1",
    "attribute": null,
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "decision": "retain",
    "end": 31,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_367f420551d784",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate A.",
    "required_rule_ids": [],
    "round": 0,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": "insufficient_explicit_premises"
  }
]
```
Judge 主张：
```json
[
  {
    "active_version": 1,
    "agent_id": "agent_1",
    "attribute": "available_tuesday",
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000184:A:available_tuesday:v1"
    ],
    "current_error": true,
    "end": 31,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_367f420551d784",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate A.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": null,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": "The agent retains candidate A even though official evidence states A is unavailable on Tuesday, but the message gives no explicit premise for the retention decision."
  }
]
```

## dev / M1 / A4 / t_8bc3d9af903caac4
差异：attribute_binding
公开发言：
- m_367f420551d784 agent_1 T1 R0: Therefore I retain candidate A.
参考主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_1",
    "attribute": null,
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "decision": "retain",
    "end": 31,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_367f420551d784",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate A.",
    "required_rule_ids": [],
    "round": 0,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": "insufficient_explicit_premises"
  }
]
```
Judge 主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_1",
    "attribute": "available_tuesday",
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000184:A:available_tuesday:v1"
    ],
    "current_error": true,
    "end": 31,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_367f420551d784",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate A.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": null,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": "The retention decision is unsupported and conflicts with the known fact that Casey is unavailable on Tuesday, which violates C3; the message gives no explicit premise to diagnose as F/R/I."
  }
]
```

## dev / M2 / A4 / t_8bc3d9af903caac4
差异：evidence_rule_or_version_binding
公开发言：
- m_367f420551d784 agent_1 T1 R0: Therefore I retain candidate A.
参考主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_1",
    "attribute": null,
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "decision": "retain",
    "end": 31,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_367f420551d784",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate A.",
    "required_rule_ids": [],
    "round": 0,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": "insufficient_explicit_premises"
  }
]
```
Judge 主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_1",
    "attribute": null,
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000184:A:available_tuesday:v1"
    ],
    "current_error": true,
    "end": 31,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_367f420551d784",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate A.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": null,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": "Retaining A conflicts with the active known fact that A is unavailable on Tuesday, and the message supplies no explicit rule or factual premise to support the decision."
  }
]
```

## dev / M0 / A2 / t_2bd5d2187d31dfb2
差异：evidence_rule_or_version_binding
公开发言：
- m_4e7d62408a453d agent_3 T1 R0: Candidate B has not given public presentations before. For candidate B, I apply C3 as requiring has_public_speaking_experience = false. Therefore I retain candidate B.
参考主张：
```json
[
  {
    "active_version": 1,
    "agent_id": "agent_3",
    "attribute": "has_public_speaking_experience",
    "candidate_id": "B",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "end": 135,
    "evidence_stage": 1,
    "kind": "rule",
    "labels": [
      "R"
    ],
    "message_id": "m_4e7d62408a453d",
    "offset_repaired": false,
    "quote": "For candidate B, I apply C3 as requiring has_public_speaking_experience = false.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": "C3",
    "stance": "asserted",
    "start": 55,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null,
    "value": false
  }
]
```
Judge 主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_3",
    "attribute": "has_public_speaking_experience",
    "candidate_id": "B",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "end": 135,
    "evidence_stage": 1,
    "kind": "rule",
    "labels": [
      "R"
    ],
    "message_id": "m_4e7d62408a453d",
    "offset_repaired": false,
    "quote": "For candidate B, I apply C3 as requiring has_public_speaking_experience = false.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": "C3",
    "stance": "asserted",
    "start": 55,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null
  }
]
```

## dev / M2 / A5 / t_879953f266ff04a8
差异：message_classification, missing_valid_diagnostic
公开发言：
- m_bb4521f5e6f3b7 agent_2 T1 R0: Another speaker claimed: "Candidate D can participate on Monday." I reject that claim. Candidate D is unavailable on Monday. For candidate D, I apply C5 as requiring available_monday = true. Therefore I exclude candidate D.
参考主张：
```json
[]
```
Judge 主张：
```json
[]
```

## dev / M2 / A1 / t_7bdc6e6d8c6d26c8
差异：message_classification, missing_valid_diagnostic
公开发言：
- m_741bea3bbf38c0 agent_1 T1 R0: Candidate A can join the project next month. For candidate A, I apply C5 as requiring available_next_month = true. Therefore I retain candidate A.
参考主张：
```json
[
  {
    "active_version": 1,
    "agent_id": "agent_1",
    "attribute": "available_next_month",
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000390:A:available_next_month:v1"
    ],
    "current_error": true,
    "end": 44,
    "evidence_stage": 1,
    "kind": "fact",
    "labels": [
      "F"
    ],
    "message_id": "m_741bea3bbf38c0",
    "offset_repaired": false,
    "quote": "Candidate A can join the project next month.",
    "required_rule_ids": [
      "C5"
    ],
    "round": 0,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null,
    "value": true
  }
]
```
Judge 主张：
```json
[
  {
    "active_version": 1,
    "agent_id": "agent_1",
    "attribute": "available_next_month",
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000390:A:available_next_month:v1"
    ],
    "current_error": true,
    "decision": null,
    "end": 44,
    "evidence_stage": 1,
    "kind": "fact",
    "labels": [
      "F"
    ],
    "message_id": "m_741bea3bbf38c0",
    "offset_repaired": false,
    "quote": "Candidate A can join the project next month.",
    "required_rule_ids": [
      "C5"
    ],
    "round": 0,
    "rule_id": null,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null,
    "value": true
  }
]
```
