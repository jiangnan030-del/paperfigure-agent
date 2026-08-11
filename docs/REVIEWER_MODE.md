# Reviewer Mode

`paperfig review <bundle>` performs a deterministic, read-only review of a
finished run bundle. It does not re-render, repair, call a model, or validate
the scientific claim.

```bash
paperfig review runs/demo
paperfig review runs/demo --fail-on warning
```

It writes `figure.review.json` and `figure.review.md` into the bundle.

## Exit thresholds

| `--fail-on` | Non-zero exit when |
| --- | --- |
| `error` (default) | an error exists |
| `warning` | a warning or error exists |
| `never` | never |

## Bundle integrity

Reviewer Mode requires the replay spec, snapshotted data, replay script, audit,
provenance, alt text, environment lock, run log, artifact manifest, and every
requested export. Every manifest entry is re-hashed with SHA-256.

Errors include missing required artifacts, missing or empty manifests, missing
tracked files, and digest mismatches. Malformed entries, size mismatches, and
untracked files are warnings. Review reports themselves are intentionally
ignored because they are produced after the render manifest is frozen.

## Categorical colours

Categorical palettes are converted from sRGB to CIE L*a*b* against D65.
Deuteranopia, protanopia, and tritanopia are approximated in linear RGB, and
each pair is scored by the worst simulated deltaE76.

| Rule | Threshold |
| --- | --- |
| `CVD_COLOR_COLLISION` | worst simulated deltaE76 below 5 |
| `CVD_COLOR_MARGINAL` | worst simulated deltaE76 from 5 to below 12 |
| `GRAYSCALE_LUMINANCE_COLLISION` | luminance gap below 0.10 when required |
| `LOW_CONTRAST_AGAINST_BACKGROUND` | WCAG non-text contrast below 3:1 |
| `LOW_CHROMA_SERIES_COLOR` | CIE chroma below 8 in a multi-colour figure |

A collision is an error when `qa.color_vision_gate` is enabled. Warnings advise
shape, marker, dash, pattern, or direct-label redundancy.

## Continuous colormaps

Heatmaps use `viridis` in the current renderer. The public review path samples
17 points and checks normal vision plus deuteranopia, protanopia, and
tritanopia simulation.

| Rule | Trigger |
| --- | --- |
| `COLORMAP_NOT_REVIEWABLE` | map cannot be sampled |
| `COLORMAP_LIGHTNESS_REVERSAL` | signed lightness step below -0.5 L* |
| `COLORMAP_CVD_LIGHTNESS_REVERSAL` | the same after CVD simulation |
| `COLORMAP_NONUNIFORM_STEPS` | adjacent deltaE76 coefficient of variation above 0.30 |
| `COLORMAP_CVD_FLAT_SPOT` | simulated adjacent deltaE76 below 1.5 |
| `COLORMAP_ENDPOINT_COLLISION` | worst endpoint deltaE76 below 20 |

Lightness reversal and endpoint collision are errors when the CVD gate is
enabled. The old `SEQUENTIAL_COLORMAP_NOT_REVIEWED` placeholder is removed.

## Typography, dimensions, alt text, and encoding

- SVG text remains text (`svg.fonttype="none"`) so declared font sizes can be
  checked against a verified venue range.
- Figure width is checked only when the venue profile records `max_width_mm`.
- Required alt text must exist; text shorter than 80 characters is a warning.
- Multi-series line and scatter figures warn when colour is the only series
  encoding.

A missing verified venue constraint degrades to an info finding rather than an
invented rule.

## Reports

The JSON report contains schema version, status, tool version, counts, findings,
limitations, and `human_review_required: true`. Every finding contains a stable
rule ID, severity, message, evidence, and remediation.

The Markdown report presents the same information for human review. Reports
are advisory evidence and never count as approval for `paperfig package`.

## Method references

- IEC 61966-2-1: sRGB transfer function and primaries.
- CIE 15:2004: CIE L*a*b* and D65.
- Vienot, Brettel, and Mollon (1999): linear-RGB dichromat approximations.
- WCAG 2.1 sections 1.4.3 and 1.4.11: contrast ratios.

The simulation is an approximation. It does not model anomalous trichromacy,
individual adaptation, display calibration, print production, or viewing
conditions.

## Limitations

- deterministic rules are not peer review;
- panel composition and statistical interpretation remain outside Reviewer Mode;
- passing checks does not validate the claim, data provenance, or rights status;
- final scientific and publication decisions require a human.
