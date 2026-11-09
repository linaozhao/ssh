# Metrics and Denominators

Detection uses verified definite positive/negative references. Unsupported or
ambiguous reference cases remain excluded with counts. API/schema failures are
not negative predictions: they miss positive references and do not count as true
negative rejections. Negative strata report judged coverage and end-to-end correct
rejection in addition to false-positive rate among judged cases.

Claim matching is deterministic maximum-cardinality bipartite matching using
message/agent/stage/round, candidate/attribute/rule, and exact span. It does not
look at predicted class. Only preregistered equivalent claims/support may match.
Strict localization additionally checks stance, conflicting evidence and version.
Category scoring happens after matching. Wrong object at the right message is
not an object TP. All applicable reference claims, including missed messages,
remain in recall denominators.

F1 = 2TP/(2TP+FP+FN); zero TP with positive support is zero, not undefined.
Empty applicable support yields null with a reason. Report per-class, micro,
supported-class macro, unresolved and abstentions separately.

Time accuracy includes only references with sufficient history; necessary prior
support is checked separately. Missing-history cases measure unjustified certainty
and retention of uncertainty. Overall message labels do not substitute for each
claim's object-specific temporal evidence.

Dev36 and holdout36 are separate. Paired direct/structured differences report
both-valid count and family means. Shared templates/families are correlated; no
IID confidence interval is reported. Online outputs absent means not_evaluated,
not zero detector accuracy. Mock scores are software_test_only.

Natural MAD reports only program-set/candidate behavior. Four suffix conditions
are paired by family; means require all18 stage/round/agent suffix observations.
No independent human references means natural F/R/I accuracy is not evaluated.
