# Single-Agent Screening Report

## Run Summary
```json
{
  "all_successful_runs_have_valid_option": true,
  "api_failures": 0,
  "attempted_runs": 600,
  "combined_accuracy": 0.9333333333333333,
  "combined_mean_confidence": 0.9132721202003338,
  "combined_parse_success_rate": 0.9983333333333333,
  "completed_runs": 600,
  "dataset_items": 100,
  "duplicate_run_count": 0,
  "expected_runs": 600,
  "fallback_parse_success_rate": 0.0,
  "missing_run_count": 0,
  "parse_failures": 1,
  "strict_json_success_rate": 0.9983333333333333,
  "total_parse_success_rate": 0.9983333333333333,
  "unique_run_keys": 600,
  "valid_runs": 599
}
```

## Dataset Difficulty
1. Qwen overall accuracy: `1.000`.
2. Llama overall accuracy: `0.867`.
3. Combined accuracy: `0.933`.
4. `stable_correct`: `83`.
5. `mildly_vulnerable`: `4`.
6. `mixed_correctness`: `13`.
7. `mostly_wrong`: `0`.

## Natural Disagreement
8. Items with any natural disagreement: `17`.
9. Items with cross-model disagreement: `17`.
10. Items with Qwen internal disagreement: `0`.
11. Items with Llama internal disagreement: `8`.

## Diagnostic Value
12. Total wrong answers: `39`.
13. Share of wrong answers violating exactly one constraint: `0.821`.
14. Most frequent raw attributes for wrong answers:
```json
{
  "accepts_flexible_hours": 5,
  "available_afternoon": 0,
  "available_monday": 0,
  "available_morning": 0,
  "available_next_month": 0,
  "available_tuesday": 10,
  "available_weekend": 3,
  "can_work_independently": 0,
  "can_work_onsite": 8,
  "can_work_remote": 1,
  "has_certificate": 2,
  "has_client_communication_experience": 1,
  "has_local_work_permit": 2,
  "has_management_experience": 3,
  "has_ml_experience": 3,
  "has_programming_experience": 1,
  "has_schedule_conflict": 3,
  "has_security_clearance": 1,
  "has_teamwork_experience": 1,
  "needs_supervision": 2
}
```
15. Most vulnerable normalized attributes:
```json
{
  "accepts_flexible_hours": 0.046296296296296294,
  "available_afternoon": 0.0,
  "available_monday": 0.0,
  "available_morning": 0.0,
  "available_next_month": 0.0,
  "available_tuesday": 0.09259259259259259,
  "available_weekend": 0.03571428571428571,
  "can_work_independently": 0.0,
  "can_work_onsite": 0.07407407407407407,
  "can_work_remote": 0.00980392156862745,
  "has_certificate": 0.047619047619047616,
  "has_client_communication_experience": 0.016666666666666666,
  "has_local_work_permit": 0.041666666666666664,
  "has_management_experience": 0.045454545454545456,
  "has_ml_experience": 0.07142857142857142,
  "has_programming_experience": 0.023809523809523808,
  "has_schedule_conflict": 0.02631578947368421,
  "has_security_clearance": 0.018518518518518517,
  "has_teamwork_experience": 0.020833333333333332,
  "needs_supervision": 0.020833333333333332
}
```
16. Constraint type/category error summary:
```json
{
  "category_violation_counts": {
    "ability": 18,
    "availability": 13,
    "preference": 5,
    "qualification": 5,
    "restriction": 5
  },
  "required_value_violation_counts": {
    "required_false": 5,
    "required_true": 41
  }
}
```

## Difficulty Design
17. option_closeness accuracy relationship: `predictive_in_expected_direction`.
```json
{
  "accuracy_by_level": {
    "easy": 0.975,
    "hard": 0.9,
    "medium": 0.9305555555555556
  },
  "accuracy_span": 0.07499999999999996,
  "interpretation": "predictive_in_expected_direction",
  "monotonic_expected_order": true
}
```
18. 3/4/5 constraint accuracy relationship: `mixed_or_non_monotonic_relationship`.
```json
{
  "accuracy_by_level": {
    "3": 0.9458333333333333,
    "4": 0.9,
    "5": 0.975
  },
  "accuracy_span": 0.07499999999999996,
  "interpretation": "mixed_or_non_monotonic_relationship",
  "monotonic_expected_order": false
}
```
19. structural_complexity relationship with empirical difficulty: `mixed_or_non_monotonic_relationship`.
```json
{
  "accuracy_by_level": {
    "high": 0.975,
    "low": 0.9458333333333333,
    "medium": 0.9
  },
  "accuracy_span": 0.07499999999999996,
  "interpretation": "mixed_or_non_monotonic_relationship",
  "monotonic_expected_order": false
}
```
20. Current generator difficulty validity: treat as useful only if the grouped relationships above are monotonic and the span is non-trivial; otherwise it should be considered structural metadata rather than empirical difficulty.

## Suitability For MAD
21. High-priority MAD candidates: `14`.
22. Medium-priority MAD candidates: `3`.
23. Items with correct + wrong coexistence: `17`.
24. Single-constraint wrong answers observed: `32`.
25. Current recommendation: The data show base competence plus natural instability, and many mistakes are single-constraint violations.

