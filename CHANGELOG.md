# Changelog

## Unreleased — Phase 1 executable core

### Added

- line, scatter, heatmap, box, violin, and interval renderers;
- mark-specific FigureSpec fields and validation;
- data-fidelity checks for duplicate coordinates, non-finite values, negative errors, and invalid intervals;
- synthetic examples for every supported mark;
- scientific-semantics documentation and expanded test coverage.

### Fixed

- generated `figure.py` now contains real newlines and is compile-tested;
- zero-baseline enforcement is limited to bar charts;
- venue-profile sources remain embedded in provenance.
