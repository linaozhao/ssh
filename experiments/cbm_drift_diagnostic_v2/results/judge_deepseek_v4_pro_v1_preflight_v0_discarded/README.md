# Discarded 4096-token preflight

This directory preserves the first TokenPlan DeepSeek-V4-Pro preflight protocol. It is not
mixed with the formal experiment.

- Configuration: thinking enabled, reasoning effort low, `max_tokens=4096`.
- Seven responses were durably recorded; a further request was in flight when the run was
  manually stopped and its completion state is unknown.
- Five of seven recorded responses ended with `finish_reason=length`. In each truncated
  response all 4096 completion tokens were reported as reasoning tokens and final `content`
  was empty.
- Two responses ended normally and produced valid JSON.
- The provider reported reasoning-token counts in `usage.completion_tokens_details`, but did
  not expose raw `reasoning_content` through this gateway.

The frozen replacement protocol uses `max_tokens=8192` and a new experiment fingerprint.
All eight started calls are carried into the conservative 100-attempt accounting for the
current five-hour window.
