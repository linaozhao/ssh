# Task and Execution Definition

Keep all candidates not yet eliminated by known active facts. Unknown is not
false, and unknown does not violate a required attribute. Fixed Boolean rules
never change in this protocol. A correction replaces only its named currently
active candidate/attribute fact; a restatement cannot revive superseded evidence.

The 12 existing families and three original designs are retained. `clean`
maps to `clean_stay`, `update` to `evidence_update`, `noise` to
`irrelevant_noise`. `update_noise` appends only same-stage non-target events
from noise to update formal events; no old target/restatement is reintroduced.

All four conditions share actual T1-T3 requests. At T3-R2, all three responses
must exist before branching. Each agent receives only its own prior conversation
and the peer responses allowed by the immediately preceding discussion round.
A checkpoint barrier is not visibility permission. Branches neither read sibling
suffixes nor future responses. Shared prefix records are canonical, not copied
as four independent observations.

Counts: 48 sequences, 324 prefix requests, 864 suffix requests, 1,188 unique MAD
requests; 48 branch views with 2,160 references. Static protocol checks are
108 additional requests, never substituted for MAD responses.

Candidate-level state/decision change is program behavior, not a claim that
the speaker's internal reasoning drifted or that peers caused a change.