## Model-Level Statistics
```json
{
  "llama": {
    "accuracy": 0.8666666666666667,
    "accuracy_by_run_id": {
      "1": {
        "accuracy": 0.87,
        "parse_success_rate": 1.0,
        "runs": 100
      },
      "2": {
        "accuracy": 0.87,
        "parse_success_rate": 1.0,
        "runs": 100
      },
      "3": {
        "accuracy": 0.86,
        "parse_success_rate": 0.99,
        "runs": 100
      }
    },
    "accuracy_by_seed": {
      "11": {
        "accuracy": 0.87,
        "parse_success_rate": 1.0,
        "runs": 100
      },
      "22": {
        "accuracy": 0.87,
        "parse_success_rate": 1.0,
        "runs": 100
      },
      "33": {
        "accuracy": 0.86,
        "parse_success_rate": 0.99,
        "runs": 100
      }
    },
    "answer_distribution": {
      "A": 80,
      "B": 78,
      "C": 57,
      "D": 84,
      "invalid": 1
    },
    "fallback_parse_success_rate": 0.0,
    "mean_confidence": 0.9306020066889632,
    "parse_success_rate": 0.9966666666666667,
    "seed_agreement_rate": 0.92,
    "strict_json_success_rate": 0.9966666666666667,
    "total_parse_success_rate": 0.9966666666666667,
    "total_runs": 300
  },
  "qwen": {
    "accuracy": 1.0,
    "accuracy_by_run_id": {
      "1": {
        "accuracy": 1.0,
        "parse_success_rate": 1.0,
        "runs": 100
      },
      "2": {
        "accuracy": 1.0,
        "parse_success_rate": 1.0,
        "runs": 100
      },
      "3": {
        "accuracy": 1.0,
        "parse_success_rate": 1.0,
        "runs": 100
      }
    },
    "accuracy_by_seed": {
      "11": {
        "accuracy": 1.0,
        "parse_success_rate": 1.0,
        "runs": 100
      },
      "22": {
        "accuracy": 1.0,
        "parse_success_rate": 1.0,
        "runs": 100
      },
      "33": {
        "accuracy": 1.0,
        "parse_success_rate": 1.0,
        "runs": 100
      }
    },
    "answer_distribution": {
      "A": 75,
      "B": 75,
      "C": 75,
      "D": 75,
      "invalid": 0
    },
    "fallback_parse_success_rate": 0.0,
    "mean_confidence": 0.896,
    "parse_success_rate": 1.0,
    "seed_agreement_rate": 1.0,
    "strict_json_success_rate": 1.0,
    "total_parse_success_rate": 1.0,
    "total_runs": 300
  }
}
```

## Grouped Accuracy
```json
{
  "gold_position": {
    "A": {
      "accuracy": 0.98,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.8929530201342281,
      "parse_success_rate": 0.9933333333333333,
      "strict_json_success_rate": 0.9933333333333333,
      "total_runs": 150
    },
    "B": {
      "accuracy": 0.9466666666666667,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9176666666666667,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 150
    },
    "C": {
      "accuracy": 0.8466666666666667,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9129999999999999,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 150
    },
    "D": {
      "accuracy": 0.96,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9293333333333333,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 150
    }
  },
  "has_negative_risk_constraint": {
    "false": {
      "accuracy": 0.9320987654320988,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9167182662538699,
      "parse_success_rate": 0.9969135802469136,
      "strict_json_success_rate": 0.9969135802469136,
      "total_runs": 324
    },
    "true": {
      "accuracy": 0.9347826086956522,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9092391304347825,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 276
    }
  },
  "model": {
    "llama": {
      "accuracy": 0.8666666666666667,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9306020066889632,
      "parse_success_rate": 0.9966666666666667,
      "strict_json_success_rate": 0.9966666666666667,
      "total_runs": 300
    },
    "qwen": {
      "accuracy": 1.0,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.896,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 300
    }
  },
  "num_constraints": {
    "3": {
      "accuracy": 0.9458333333333333,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.91875,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 240
    },
    "4": {
      "accuracy": 0.9,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9081589958158995,
      "parse_success_rate": 0.9958333333333333,
      "strict_json_success_rate": 0.9958333333333333,
      "total_runs": 240
    },
    "5": {
      "accuracy": 0.975,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9125,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 120
    }
  },
  "option_closeness": {
    "easy": {
      "accuracy": 0.975,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9125,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 120
    },
    "hard": {
      "accuracy": 0.9,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9170833333333334,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 120
    },
    "medium": {
      "accuracy": 0.9305555555555556,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9122562674094707,
      "parse_success_rate": 0.9972222222222222,
      "strict_json_success_rate": 0.9972222222222222,
      "total_runs": 360
    }
  },
  "scenario": {
    "availability_selection": {
      "accuracy": 0.9090909090909091,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9047979797979798,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 198
    },
    "expert_recruitment": {
      "accuracy": 0.9411764705882353,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.917156862745098,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 204
    },
    "project_assignment": {
      "accuracy": 0.9494949494949495,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9177664974619288,
      "parse_success_rate": 0.9949494949494949,
      "strict_json_success_rate": 0.9949494949494949,
      "total_runs": 198
    }
  },
  "structural_complexity": {
    "high": {
      "accuracy": 0.975,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9125,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 120
    },
    "low": {
      "accuracy": 0.9458333333333333,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.91875,
      "parse_success_rate": 1.0,
      "strict_json_success_rate": 1.0,
      "total_runs": 240
    },
    "medium": {
      "accuracy": 0.9,
      "fallback_parse_success_rate": 0.0,
      "mean_confidence": 0.9081589958158995,
      "parse_success_rate": 0.9958333333333333,
      "strict_json_success_rate": 0.9958333333333333,
      "total_runs": 240
    }
  }
}
```

## Screening Category Distribution
```json
{
  "mildly_vulnerable": 4,
  "mixed_correctness": 13,
  "stable_correct": 83
}
```

## MAD Priority Distribution
```json
{
  "high": 14,
  "low": 83,
  "medium": 3
}
```

## Final Result
RESULT: SUITABLE FOR BASELINE MAD PILOT
