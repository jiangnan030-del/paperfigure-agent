# PaperFigure Agent

A clean-room, spec-driven toolkit for reproducible, auditable,
publication-ready scientific figures.

> **Status:** v0.1.0 + Unreleased. The deterministic Phase 2 workflow is
> implemented. The project does not execute model-generated code or claim
> autonomous scientific judgment.

## Pipeline

```text
claim + data + venue profile
  -> FigureSpec
  -> deterministic renderer
  -> static/scientific audit
  -> SVG/PDF/PNG + replay + provenance
  -> deterministic Reviewer Mode
  -> structural visual-regression baseline
  -> baseline/candidate comparison
  -> explicit human approval
  -> deterministic submission package
```

## Implemented core

- typed `FigureSpec` validation;
- local CSV loading with data-fidelity hard gates;
- bar, line, scatter, heatmap, box, violin, and interval renderers;
- Nature Machine Intelligence, ICML, NeurIPS, and ECCV starter profiles;
- SVG, PDF, and PNG export;
- self-contained replay bundles with snapshotted data;
- SHA-256 provenance and artifact manifests;
- categorical colour, CVD, contrast, greyscale, typography, size, and alt-text review;
- continuous-colormap review under normal and simulated dichromat vision;
- structural SVG fingerprints and reviewable JSON baselines;
- deterministic baseline/candidate bundle comparison;
- human-gated, reproducible submission ZIPs with a second integrity manifest;
- tests and a complete GitHub Actions smoke workflow.

## Commands

| Command | Purpose |
| --- | --- |
| `paperfig init` | create a synthetic starter project |
| `paperfig validate` | validate a FigureSpec |
| `paperfig render` | create a complete replayable run bundle |
| `paperfig audit` | run pre-render and artifact rules |
| `paperfig review` | inspect one finished bundle |
| `paperfig regress` | compare a render with its accepted baseline |
| `paperfig compare` | compare baseline and candidate bundles |
| `paperfig package` | build a human-approved submission archive |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

paperfig validate examples/specs/grouped_bar.yaml
paperfig render examples/specs/grouped_bar.yaml --output runs/baseline
paperfig review runs/baseline
paperfig regress examples/specs/grouped_bar.yaml --update
```

Create and compare a candidate:

```bash
paperfig render examples/specs/grouped_bar.yaml --output runs/candidate
paperfig compare runs/baseline runs/candidate --output runs/comparison
```

Package only after inspecting the figure and its reports:

```bash
paperfig package runs/candidate \
  --output dist/figure.submission.zip \
  --approve
```

`--approve` is mandatory. It records an explicit human gate; it is not inferred
from green automation.

## Verification and delivery stages

| Stage | Question |
| --- | --- |
| `audit` | Is the requested figure allowed and internally consistent? |
| `review` | Is this bundle intact, accessible, and venue-aware? |
| `regress` | Did the accepted rendering drift? |
| `compare` | Did the candidate improve without changing data or semantics? |
| `package` | Is the approved delivery complete and self-verifying? |

The commands deliberately do not overlap. The render manifest proves that one
bundle was not edited after rendering. It cannot compare two runs because
Matplotlib writes a timestamp into SVG metadata. Structural fingerprints ignore
that metadata and compare text, colours, fonts, element counts, canvas size,
and quantised geometry instead.

## Run-bundle contents

```text
runs/demo/
├── figure.spec.yaml
├── figure.data.csv
├── figure.py
├── figure.svg
├── figure.pdf
├── figure.png
├── figure.alt.txt
├── figure.audit.json
├── figure.provenance.json
├── artifact.manifest.json
├── run.log.jsonl
└── environment.lock
```

`paperfig review` adds `figure.review.json` and `figure.review.md`. These are
excluded from the render-time manifest so review cannot invalidate the bundle
it is reviewing.

`paperfig compare --output DIR` adds `figure.comparison.json` and
`figure.comparison.md` in the chosen report directory.

`paperfig package` includes the complete run, deterministic review reports, and
`submission.manifest.json` in a sorted ZIP with fixed entry metadata. It also
writes `<archive>.sha256` beside the ZIP.

## Visual-regression baselines

```bash
paperfig regress examples/specs/grouped_bar.yaml --update
paperfig regress examples/specs/grouped_bar.yaml --fail-on warning
```

Baselines are JSON under `tests/baselines/`, not binary images. They must be
recorded in the same pinned environment that enforces them. CI records all
seven example baselines and enforces every committed baseline.

## Clean-room and attribution notice

This is an independent implementation. No source code, images, datasets, or
documentation text from
[`ChenLiu-1996/figures4papers`](https://github.com/ChenLiu-1996/figures4papers)
has been copied. No explicit upstream license was identified at project
initialization, so that repository remains conceptual prior art only unless
permission or a compatible license is verified.

All bundled example datasets are synthetic and explicitly labelled as
non-evidence.

## Documentation

- [`docs/PHASE2_COMPLETE.md`](docs/PHASE2_COMPLETE.md)
- [`docs/REVIEWER_MODE.md`](docs/REVIEWER_MODE.md)
- [`docs/VISUAL_REGRESSION.md`](docs/VISUAL_REGRESSION.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/SCIENTIFIC_SEMANTICS.md`](docs/SCIENTIFIC_SEMANTICS.md)
- [`docs/VENUE_PROFILES.md`](docs/VENUE_PROFILES.md)
- [`docs/CLEAN_ROOM.md`](docs/CLEAN_ROOM.md)
- [`docs/ACADEMIC_INTEGRITY.md`](docs/ACADEMIC_INTEGRITY.md)
- [`THIRD_PARTY.yml`](THIRD_PARTY.yml)

## Human-only decisions

Automation does not decide whether a claim is valid, a statistical transform
is appropriate, an axis truncation is justified, third-party material may be
redistributed, or a figure should be formally submitted. Those remain explicit
human responsibilities.

## License

Original code in this repository is released under the MIT License. Third-party
material, links, datasets, and generated research outputs remain subject to
their own terms.
