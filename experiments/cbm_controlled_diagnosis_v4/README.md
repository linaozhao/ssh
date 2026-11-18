# Controlled Diagnosis v4

**Stopped development version. Do not resume.** B1 background ambiguity was found
before any holdout calls. See `reports/ERRATUM_STOPPED_ZH.md`; the active corrected
experiment is `../cbm_controlled_diagnosis_v4_r2/`. Historical artifacts stay intact.

CPU-only exploratory controlled diagnostics. Does not run MAD, GPU inference,
real-message annotation or real-MAD formal evaluation. Previous experiments remain
unchanged. Branch: `feature/cbm-controlled-diagnosis-v4`.

## Design

- A: 12 families x 6 variants = 72 tasks. Same wrong decision with false fact,
  altered rule, invalid inference, or absent explanation; rejection and paraphrase pairs.
- B1: 12 x 6 = 72. Missing history, new, persistent, corrected, recurrence and
  post-official-fact-update reversion. Same-agent visible history only.
- B2: 12 x 4 = 48. Three agents in synchronous R0/R1/R2, first error at each round
  or no error. No target message or object supplied to the judge.
- 6/6 existing family dev/holdout split, shared across all variants. These are new
  controlled statements on old base tasks, not unseen-base-task generalization.
- A/B2 use a declared prefix of source observations isolating one decisive known
  violation. B1 reuses real source correction operations. No original data edited.

## Methods

M0 uses complete public rules/evidence/messages. M1 adds deterministic effective
states (new adapter of the previous structured-state idea, not a byte-identical old
prompt). M2 calls an LLM to extract public claims, stance and their source spans,
then checks predicates and same-agent history in Python; at most one additional
semantic call for ambiguous extraction. No construction parser or references are
available to M2. Program-unmappable content may remain uncertain.

## Definitions and old-protocol audit

F requires an adopted assertion contradicting a known active fact. Unsupported
assertions on unknown attributes are separately uncertain, unlike the old v3
`inspect_message` fallback. R changes a formal criterion. I requires explicit correct
premises incompatible with the conclusion; wrong answers alone are unresolved.
Quoted/rejected/hypothetical stances are scoped to each assertion.

Old exact matching bound candidate, attribute AND all rule IDs before scoring,
then required exact spans and evidence. New core matching uses message, candidate,
attribute and span only. Extra rules affect evidence/strict metrics, not core.
Exact and span-IoU >= 0.5 scores are preregistered separately. Matching never uses
predicted semantic labels. All failures stay in end-to-end denominators.
Known A/B1 target locations are not counted as autonomous discovery. B2 is separate.

`active_version` and `cited_version` are distinct integer-or-null fields. Contradicting
the new value does not by itself prove an explicitly cited old version. Current
evidence IDs, cited evidence IDs and same-agent historical message support are separate.
Schema and rubric: `protocol_schema.json`; implementation: `lib/protocol.py`.

## Reference limitations

References are `program_verified`, never human gold. A separate finite-language
recognizer interprets actual sentences instead of trusting variant labels. State
solutions are cross-checked by enumerating unknown completions; visible chronology
and paired invariants are checked. Formal checking shares code with M2, and natural
text recognition shares the preexisting attribute lexicon, so independent human
review remains necessary. `review/samples.md` contains all inputs and references.

## Run

From repository root (Python 3.10+, standard library and pytest):

```bash
pytest -q -o addopts='' experiments/cbm_controlled_diagnosis_v4/tests
python experiments/cbm_controlled_diagnosis_v4/scripts/run.py prepare
python experiments/cbm_controlled_diagnosis_v4/scripts/run.py run --split dev --online --prompt-key
python experiments/cbm_controlled_diagnosis_v4/scripts/run.py analyze
# Inspect development results; explicitly freeze dev_review.json with fingerprint.
python experiments/cbm_controlled_diagnosis_v4/scripts/review_development.py --approve-unchanged-protocol
python experiments/cbm_controlled_diagnosis_v4/scripts/run.py run --split holdout --online --prompt-key
python experiments/cbm_controlled_diagnosis_v4/scripts/run.py analyze
python experiments/cbm_controlled_diagnosis_v4/scripts/audit_run.py --final
python experiments/cbm_controlled_diagnosis_v4/scripts/summarize_errors.py
```

Online is disabled without `--online`. A fresh authorized key is read without echo
or from `CBM_V4_JUDGE_KEY`, never embedded/persisted. No legacy credential lookup.
API endpoint/model/parameters are all in `config/judge.json`.
Default maximum 768 physical calls plus 24 infrastructure retries; no format/answer
retry. Reserve input-byte proxy plus output budget before each attempt, reconcile
provider usage, enforce 40M total token cap. Monetary cost remains unknown.
No automatic credential rotation, quota override or GPU fallback.

Artifacts include immutable inputs/references/queue/fingerprints, per-attempt raw
responses/usage, per-method-task outputs, layered scores, resource usage and a
Chinese report. A crashed in-flight attempt is marked unresolved, not silently
duplicated. Completed outputs are skipped only under identical fingerprints.

Development and holdout are never pooled into a test accuracy. Freeze precedes
online execution; any later protocol change requires a new experiment version.

`raw_offset_audit.jsonl` separately scores the unrepaired model-provided spans.
M2 entries in that supplemental file cover only its semantic follow-up responses;
ordinary M2 final spans come from its checked extractor. Do not compare that subset
with a complete M0/M1 denominator. Primary metrics retain all expected tasks.
