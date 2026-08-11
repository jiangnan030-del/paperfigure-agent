# PaperFigure Agent

A clean-room, spec-driven toolkit for reproducible, auditable, publication-ready scientific figures.

> **Status:** early MVP scaffold (v0.1.0). The repository starts with deterministic data-chart rendering and rule-based review. It does **not** yet execute model-generated code or claim autonomous scientific judgment.

## Why this repository exists

Scientific figure tooling often optimizes appearance before data fidelity, provenance, and reviewability. PaperFigure Agent reverses that order:

```text
claim + data + venue profile
        -> FigureSpec
        -> deterministic renderer
        -> rule-based audit
        -> SVG/PDF/PNG + provenance
```

The long-term architecture follows `Prompt -> Context -> Harness -> Loop -> Graph -> Evolver`, but the MVP intentionally starts with the auditable core.

## Clean-room and attribution notice

This is an independent implementation. No source code, images, datasets, or documentation text from [`ChenLiu-1996/figures4papers`](https://github.com/ChenLiu-1996/figures4papers) has been copied into this repository. At project initialization, no explicit upstream license was identified, so that repository is treated as **conceptual prior art only** until written permission or a compatible license is verified.

See:

- [`docs/CLEAN_ROOM.md`](docs/CLEAN_ROOM.md)
- [`docs/ACADEMIC_INTEGRITY.md`](docs/ACADEMIC_INTEGRITY.md)
- [`docs/REFERENCES.md`](docs/REFERENCES.md)
- [`docs/VENUE_PROFILES.md`](docs/VENUE_PROFILES.md)
- [`docs/SCIENTIFIC_SEMANTICS.md`](docs/SCIENTIFIC_SEMANTICS.md)
- [`THIRD_PARTY.yml`](THIRD_PARTY.yml)

## Implemented core

- typed `FigureSpec` loader and validation;
- local CSV data loading (remote inputs are rejected);
- deterministic Matplotlib renderers for bar, line, scatter, heatmap, box, violin, and interval charts;
- source-cited 2026 starter profiles for Nature Machine Intelligence, ICML, NeurIPS, and ECCV;
- SVG, PDF, and PNG export;
- rule-based audit with severity, evidence, and an error-level render gate;
- data-fidelity validation for duplicate coordinates, non-finite values, negative errors, and invalid intervals;
- self-contained replay bundle with a snapshotted CSV input;
- SHA-256 input provenance and a run-wide artifact manifest;
- direct dependency versions and platform details in `environment.lock`;
- CLI commands: `init`, `validate`, `render`, and `audit`;
- tests and GitHub Actions CI;
- contribution gates for citation, provenance, licensing, and clean-room review.

## Supported marks

| Mark | Primary use | Required extra fields |
| --- | --- | --- |
| `bar` | grouped comparisons | optional `series`, `error` |
| `line` | trends and trajectories | optional `series`, `error` |
| `scatter` | relationships and trade-offs | optional `series`, `size` |
| `heatmap` | matrix comparison | `value` |
| `box` / `violin` | raw-observation distributions | none |
| `interval` | forest and uncertainty plots | `lower`, `upper` |

All bundled datasets are synthetic and explicitly labeled as non-evidence.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

paperfig validate examples/specs/grouped_bar.yaml
paperfig render examples/specs/grouped_bar.yaml --output runs/demo
paperfig audit examples/specs/grouped_bar.yaml --artifacts runs/demo
```

`paperfig render` preserves the complete run and exits non-zero when the generated audit contains an error. The emitted replay bundle uses its local `figure.data.csv`, so it does not depend on the original dataset path.

Generated files:

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

## FigureSpec example

```yaml
claim: "The proposed method improves accuracy across both datasets."
venue: nature-machine-intelligence
stage: draft
backend: matplotlib

data:
  source: ../datasets/grouped_bar.csv
  license: CC0-1.0
  citation: "Synthetic demonstration data created for this repository."

chart:
  family: comparison
  mark: bar
  x: model
  y: accuracy
  series: dataset
  error: std
  highlight: Ours

qa:
  require_zero_baseline: true
  color_vision_gate: true
  require_alt_text: true

export:
  formats: [svg, pdf, png]
  dpi: 300
```

## Non-goals for the MVP

- copying the visual identity of a specific published figure;
- redistributing third-party figures or datasets;
- executing arbitrary generated Python;
- silently choosing statistical transformations;
- claiming that automated checks replace author or reviewer judgment.

## License

Original code in this repository is released under the MIT License. Third-party material, links, datasets, and generated research outputs remain subject to their own terms. The license does not retroactively authorize reuse of any upstream repository.
