# SPDX-License-Identifier: MIT
from __future__ import annotations

import tempfile
from pathlib import Path

from paperfig.harness import render_spec
from paperfig.regression.baseline import (
    DEFAULT_BASELINE_DIR,
    baseline_path,
    load_baseline,
    write_baseline,
)
from paperfig.regression.fingerprint import (
    GEOMETRY_QUANTUM_PT,
    FigureFingerprint,
    fingerprint_from_bundle,
)
from paperfig.review.models import ReviewFinding, Severity

#: Relative canvas drift tolerated before reporting a resize.
CANVAS_TOLERANCE = 0.01

_PREVIEW_LIMIT = 5


def _summarize(values: list[str], limit: int = _PREVIEW_LIMIT) -> str:
    if not values:
        return "none"
    shown = ", ".join(repr(item) for item in values[:limit])
    if len(values) > limit:
        shown = f"{shown}, ... (+{len(values) - limit} more)"
    return shown


def _drift_severity(same_environment: bool) -> Severity:
    """Layout-sensitive differences are advisory across rendering stacks.

    Element counts, canvas size, and path geometry all depend on Matplotlib's
    layout engine and on font metrics. Reporting them as warnings inside one
    environment catches real regressions; downgrading them across environments
    stops a dependency bump from failing a build for no substantive reason.
    """
    return "warning" if same_environment else "info"


def compare_fingerprints(
    baseline: FigureFingerprint, current: FigureFingerprint
) -> list[ReviewFinding]:
    """Compare a recorded baseline against a freshly rendered fingerprint."""
    findings: list[ReviewFinding] = []
    baseline_mpl = baseline.environment.get("matplotlib", "unknown")
    current_mpl = current.environment.get("matplotlib", "unknown")
    same_environment = baseline_mpl == current_mpl
    drift = _drift_severity(same_environment)

    if baseline.schema_version != current.schema_version:
        findings.append(
            ReviewFinding(
                rule_id="BASELINE_SCHEMA_UNKNOWN",
                severity="warning",
                message="The recorded baseline uses a different fingerprint schema.",
                evidence=f"baseline={baseline.schema_version}; current={current.schema_version}",
                remediation="Re-record the baseline with paperfig regress --update.",
            )
        )

    if not same_environment:
        findings.append(
            ReviewFinding(
                rule_id="BASELINE_ENVIRONMENT_DRIFT",
                severity="warning",
                message=(
                    "The baseline was recorded with a different Matplotlib version, so "
                    "layout and geometry differences are reported as notes only."
                ),
                evidence=f"baseline matplotlib={baseline_mpl}; current={current_mpl}",
                remediation="Re-record the baseline in this environment.",
            )
        )

    if baseline.text_content != current.text_content:
        removed = [item for item in baseline.text_content if item not in current.text_content]
        added = [item for item in current.text_content if item not in baseline.text_content]
        if removed or added:
            message = "The text drawn in the figure changed."
            evidence = f"removed: {_summarize(removed)}; added: {_summarize(added)}"
        else:
            message = "The figure draws the same labels in a different order."
            evidence = f"{len(current.text_content)} labels reordered"
        findings.append(
            ReviewFinding(
                rule_id="FIGURE_TEXT_CHANGED",
                severity="error",
                message=message,
                evidence=evidence,
                remediation="Confirm the change is intended, then re-record with --update.",
            )
        )

    if baseline.colors != current.colors:
        gone = sorted(set(baseline.colors) - set(current.colors))
        gained = sorted(set(current.colors) - set(baseline.colors))
        findings.append(
            ReviewFinding(
                rule_id="FIGURE_COLORS_CHANGED",
                severity="error",
                message="The set of colours drawn in the figure changed.",
                evidence=f"removed: {_summarize(gone)}; added: {_summarize(gained)}",
                remediation="Check the venue palette, then re-record with --update.",
            )
        )

    if baseline.font_sizes_pt != current.font_sizes_pt:
        findings.append(
            ReviewFinding(
                rule_id="FIGURE_FONT_SIZES_CHANGED",
                severity="error",
                message="The label font sizes drawn in the figure changed.",
                evidence=f"baseline={baseline.font_sizes_pt}; current={current.font_sizes_pt}",
                remediation="Check the venue base font size, then re-record with --update.",
            )
        )

    if baseline.element_counts != current.element_counts:
        tags = sorted(set(baseline.element_counts) | set(current.element_counts))
        changes = [
            f"{tag} {baseline.element_counts.get(tag, 0)}->{current.element_counts.get(tag, 0)}"
            for tag in tags
            if baseline.element_counts.get(tag, 0) != current.element_counts.get(tag, 0)
        ]
        findings.append(
            ReviewFinding(
                rule_id="FIGURE_ELEMENT_COUNT_CHANGED",
                severity=drift,
                message="The figure is built from a different number of SVG elements.",
                evidence="; ".join(changes),
                remediation="Inspect the rendering, then re-record with --update.",
            )
        )

    for axis, before, after in (
        ("width", baseline.canvas_width_pt, current.canvas_width_pt),
        ("height", baseline.canvas_height_pt, current.canvas_height_pt),
    ):
        if before <= 0.0:
            continue
        relative = abs(after - before) / before
        if relative <= CANVAS_TOLERANCE:
            continue
        findings.append(
            ReviewFinding(
                rule_id="FIGURE_CANVAS_RESIZED",
                severity=drift,
                message=f"The exported canvas {axis} moved outside the baseline tolerance.",
                evidence=f"{before:.2f}pt -> {after:.2f}pt ({relative * 100:.1f}%)",
                remediation="Check the layout settings, then re-record with --update.",
            )
        )

    if baseline.geometry_digest != current.geometry_digest:
        findings.append(
            ReviewFinding(
                rule_id="FIGURE_GEOMETRY_CHANGED",
                severity=drift,
                message="The plotted geometry changed beyond the quantisation tolerance.",
                evidence=(
                    f"quantised at {GEOMETRY_QUANTUM_PT:g}pt; "
                    f"coordinates {baseline.geometry_points} -> {current.geometry_points}"
                ),
                remediation="Confirm the data and plot code, then re-record with --update.",
            )
        )

    return findings


def _render_fingerprint(spec_path: Path) -> FigureFingerprint:
    with tempfile.TemporaryDirectory() as directory:
        render_spec(spec_path, Path(directory))
        return fingerprint_from_bundle(directory, spec_path.stem)


def record_baseline(
    spec_path: str | Path, baselines_dir: str | Path = DEFAULT_BASELINE_DIR
) -> Path:
    """Render a FigureSpec and store its fingerprint as the new baseline."""
    return write_baseline(baselines_dir, _render_fingerprint(Path(spec_path)))


def regress_spec(
    spec_path: str | Path, baselines_dir: str | Path = DEFAULT_BASELINE_DIR
) -> tuple[FigureFingerprint, list[ReviewFinding]]:
    """Render a FigureSpec and compare it against its recorded baseline."""
    path = Path(spec_path)
    current = _render_fingerprint(path)
    baseline = load_baseline(baselines_dir, path.stem)
    if baseline is None:
        return current, [
            ReviewFinding(
                rule_id="BASELINE_MISSING",
                severity="error",
                message="No baseline has been recorded for this FigureSpec.",
                evidence=str(baseline_path(baselines_dir, path.stem)),
                remediation="Record the current rendering with paperfig regress --update.",
            )
        ]
    return current, compare_fingerprints(baseline, current)
