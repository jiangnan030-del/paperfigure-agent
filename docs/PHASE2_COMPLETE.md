# Phase 2: deterministic review, comparison, and delivery

Phase 2 completes the deterministic path from a rendered run to a human-approved
submission archive:

```text
FigureSpec
  -> render
  -> audit
  -> review (categorical colour + continuous colormap + typography + integrity)
  -> regress (committed structural baseline)
  -> compare (baseline bundle vs candidate bundle)
  -> package (human gate + deterministic ZIP + two integrity manifests)
```

None of these stages calls a model or silently edits scientific content.

## Continuous-colormap review

Heatmaps currently render with Matplotlib `viridis`. Reviewer Mode samples the
map at 17 evenly spaced points and evaluates CIE L*a*b* behaviour under normal
vision and deuteranopia, protanopia, and tritanopia simulation.

| Rule | Default severity | Trigger |
| --- | --- | --- |
| `COLORMAP_NOT_REVIEWABLE` | error | configured map cannot be sampled |
| `COLORMAP_LIGHTNESS_REVERSAL` | error with CVD gate | sequential lightness reverses by more than 0.5 L* |
| `COLORMAP_CVD_LIGHTNESS_REVERSAL` | error with CVD gate | ordering reverses after dichromat simulation |
| `COLORMAP_NONUNIFORM_STEPS` | warning | adjacent deltaE76 coefficient of variation exceeds 0.30 |
| `COLORMAP_CVD_FLAT_SPOT` | warning | simulated adjacent deltaE76 falls below 1.5 |
| `COLORMAP_ENDPOINT_COLLISION` | error with CVD gate | worst endpoint deltaE76 falls below 20 |

The former `SEQUENTIAL_COLORMAP_NOT_REVIEWED` placeholder is removed from the
public review path. The thresholds are deterministic tripwires, not a claim
that one colormap is optimal for every task or display.

## `paperfig compare`

Compare two finished run bundles before choosing a candidate:

```bash
paperfig compare runs/baseline runs/candidate --output runs/comparison
paperfig compare runs/baseline runs/candidate --fail-on warning
```

The command compares five independent layers:

1. input-data SHA-256;
2. semantic and presentation fields in the bundled FigureSpec;
3. `environment.lock`;
4. structural SVG fingerprints (text, colours, fonts, elements, canvas, geometry);
5. Reviewer Mode severities before and after.

It writes `figure.comparison.json` and `figure.comparison.md` when `--output` is
provided. Scientific/data-encoding changes and data changes are errors. A new
candidate warning remains a warning; an improvement is recorded as an info
finding. A passing result means no tracked regression was found, not that the
candidate's scientific claim is correct.

## `paperfig package`

Build a submission archive only after deterministic gates and an explicit human
approval:

```bash
paperfig package runs/candidate \
  --output dist/figure.submission.zip \
  --approve
```

Without `--approve`, the command refuses to package. This is an intentional
human gate for scientific interpretation, third-party rights, and formal
release.

Packaging performs the following checks and actions:

- requires `figure.audit.json` to record `status: passed`;
- reruns Reviewer Mode and applies `--fail-on error|warning|never`;
- rejects missing files, manifest mismatches, altered artifacts, and symlinks;
- includes the spec, snapshotted data, replay code, SVG/PDF/PNG, alt text,
  provenance, audit, environment, run log, and deterministic review reports;
- writes `submission.manifest.json` with the size and SHA-256 of every payload;
- writes a deterministic ZIP (sorted paths, fixed timestamps and permissions);
- emits a companion `<archive>.sha256` checksum.

The original render manifest proves integrity inside the source run. The
submission manifest proves integrity inside the delivery package. The companion
checksum identifies the ZIP as a whole.

## Visual-regression baselines

Seven reviewable JSON baselines were recorded on GitHub Actions and merged via
PR #5 before this completion branch was created. They cover every example spec
under matplotlib 3.11.1 and Python 3.12.13. CI renders each example again and
runs `paperfig regress --fail-on warning` against its committed baseline. The
check is therefore a real cross-run gate rather than generate-and-compare in one
job.

## What still requires human judgment

Phase 2 deliberately does not automate:

- whether a claim is scientifically valid;
- whether an error bar or statistical transformation is appropriate;
- whether a truncated axis is justified;
- whether third-party data and references may be redistributed;
- whether the final candidate should be formally submitted.

Those are governance boundaries, not missing implementation.
