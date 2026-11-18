# 逐例诊断差异审计

这是自动比对后的输出文本审计，不是独立人工标注或模型内部机制解释。
主评分规则未变；一例可以出现在多个差异类别，数量不可相加作总错误数。

|划分|方法|差异|数量|
|---|---|---|---|
|dev|M0|attribute_binding|6|
|dev|M0|evidence_rule_or_version_binding|14|
|dev|M0|quote_span|3|
|dev|M0|temporal_status_or_history_support|16|
|dev|M1|attribute_binding|5|
|dev|M1|evidence_rule_or_version_binding|7|
|dev|M1|message_or_candidate|4|
|dev|M1|quote_span|3|
|dev|M1|temporal_status_or_history_support|13|
|dev|M2|evidence_rule_or_version_binding|1|
|holdout|M0|attribute_binding|2|
|holdout|M0|evidence_rule_or_version_binding|10|
|holdout|M0|message_or_candidate|1|
|holdout|M0|quote_span|1|
|holdout|M0|temporal_status_or_history_support|18|
|holdout|M1|attribute_binding|4|
|holdout|M1|evidence_rule_or_version_binding|12|
|holdout|M1|message_or_candidate|1|
|holdout|M1|temporal_status_or_history_support|20|

## dev / M1 / A3 / t_74d029a3170890e7
差异：evidence_rule_or_version_binding
公开发言：
- m_23888e3f0ecc63 agent_1 T1 R0: Candidate A is unavailable on Tuesday. For candidate A, I apply C3 as requiring available_tuesday = true. Therefore I retain candidate A.
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
    "message_id": "m_23888e3f0ecc63",
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
    "end": 137,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "I"
    ],
    "message_id": "m_23888e3f0ecc63",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate A.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": "C3",
    "stance": "asserted",
    "start": 106,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null
  }
]
```

## dev / M0 / A4 / t_83e16c802b4a58e2
差异：evidence_rule_or_version_binding
公开发言：
- m_f1819631e417fc agent_1 T1 R0: Therefore I retain candidate A.
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
    "message_id": "m_f1819631e417fc",
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
    "message_id": "m_f1819631e417fc",
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
    "uncertainty_reason": "No explicit premise is given to diagnose the wrong retention decision as F or I; it is an unsupported decision."
  }
]
```

## dev / M1 / A4 / t_83e16c802b4a58e2
差异：attribute_binding
公开发言：
- m_f1819631e417fc agent_1 T1 R0: Therefore I retain candidate A.
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
    "message_id": "m_f1819631e417fc",
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
    "message_id": "m_f1819631e417fc",
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
    "uncertainty_reason": "The message asserts retaining candidate A without stating any supporting premises; active evidence says A is unavailable on Tuesday, while C3 requires Tuesday availability."
  }
]
```

## holdout / M0 / A2 / t_05cc661ce964a0f8
差异：temporal_status_or_history_support
公开发言：
- m_667e83f3bdf4e4 agent_2 T1 R0: Candidate C is unavailable next month. My eligibility test for candidate C under C1 is that available_next_month must be false. My decision is to retain candidate C.
参考主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_2",
    "attribute": "available_next_month",
    "candidate_id": "C",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "end": 127,
    "evidence_stage": 1,
    "kind": "rule",
    "labels": [
      "R"
    ],
    "message_id": "m_667e83f3bdf4e4",
    "offset_repaired": false,
    "quote": "My eligibility test for candidate C under C1 is that available_next_month must be false.",
    "required_rule_ids": [
      "C1"
    ],
    "round": 0,
    "rule_id": "C1",
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
    "agent_id": "agent_2",
    "attribute": "available_next_month",
    "candidate_id": "C",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "end": 127,
    "evidence_stage": 1,
    "kind": "rule",
    "labels": [
      "R"
    ],
    "message_id": "m_667e83f3bdf4e4",
    "offset_repaired": false,
    "quote": "My eligibility test for candidate C under C1 is that available_next_month must be false.",
    "required_rule_ids": [
      "C1"
    ],
    "round": 0,
    "rule_id": "C1",
    "stance": "asserted",
    "start": 39,
    "support_message_ids": [],
    "temporal_status": "newly_introduced",
    "uncertainty_reason": null
  }
]
```

