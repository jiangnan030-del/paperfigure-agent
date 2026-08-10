# Clean-room development protocol

## Scope

This protocol applies because the audited `figures4papers` repository did not expose an explicit root license at project initialization. Lack of a license is not permission to copy, modify, or redistribute.

## Allowed design inputs

- published papers and public project descriptions, cited by URL/DOI;
- observable input/output behavior documented in our own tests;
- venue author guidelines and standards, with source and access date;
- independently created synthetic data;
- permissively licensed dependencies used according to their terms;
- requirements written in the project roadmap.

## Prohibited inputs until permission is verified

- upstream Python source copied or lightly rewritten;
- upstream images, screenshots, plots, icons, datasets, or fonts;
- upstream Skill/reference prose copied, translated, or paraphrased too closely;
- output tracing intended to recreate a distinctive protected composition;
- publication figures used as training or regression assets without rights review.

## Implementation process

1. Write a behavior-level requirement without copying implementation detail.
2. Record prior art and license state in `THIRD_PARTY.yml`.
3. Implement from the requirement using original names and structure where practical.
4. Use synthetic or rights-cleared fixtures.
5. Add deterministic tests and provenance output.
6. Review similarity, attribution, and third-party notices before merge.
7. If contamination is suspected, quarantine the contribution and reimplement from a clean specification.

## Migrating the eight upstream cases

The `examples/migrated/` directory is intentionally empty. Each case requires one of:

- explicit written permission;
- a newly added compatible license covering the relevant code/assets; or
- a clean-room recreation from independently described scientific requirements and newly generated data/assets.

A visual resemblance goal alone is not enough. Every migrated case needs a provenance record and a rights decision.
