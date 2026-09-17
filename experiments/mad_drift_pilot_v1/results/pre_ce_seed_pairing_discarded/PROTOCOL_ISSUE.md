# Isolated seed-pairing preflight

The initial MAD preflight and interrupted formal launch derived request seeds
with the condition name included. Consequently, corresponding C_clean and
E_noise requests had different seeds. The requests and responses were valid,
but this weakens the intended paired interpretation because the comparison
would vary both non-target information and the requested sampling seed.

The issue was found during plan auditing, before result analysis and without
reference to accuracy. All generated records were isolated here and excluded
from formal statistics. The frozen formal plan uses the same derived seed for
corresponding C_clean and E_noise requests while retaining distinct agent,
item, stage, revision-round, and team-root components. MAD and self branches
also retain paired seeds. No response from this directory is reused.