## holdout / M0 / A3 / t_5bb805d945b4c288
差异：quote_span
公开发言：
- m_4c474ff9d1e849 agent_2 T1 R0: Candidate C is unavailable next month. My eligibility test for candidate C under C1 is that available_next_month must be true. My decision is to retain candidate C.
参考主张：
```json
[
  {
    "active_version": 1,
    "agent_id": "agent_2",
    "attribute": "available_next_month",
    "candidate_id": "C",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000202:C:available_next_month:v1"
    ],
    "current_error": true,
    "decision": "retain",
    "end": 164,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "I"
    ],
    "message_id": "m_4c474ff9d1e849",
    "offset_repaired": false,
    "quote": "My decision is to retain candidate C.",
    "required_rule_ids": [
      "C1"
    ],
    "round": 0,
    "stance": "asserted",
    "start": 127,
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
    "agent_id": "agent_2",
    "attribute": "available_next_month",
    "candidate_id": "C",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000202:C:available_next_month:v1"
    ],
    "current_error": true,
    "end": 164,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "I"
    ],
    "message_id": "m_4c474ff9d1e849",
    "offset_repaired": false,
    "quote": "Candidate C is unavailable next month. My eligibility test for candidate C under C1 is that available_next_month must be true. My decision is to retain candidate C.",
    "required_rule_ids": [
      "C1"
    ],
    "round": 0,
    "rule_id": "C1",
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null
  }
]
```

## holdout / M1 / A3 / t_5bb805d945b4c288
差异：temporal_status_or_history_support
公开发言：
- m_4c474ff9d1e849 agent_2 T1 R0: Candidate C is unavailable next month. My eligibility test for candidate C under C1 is that available_next_month must be true. My decision is to retain candidate C.
参考主张：
```json
[
  {
    "active_version": 1,
    "agent_id": "agent_2",
    "attribute": "available_next_month",
    "candidate_id": "C",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000202:C:available_next_month:v1"
    ],
    "current_error": true,
    "decision": "retain",
    "end": 164,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "I"
    ],
    "message_id": "m_4c474ff9d1e849",
    "offset_repaired": false,
    "quote": "My decision is to retain candidate C.",
    "required_rule_ids": [
      "C1"
    ],
    "round": 0,
    "stance": "asserted",
    "start": 127,
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
    "agent_id": "agent_2",
    "attribute": "available_next_month",
    "candidate_id": "C",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000202:C:available_next_month:v1"
    ],
    "current_error": true,
    "end": 164,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "I"
    ],
    "message_id": "m_4c474ff9d1e849",
    "offset_repaired": false,
    "quote": "My decision is to retain candidate C.",
    "required_rule_ids": [
      "C1"
    ],
    "round": 0,
    "rule_id": "C1",
    "stance": "asserted",
    "start": 127,
    "support_message_ids": [],
    "temporal_status": "newly_introduced",
    "uncertainty_reason": null
  }
]
```

## holdout / M0 / A4 / t_a3a71f79215ed9d6
差异：attribute_binding
公开发言：
- m_6b44cad3ff2d64 agent_2 T1 R0: My decision is to retain candidate C.
参考主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_2",
    "attribute": null,
    "candidate_id": "C",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "decision": "retain",
    "end": 37,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_6b44cad3ff2d64",
    "offset_repaired": false,
    "quote": "My decision is to retain candidate C.",
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
    "agent_id": "agent_2",
    "attribute": "available_next_month",
    "candidate_id": "C",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000202:C:available_next_month:v1"
    ],
    "current_error": true,
    "end": 37,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_6b44cad3ff2d64",
    "offset_repaired": false,
    "quote": "My decision is to retain candidate C.",
    "required_rule_ids": [
      "C1"
    ],
    "round": 0,
    "rule_id": null,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": "The decision to retain candidate C is unsupported because the active official evidence says Marley is unavailable next month, which violates required rule C1; no explicit premise explains the decision."
  }
]
```

## holdout / M1 / A4 / t_a3a71f79215ed9d6
差异：attribute_binding
公开发言：
- m_6b44cad3ff2d64 agent_2 T1 R0: My decision is to retain candidate C.
参考主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_2",
    "attribute": null,
    "candidate_id": "C",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "decision": "retain",
    "end": 37,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_6b44cad3ff2d64",
    "offset_repaired": false,
    "quote": "My decision is to retain candidate C.",
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
    "agent_id": "agent_2",
    "attribute": "available_next_month",
    "candidate_id": "C",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000202:C:available_next_month:v1"
    ],
    "current_error": true,
    "end": 37,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_6b44cad3ff2d64",
    "offset_repaired": false,
    "quote": "My decision is to retain candidate C.",
    "required_rule_ids": [
      "C1"
    ],
    "round": 0,
    "rule_id": null,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": "The decision to retain candidate C is unsupported because published evidence says Marley is unavailable next month, violating C1."
  }
]
```

