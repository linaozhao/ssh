# Discarded 16384-token offset-computation preflight

This directory preserves the third DeepSeek-V4-Pro preflight attempt and is
excluded from the formal Judge experiment.

The same target message was tested once per protocol. The direct protocol
completed with valid JSON after 9,479 reasoning tokens. The structured protocol
used all 16,384 completion tokens as reasoning and returned no final JSON. Its
reasoning trace repeatedly recalculated exact quote offsets. Since offsets are
deterministically derivable from an exact quote, the next protocol removes
offset calculation from the model output and derives unique offsets in code.

A third request was interrupted after this systematic issue was established;
its completion state is unknown and it has no atomic result record.
