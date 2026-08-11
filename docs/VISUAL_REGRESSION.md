# Visual regression

`paperfig regress <spec>` renders a FigureSpec and compares a **structural
fingerprint** of the exported SVG against a recorded baseline.

```bash
paperfig regress examples/specs/grouped_bar.yaml --update   # record
paperfig regress examples/specs/grouped_bar.yaml            # check
paperfig regress examples/specs/grouped_bar.yaml --fail-on warning
```

Baselines live in `tests/baselines/<spec-name>.baseline.json` by default.
Override with `--baselines <dir>`.

## Why not hash the file, and why not diff pixels

**Hashing the exported file does not work.** Matplotlib writes a creation
timestamp into SVG metadata, so rendering the same spec twice produces two
different files with two different SHA-256 digests. The artifact manifest that
`paperfig review` verifies is therefore a *within-run* integrity check: it
proves a bundle has not been edited since it was rendered, but it cannot
compare two separate renders.

**Pixel diffing is valid only inside one exact rendering stack.** Antialiasing
and font rasterization differ between FreeType versions and platforms, so a
pixel baseline recorded on macOS will not match one produced on CI. The usual
workaround is a loose tolerance, which is also loose enough to hide real
regressions.

**A structural fingerprint avoids both problems.** It ignores metadata and
rasterization entirely, and it records the properties that actually define the
figure. Because it is JSON, a rendering change appears in a pull request as a
readable diff:

```diff
-    "Accuracy",
+    "Precision",
```

That is far more actionable than "RMS 0.004 exceeds tolerance 0.001".

## What the fingerprint records

| Field | Meaning |
| --- | --- |
| `canvas_width_pt`, `canvas_height_pt` | SVG root dimensions, normalized to points |
| `element_counts` | count of each SVG tag, namespace stripped |
| `text_content` | every `<text>` string, in drawing order |
| `colors` | every `#rrggbb` literal, lowercased and sorted |
| `font_sizes_pt` | every declared font size, deduplicated and sorted |
| `geometry_digest` | SHA-256 of all path coordinates, quantised to 1.0 pt |
| `geometry_points` | how many coordinates went into that digest |
| `environment` | Matplotlib version, Python version, platform |

Only SVG is fingerprinted. The renderer sets `svg.fonttype="none"`, so label
text stays as text rather than being converted to outlines, which is what makes
`text_content` reliable.

## Rules

### Always errors

These properties come from the FigureSpec and the venue profile, not from the
layout engine. They do not drift between Matplotlib versions, so any change
means the figure itself changed.

| Rule | Meaning |
| --- | --- |
| `FIGURE_TEXT_CHANGED` | Labels were added, removed, or reordered. |
| `FIGURE_COLORS_CHANGED` | The set of colours drawn changed. |
| `FIGURE_FONT_SIZES_CHANGED` | Declared label sizes changed. |
| `BASELINE_MISSING` | No baseline has been recorded for this spec. |

### Warnings that downgrade across environments

These depend on the layout engine and on font metrics.

| Rule | Threshold |
| --- | --- |
| `FIGURE_ELEMENT_COUNT_CHANGED` | any change in per-tag element counts |
| `FIGURE_CANVAS_RESIZED` | more than 1% relative change in width or height |
| `FIGURE_GEOMETRY_CHANGED` | any change in the quantised coordinate digest |

When the baseline was recorded against a **different Matplotlib version**,
these three drop from `warning` to `info` and `BASELINE_ENVIRONMENT_DRIFT` is
reported instead. A dependency bump therefore produces one clear, actionable
notice rather than a wall of failures, while the always-error rules keep
working across versions.

`BASELINE_SCHEMA_UNKNOWN` is a warning when the baseline was written by a
different fingerprint schema.

## Exit behaviour

| `--fail-on` | Exits non-zero when |
| --- | --- |
| `error` (default) | any finding has severity `error` |
| `warning` | any finding has severity `warning` or `error` |
| `never` | never |

CI uses `--fail-on warning`, because unexplained layout drift is exactly what
this check exists to surface.

## Recording the first baselines

Baselines must be recorded in the environment that will check them. CI records
fingerprints for every example on each run and uploads them in the
`smoke-renders` artifact under `baselines/`. To adopt them:

1. Download the `smoke-renders` artifact from a green CI run on `main`.
2. Copy `baselines/*.baseline.json` into `tests/baselines/`.
3. Commit them.

From that point on, CI enforces every committed baseline. Until then, CI only
records them, so the check cannot fail spuriously before a baseline exists.

## Interaction with dependency pinning

This check is only as sharp as the environment is stable. `pyproject.toml`
currently requires `matplotlib>=3.8` with no upper bound, so a resolver change
can silently move the rendering stack. The environment-drift downgrade keeps
that from breaking the build, but the honest fix is a tighter pin or a lock
file for the CI environment. That is deliberately left as a separate decision.

## Limitations

- Only SVG is compared. PDF and PNG are checked for presence and integrity by
  `paperfig review`, not for content.
- The geometry digest detects *that* geometry moved, not *where*. It is a
  tripwire, not a diff.
- Coordinates are compared in absolute points, so a change in canvas size also
  changes the geometry digest. Expect both findings together.
- Text is compared as exact strings. A change in numeric tick formatting reads
  as a text change, which is intended but can be surprising.
- A matching fingerprint does not mean the figure is correct. It means the
  figure has not changed.
