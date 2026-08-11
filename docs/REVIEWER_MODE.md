# Reviewer Mode

`paperfig review <bundle>` performs a deterministic, rule-based pass over a
rendered run bundle. It never re-renders, never edits artifacts, and never
calls a model. It answers two questions:

1. **Is this bundle still the bundle that was rendered?**
2. **Would a reader with limited colour vision, or a greyscale printer, be able
   to read this figure?**

```bash
paperfig render examples/specs/grouped_bar.yaml --output runs/demo
paperfig review runs/demo
paperfig review runs/demo --fail-on warning
```

The command writes `figure.review.json` and `figure.review.md` into the bundle.
Both files are deliberately excluded from the render-time artifact manifest, so
reviewing a bundle never invalidates its own integrity check.

## Exit behaviour

| `--fail-on` | Exits non-zero when |
| --- | --- |
| `error` (default) | any finding has severity `error` |
| `warning` | any finding has severity `warning` or `error` |
| `never` | never; the report is still written |

CI uses the default, so integrity regressions break the build while
accessibility observations stay visible without blocking work in progress.

## Rules

### Bundle integrity

| Rule | Severity | Meaning |
| --- | --- | --- |
| `BUNDLE_ARTIFACT_MISSING` | error | A required run artifact or declared export format is absent. |
| `MANIFEST_MISSING` | error | The bundle has no `artifact.manifest.json`. |
| `MANIFEST_EMPTY` | error | The manifest records no artifacts. |
| `MANIFEST_ENTRY_MISSING` | error | A manifest-tracked file is gone. |
| `MANIFEST_DIGEST_MISMATCH` | error | A file no longer matches its render-time SHA-256. |
| `MANIFEST_SIZE_MISMATCH` | warning | A file no longer matches its recorded size. |
| `MANIFEST_SCHEMA_UNKNOWN` | warning | The manifest schema version is unrecognized. |
| `MANIFEST_ENTRY_MALFORMED` | warning | A manifest entry has no usable path. |
| `MANIFEST_UNTRACKED_FILE` | warning | The bundle contains a file the manifest does not track. |

### Colour and accessibility

| Rule | Severity | Threshold |
| --- | --- | --- |
| `CVD_COLOR_COLLISION` | error when `qa.color_vision_gate` is true, else warning | worst-case simulated delta-E76 < 5.0 |
| `CVD_COLOR_MARGINAL` | warning | worst-case simulated delta-E76 < 12.0 |
| `LOW_CONTRAST_AGAINST_BACKGROUND` | warning | WCAG non-text contrast against white < 3.0:1 |
| `LOW_CHROMA_SERIES_COLOR` | warning | CIE chroma < 8.0 while more than one series is drawn |
| `GRAYSCALE_LUMINANCE_COLLISION` | warning | relative luminance gap < 0.10, only for venues that require greyscale legibility |
| `REDUNDANT_ENCODING_MISSING` | warning | multi-series `line` or `scatter` marks separated by colour alone |
| `SEQUENTIAL_COLORMAP_NOT_REVIEWED` | info | heatmaps are skipped by the categorical rules |
| `PALETTE_NOT_REVIEWABLE` | info | the venue profile has no usable palette |

### Typography, size, and alt text

| Rule | Severity | Meaning |
| --- | --- | --- |
| `FONT_SIZE_BELOW_VENUE_MINIMUM` | warning | SVG label text is smaller than `constraints.label_font_size_pt[0]`. |
| `FIGURE_WIDTH_EXCEEDS_VENUE` | warning | The exported SVG is wider than `constraints.max_width_mm`. |
| `ALT_TEXT_MISSING` | error | `qa.require_alt_text` is set but no alt text exists. |
| `ALT_TEXT_TOO_SHORT` | warning | Alt text is shorter than 80 characters. |
| `TYPOGRAPHY_NOT_VERIFIABLE` | info | No SVG, or no readable font sizes in it. |
| `VENUE_FONT_RANGE_UNSPECIFIED` | info | The venue profile states no label size range. |
| `FIGURE_WIDTH_NOT_VERIFIABLE` | info | The SVG root declares no readable width. |

## Colour method

All colour math lives in `src/paperfig/review/color.py` and is an independent
implementation of published methods:

- sRGB transfer function and primaries: IEC 61966-2-1.
- CIE L\*a\*b\* conversion against the D65 white point: CIE 15:2004.
- Dichromat simulation matrices applied in **linear** RGB: Vienot, Brettel and
  Mollon (1999), *Digital video colourmaps for checking the legibility of
  displays by dichromats*, Color Research & Application 24(4), 243-252.
- Relative luminance and contrast ratio: WCAG 2.1, sections 1.4.3 and 1.4.11.

The reviewed colour set is derived from the venue profile palette and the
number of distinct series in the bundled data, plus the highlight colour when
the FigureSpec sets `chart.highlight`. Deriving colours from the spec rather
than scraping the SVG keeps the result stable across Matplotlib versions.

Separation is reported as delta-E76 under the worst of deuteranopia,
protanopia, and tritanopia. A delta-E76 near 5 is roughly the point where two
colours stop being reliably distinguishable at small sizes; 12 is the point
where separation stops being comfortable in print.

## Limitations

- The simulation models dichromacy only. Anomalous trichromacy, individual
  adaptation, and display calibration are out of scope.
- Continuous colormaps are not evaluated. Heatmaps receive an informational
  finding instead.
- Only SVG is measured for typography and width. PDF and PNG are checked for
  presence and integrity only.
- Contrast is measured against a white background because the renderer does not
  emit figure backgrounds.
- Panel composition, statistical validity, and caption quality are not
  reviewed. Reviewer Mode supports human review; it does not replace it.
