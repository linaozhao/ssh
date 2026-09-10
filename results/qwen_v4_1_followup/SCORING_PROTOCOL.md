# Qwen v4.1 Follow-up Scoring Protocol

## Frozen response protocol

The model is instructed to return a JSON object whose `answer` value is exactly
one of `A`, `B`, `C`, or `D`. Full JSON compliance additionally requires a
string `reasoning` field and a numeric `confidence` in `[0, 1]`.

## Separate format and semantic scores

- `json_compliant` records complete protocol compliance.
- `strict_answer_format` requires an A-D value in the `answer` field.
- `answer_extractable` records whether one unambiguous candidate can be mapped.
- `correct` uses the extracted candidate label and the frozen dataset Gold.
- `strict_format_correct` additionally requires `strict_answer_format=true`.

An exact full candidate name in the `answer` field may be mapped to its label
using only the four names in that question. This keeps a semantically clear
answer scoreable while retaining `json_compliant=false` and
`strict_answer_format=false`. Gold labels and reasoning text are never used to
infer a name mapping.

Fallback parsing accepts only an explicit, unambiguous final-answer declaration
or answer field. Ordinary occurrences such as “Option A fails” or “Candidate B
should be checked” are not treated as final answers. Conflicting labels, names,
or multiple selections remain unrecognized and the raw response is preserved.

## Deterministic constraint scoring

For every extracted label, correctness and
`selected_option_violation_signature` are read directly from the frozen item.
No model is asked to identify its own violated constraints.

Parser revision: `qwen-v4.1-name-aware-parser-2`.
