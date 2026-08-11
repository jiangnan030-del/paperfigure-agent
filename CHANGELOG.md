# Changelog

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