## dev / M0 / A3 / t_b73e69736e3540a7
差异：attribute_binding
公开发言：
- m_79a2b51545ca57 agent_3 T1 R0: Candidate B has not given public presentations before. For candidate B, I apply C3 as requiring has_public_speaking_experience = true. Therefore I retain candidate B.
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
    "conflicting_evidence_ids": [
      "attr_v4_1_000229:B:has_public_speaking_experience:v1"
    ],
    "current_error": true,
    "decision": "retain",
    "end": 166,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "I"
    ],
    "message_id": "m_79a2b51545ca57",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate B.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "stance": "asserted",
    "start": 135,
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
    "agent_id": "agent_3",
    "attribute": null,
    "candidate_id": "B",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000229:B:has_public_speaking_experience:v1"
    ],
    "current_error": true,
    "end": 166,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "I"
    ],
    "message_id": "m_79a2b51545ca57",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate B.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": null,
    "stance": "asserted",
    "start": 135,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": null
  }
]
```

## dev / M0 / A4 / t_bbd690d0d2411aad
差异：attribute_binding
公开发言：
- m_1e43572516cdf5 agent_3 T1 R0: Therefore I retain candidate B.
参考主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_3",
    "attribute": null,
    "candidate_id": "B",
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
    "message_id": "m_1e43572516cdf5",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate B.",
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
    "agent_id": "agent_3",
    "attribute": "has_public_speaking_experience",
    "candidate_id": "B",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000229:B:has_public_speaking_experience:v1"
    ],
    "current_error": true,
    "end": 31,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_1e43572516cdf5",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate B.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": null,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": "The decision to retain Blair is unsupported and conflicts with the active known fact that Blair lacks public speaking experience, which violates rule C3."
  }
]
```

## dev / M1 / A4 / t_bbd690d0d2411aad
差异：attribute_binding
公开发言：
- m_1e43572516cdf5 agent_3 T1 R0: Therefore I retain candidate B.
参考主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_3",
    "attribute": null,
    "candidate_id": "B",
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
    "message_id": "m_1e43572516cdf5",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate B.",
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
    "agent_id": "agent_3",
    "attribute": "has_public_speaking_experience",
    "candidate_id": "B",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000229:B:has_public_speaking_experience:v1"
    ],
    "current_error": true,
    "end": 31,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_1e43572516cdf5",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate B.",
    "required_rule_ids": [
      "C3"
    ],
    "round": 0,
    "rule_id": "C3",
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": "No explicit rationale is given; retaining Blair conflicts with active evidence that Blair lacks the required public speaking experience."
  }
]
```

## holdout / M1 / A2 / t_4135bcef0d947602
差异：temporal_status_or_history_support
公开发言：
- m_c45dcdac4644f7 agent_1 T1 R0: Candidate A lacks local work authorization. My eligibility test for candidate A under C1 is that has_local_work_permit must be false. My decision is to retain candidate A.
参考主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_1",
    "attribute": "has_local_work_permit",
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "end": 133,
    "evidence_stage": 1,
    "kind": "rule",
    "labels": [
      "R"
    ],
    "message_id": "m_c45dcdac4644f7",
    "offset_repaired": false,
    "quote": "My eligibility test for candidate A under C1 is that has_local_work_permit must be false.",
    "required_rule_ids": [
      "C1"
    ],
    "round": 0,
    "rule_id": "C1",
    "stance": "asserted",
    "start": 44,
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
    "attribute": "has_local_work_permit",
    "candidate_id": "A",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [],
    "current_error": true,
    "end": 133,
    "evidence_stage": 1,
    "kind": "rule",
    "labels": [
      "R"
    ],
    "message_id": "m_c45dcdac4644f7",
    "offset_repaired": false,
    "quote": "My eligibility test for candidate A under C1 is that has_local_work_permit must be false.",
    "required_rule_ids": [
      "C1"
    ],
    "round": 0,
    "rule_id": "C1",
    "stance": "asserted",
    "start": 44,
    "support_message_ids": [],
    "temporal_status": "newly_introduced",
    "uncertainty_reason": null
  }
]
```

## dev / M2 / A4 / t_135611f88f902930
差异：evidence_rule_or_version_binding
公开发言：
- m_af464b203238e9 agent_3 T1 R0: Therefore I retain candidate D.
参考主张：
```json
[
  {
    "active_version": null,
    "agent_id": "agent_3",
    "attribute": null,
    "candidate_id": "D",
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
    "message_id": "m_af464b203238e9",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate D.",
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
    "agent_id": "agent_3",
    "attribute": null,
    "candidate_id": "D",
    "cited_evidence_ids": [],
    "cited_version": null,
    "conflicting_evidence_ids": [
      "attr_v4_1_000458:D:has_data_analysis_experience:v1"
    ],
    "current_error": true,
    "end": 31,
    "evidence_stage": 1,
    "kind": "decision",
    "labels": [
      "unresolved"
    ],
    "message_id": "m_af464b203238e9",
    "offset_repaired": false,
    "quote": "Therefore I retain candidate D.",
    "required_rule_ids": [
      "C5"
    ],
    "round": 0,
    "rule_id": null,
    "stance": "asserted",
    "start": 0,
    "support_message_ids": [],
    "temporal_status": "unknown",
    "uncertainty_reason": "No explicit premise is given for retaining D, and the active known evidence says D lacks practical data analysis experience, which violates C5."
  }
]
```
