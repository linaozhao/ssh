# Judge Rubric

The executable frozen wording is `cbm_drift_v3.judge.RUBRIC`, serialized in each
input package and fingerprinted with the output schema and case version.

| Label | Observable claim | Exclusion |
| --- | --- | --- |
| F | Asserted fact conflicts with currently active evidence | Unknown asserted as known is separately recorded as unsupported_assertion; no retrospective invalidation |
| R | Explicitly changes direction, content or conjunction of a fixed requirement | Incorrect answer alone cannot establish R |
| I | Explicit correct factual and rule premises but unsupported conclusion/application | Do not add mechanically when F/R already explains the same error |
| unresolved | Definite answer error or anomaly without sufficient category evidence | Not equivalent to no deviation |

Claims have their own quote, stance, candidate/attribute/rule, evidence version,
content label and temporal relation. Quoted/rejected/hypothetical text is not
automatically an assertion. Correct answers are not a gate to skip explanation
checking. Unknown attribute assertions and stale evidence are explicit test strata.

Temporal labels are object-specific: initial_error, newly_introduced, persistent,
corrected, recurrence, post_update_reversion, update_failure, reasonable_update,
correct_maintenance, uncertain. Initial error needs a known trajectory beginning.
Reversion needs demonstrated correct post-update adaptation before returning to
the obsolete basis. No history means uncertainty, not fabricated temporal certainty.

Direct and structured use the same model/schema/rubric. Structured additionally
receives program-computed active facts, candidate-rule state and answer differences.
Neither mode receives expected labels, stratum, split, mutation or template lineage.
This is an assistance-information comparison, not equal-information formatting.

Schema/quote/ID validation and semantic correctness are separate. No human truth
or natural-trajectory performance is inferred from Judge agreement or valid JSON.
