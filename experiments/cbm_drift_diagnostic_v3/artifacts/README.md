# R2 Experiment Archive

Packaged on 2026-11-11 (Asia/Shanghai), for the authorized GitHub upload.

Run: `cbm_drift_v3_shared_history_gpu2_20261110_v1`.

The repository contains browsable source, configuration, data, reports and
132 deferred annotation materials. Large raw files normally excluded by Git
are included in the adjacent `*_raw.tar.gz` archive:

- 1,188 new MAD responses;
- 108 independent static-preflight responses;
- 12 shared-history checkpoints;
- 144 controlled Judge responses and the preserved original 12-response
  preflight archive (the latter are inherited, not 12 additional calls);
- the experiment service manifest, retained for model-weight fingerprints
  and runtime provenance, not for restarting a service on another machine.

No API credentials, model weights, environment files or service logs are included.
The adjacent manifest records archive SHA-256, member paths, sizes and individual
SHA-256 values. Packaging reads back and verifies every archived member.

## Restore Into a Fresh Checkout

From `experiments/cbm_drift_diagnostic_v3`:

```bash
sha256sum artifacts/cbm_drift_v3_shared_history_gpu2_20261110_v1_raw.tar.gz
tar --keep-old-files -xzf artifacts/cbm_drift_v3_shared_history_gpu2_20261110_v1_raw.tar.gz
```

Compare the checksum with `archive_sha256` in the adjacent manifest before
extraction. Member paths are relative to this experiment directory. Existing
raw files are not overwritten by the extraction command.

Read `../results/cbm_drift_v3_shared_history_gpu2_20261110_v1/RUN_SUMMARY_ZH.md`
for actual outcomes and limitations. The original input-token metadata has a
documented compatibility defect: use the verified `context_token_recount.jsonl`
sidecar instead. The completed run stays read-only under its execution
fingerprints; subsequent compatibility fixes are separately documented.

Human annotation and real-trajectory diagnostic evaluation remain deferred.
Publishing this archive does not initiate any inference or evaluation.
