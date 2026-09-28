# Discarded 8192-token preflight

This directory preserves the second DeepSeek-V4-Pro preflight attempt and is
excluded from the formal Judge experiment.

- The non-stream transport was unreliable for long thinking responses.
- SSE fixed the idle-connection failures, but 5 of 11 observed logical
  responses ended with `finish_reason=length`; those responses consumed all
  8192 completion tokens as reasoning and produced no parseable final JSON.
- A short scheduler overlap occurred while migrating from PID-file locking to
  kernel `flock` locking. Atomic records remained readable, but exact attempt
  attribution in the overlap window cannot be reconstructed.

No record in this directory is reused by the v2/16384 experiment.
