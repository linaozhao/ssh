# Discarded prompt-v1.1 responses

Prompt v1.1 correctly hid every internal condition label, but its
`A_original` request removed the confidence field used by the project's frozen
single-choice prompt. The set-valued conditions intentionally omit confidence;
the original static control must preserve the prior three-field protocol.

These partial responses and interim analyses are retained for auditability and
excluded from all final statistics. Prompt v1.2 changes only `A_original` back
to `answer`, `reasoning`, and `confidence`; the set protocol remains
`candidates` plus `reasoning`.
