# Changelog

## Unreleased

### Phase 2 — complete deterministic workflow

#### Added

- continuous-colormap perceptual review for heatmaps under normal and simulated dichromat vision;
- `paperfig compare <baseline> <candidate>` for data, spec, environment, SVG, and Reviewer Mode deltas;
- JSON and Markdown comparison reports;
- `paperfig package <bundle> --approve` with an explicit human gate;
- deterministic submission ZIPs, package-level artifact manifests, and companion SHA-256 files;
- end-to-end tests for colormap thresholds, A/B comparison, tamper rejection, and reproducible packages;
- `docs/PHASE2_COMPLETE.md` describing the complete verification and delivery contract.

#### Changed

- CI now smoke-tests render, audit, replay, review, compare, package, and regression for every supported mark;
- all seven CI-recorded visual baselines are enforced with `--fail-on warning`;
- Reviewer Mode no longer emits the `SEQUENTIAL_COLORMAP_NOT_REVIEWED` placeholder for heatmaps;
- Reviewer Mode limitations now distinguish implemented colormap checks from remaining human judgments.

### Phase 2 — visual regression

#### Added

- `paperfig regress <spec>`, which compares a rendering against a recorded baseline;
- structural SVG fingerprints covering text, colours, font sizes, element counts, canvas size, and quantised path geometry;
- reviewable JSON baselines in `tests/baselines/`, so a rendering change appears as a readable diff;
- environment-aware severity for layout-sensitive findings;
- `--update` and `--fail-on {error,warning,never}`;
- `docs/VISUAL_REGRESSION.md`.

### Phase 2 — reviewer mode

#### Added

- `paperfig review <bundle>`, a deterministic reviewer pass over a run bundle;
- run-bundle integrity verification against the SHA-256 artifact manifest;
- dichromat separation checks for deuteranopia, protanopia, and tritanopia;
- WCAG contrast, near-neutral colour, greyscale luminance, typography, and size checks;
- `figure.review.json` and `figure.review.md` reports;
- `docs/REVIEWER_MODE.md`.

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

- generated `figure.py` contains real newlines and is compile-tested;
- replay scripts no longer depend on the original dataset path;
- render commands preserve artifacts before failing an audit gate;
- CI audits and replays every supported example;
- zero-baseline enforcement is limited to bar charts;
- venue-profile sources remain embedded in provenance.
