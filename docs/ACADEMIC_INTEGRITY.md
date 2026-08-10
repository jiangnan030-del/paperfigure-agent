# Academic integrity and responsible figure policy

## Core rule

A scientifically attractive figure is unacceptable if its data, transformation, attribution, or provenance cannot be audited.

## Required records for every research figure

- source dataset and checksum;
- inclusion/exclusion and transformation steps;
- statistical definitions, including error bars and sample size;
- FigureSpec and software/environment versions;
- human approvals for semantic or statistical choices;
- references that materially influenced the design;
- disclosure of AI assistance when required by the target venue or institution.

## Citation versus copying

Citation acknowledges intellectual influence; it does not grant copyright permission. A URL or BibTeX entry cannot legalize copying code, prose, data, or pixels. Conversely, independently implemented general ideas should still cite materially relevant prior art.

## Published figures and target venues

Nature Machine Intelligence, ICML, NeurIPS, and ECCV are publication venues or contexts, not blanket licenses. Before using any figure from a paper:

1. identify the exact paper, authors, DOI/URL, and figure number;
2. inspect the article and figure license, not only the venue name;
3. document whether the figure is quoted, adapted, benchmarked, or only studied conceptually;
4. obtain permission when the intended reuse is not covered;
5. label adaptations explicitly and never imply original authorship.

## Automated review boundaries

Reviewer Mode may flag possible truncation, normalization, accessibility, or provenance issues. It must not claim misconduct, fabricate evidence, or replace domain review. High-risk changes—data filtering, baseline truncation, error definitions, statistical tests, or caption claims—require human approval.

## Reference-image policy

Reference retrieval must filter by license and store the source URL and intended use. The default mode extracts abstract design constraints (for example, panel hierarchy or annotation density), not protected pixels or a near-duplicate composition.

## Release gate

A release is blocked if it contains:

- an asset with unknown rights;
- copied material missing attribution;
- a scientific transform without a recorded rationale;
- a generated claim not supported by the plotted data;
- secrets, personal research data, or restricted submissions.
