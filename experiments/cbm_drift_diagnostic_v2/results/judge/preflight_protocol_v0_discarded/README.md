# Discarded Judge protocol preflight

This directory preserves one DeepSeek V4 Pro request made before the Judge protocol was frozen.

The response was valid JSON but failed quote and rule-ID validation: it paraphrased the current message, emitted zero offsets, and used bare ordinal rule numbers. The protocol was therefore revised to require verbatim substrings, zero-based slice offsets, and `C1`-style IDs. This record is retained for audit but excluded from all formal Judge statistics and predicted events.
