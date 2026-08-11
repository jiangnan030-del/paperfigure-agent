# Changelog

## Unreleased

### Phase 2 — reviewer mode

#### Added

- `paperfig review <bundle>`, a deterministic reviewer pass over a rendered run bundle;
- run-bundle integrity verification against the recorded SHA-256 artifact manifest;
- dichromat separation checks for deuteranopia, protanopia, and tritanopia in CIE L\*a\*b\*;
- WCAG non-text contrast, near-neutral colour, and greyscale luminance checks;
- venue typography and figure-width checks measured from the exported SVG;
- redundant-encoding warnings for multi-series line and scatter marks;
- `figure.review.json` and `figure.review.md` reviewer reports;
- `--fail-on {error,warning,never}` to control the review exit code;
- `docs/REVIEWER_MODE.md` documenting every rule, threshold, and limitation.

#### Changed

- CI now reviews every example after rendering, auditing, and replaying it;
- `paperfig audit` and `paperfig review` are documented as separate stages.

## Unreleased — Phase 1 executable core

### Added

- line, scatter, heatmap, box, violin, and interval renderers;
- mark-specific FigureSpec fields and validation;
- data-fidelity checks for duplicate coordinates, non-finite values, negative errors, and invalid intervals;
- synthetic examples for every supported mark;
- scientific-semantics documentation and expanded test coverage;
- self-contained replay bundles with a snapshotted CSV input and artifact manifest;
- direct dependency versions and platform details in `environment.lock`.

### Fixed

- generated `figure.py` now contains real newlines and is compile-tested;
- replay scripts no longer depend on the original dataset path;
- render commands now fail after preserving artifacts when an audit reports an error;
- CI now audits and replays every supported example after rendering;
- zero-baseline enforcement is limited to bar charts;
- venue-profile sources remain embedded in provenance.
