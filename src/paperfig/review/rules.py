# SPDX-License-Identifier: MIT
from __future__ import annotations

import csv
import itertools
import re
from pathlib import Path
from typing import Any

from paperfig.contracts.artifacts import REQUIRED_RUN_ARTIFACTS, REVIEW_ARTIFACTS
from paperfig.provenance.record import sha256_file
from paperfig.review.bundle import BUNDLE_MANIFEST_NAME, RunBundle, load_bundle
from paperfig.review.color import (
    WHITE,
    chroma,
    contrast_ratio,
    parse_hex,
    relative_luminance,
    worst_dichromat_delta_e,
)
from paperfig.review.models import ReviewFinding

COLLISION_DELTA_E = 5.0
MARGINAL_DELTA_E = 12.0
NEUTRAL_CHROMA = 8.0
MIN_GRAPHICAL_CONTRAST = 3.0
MIN_GRAYSCALE_LUMINANCE_GAP = 0.10
MIN_ALT_TEXT_CHARACTERS = 80

_SVG_NAME = "figure.svg"
_SVG_HEAD_CHARACTERS = 2000
_SVG_WIDTH_PATTERN = re.compile(r'width="([0-9.]+)(pt|px|in|mm|cm)?"')
_FONT_SIZE_PATTERN = re.compile(r'font(?:-size)?:\s*(?:[^;"]*?\s)?([0-9.]+)px')
_UNIT_TO_MM = {"pt": 25.4 / 72.0, "px": 25.4 / 96.0, "in": 25.4, "mm": 1.0, "cm": 10.0}


def _constraints(bundle: RunBundle) -> dict[str, Any]:
    constraints = bundle.profile.get("constraints")
    return constraints if isinstance(constraints, dict) else {}


def _series_cardinality(bundle: RunBundle) -> int:
    column = bundle.spec.chart.series
    if not column:
        return 1
    data_path = bundle.path(bundle.spec.data.source)
    if not data_path.is_file():
        return 1
    with data_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or column not in reader.fieldnames:
            return 1
        values = {str(row.get(column, "")).strip() for row in reader}
    return max(1, len(values))


def _reviewed_colors(bundle: RunBundle) -> list[str]:
    """Return the categorical colours the renderer assigns to this figure."""
    raw_palette = bundle.profile.get("palette")
    if not isinstance(raw_palette, list) or not raw_palette:
        return []
    palette = [str(item).strip().lower() for item in raw_palette]
    candidates: list[str] = []
    for index in range(_series_cardinality(bundle)):
        candidate = palette[index % len(palette)]
        if candidate not in candidates:
            candidates.append(candidate)
    highlight = bundle.profile.get("highlight_color")
    if bundle.spec.chart.highlight and isinstance(highlight, str):
        normalized = highlight.strip().lower()
        if normalized not in candidates:
            candidates.append(normalized)

    colors: list[str] = []
    for candidate in candidates:
        try:
            parse_hex(candidate)
        except ValueError:
            continue
        colors.append(candidate)
    return colors


def review_artifacts(bundle: RunBundle) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    expected = [
        *REQUIRED_RUN_ARTIFACTS,
        *(f"figure.{name}" for name in bundle.spec.export.formats),
    ]
    for name in dict.fromkeys(expected):
        if bundle.path(name).is_file():
            continue
        findings.append(
            ReviewFinding(
                rule_id="BUNDLE_ARTIFACT_MISSING",
                severity="error",
                message=f"The run bundle is missing a required artifact: {name}.",
                evidence=f"expected {name} in {bundle.root.name}",
                remediation="Re-run paperfig render and keep the whole output directory.",
            )
        )
    return findings


def review_manifest(bundle: RunBundle) -> list[ReviewFinding]:
    if bundle.manifest is None:
        return [
            ReviewFinding(
                rule_id="MANIFEST_MISSING",
                severity="error",
                message="The bundle has no artifact manifest, so integrity cannot be checked.",
                evidence=f"expected {BUNDLE_MANIFEST_NAME}",
                remediation="Re-render with a paperfig version that writes a manifest.",
            )
        ]

    findings: list[ReviewFinding] = []
    if bundle.manifest.get("schema_version") != 1:
        findings.append(
            ReviewFinding(
                rule_id="MANIFEST_SCHEMA_UNKNOWN",
                severity="warning",
                message="The artifact manifest uses an unrecognized schema version.",
                evidence=f"schema_version={bundle.manifest.get('schema_version')!r}",
                remediation="Regenerate the bundle with the current paperfig release.",
            )
        )

    entries = bundle.manifest.get("artifacts")
    if not isinstance(entries, list) or not entries:
        findings.append(
            ReviewFinding(
                rule_id="MANIFEST_EMPTY",
                severity="error",
                message="The artifact manifest records no artifacts.",
                evidence=f"artifacts={entries!r}",
                remediation="Re-run paperfig render to rebuild the manifest.",
            )
        )
        return findings

    tracked: set[str] = set()
    for entry in entries:
        name = str(entry.get("path", "")).strip() if isinstance(entry, dict) else ""
        if not name:
            findings.append(
                ReviewFinding(
                    rule_id="MANIFEST_ENTRY_MALFORMED",
                    severity="warning",
                    message="An artifact manifest entry has no usable path.",
                    evidence=f"entry={entry!r}",
                    remediation="Re-run paperfig render to rebuild the manifest.",
                )
            )
            continue
        tracked.add(name)
        target = bundle.path(name)
        if not target.is_file():
            findings.append(
                ReviewFinding(
                    rule_id="MANIFEST_ENTRY_MISSING",
                    severity="error",
                    message=f"A manifest-tracked artifact is absent from the bundle: {name}.",
                    evidence=f"missing {name}",
                    remediation="Restore the artifact or re-render the figure.",
                )
            )
            continue
        digest = sha256_file(target)
        if digest != str(entry.get("sha256", "")):
            findings.append(
                ReviewFinding(
                    rule_id="MANIFEST_DIGEST_MISMATCH",
                    severity="error",
                    message=f"{name} no longer matches the digest recorded at render time.",
                    evidence=f"recorded={entry.get('sha256')!r}; observed={digest}",
                    remediation="Re-render instead of editing artifacts inside a bundle.",
                )
            )
            continue
        size = entry.get("size_bytes")
        observed_size = target.stat().st_size
        if isinstance(size, int) and observed_size != size:
            findings.append(
                ReviewFinding(
                    rule_id="MANIFEST_SIZE_MISMATCH",
                    severity="warning",
                    message=f"{name} does not match the size recorded at render time.",
                    evidence=f"recorded={size}; observed={observed_size}",
                    remediation="Re-render the figure to refresh the manifest.",
                )
            )

    ignored = {BUNDLE_MANIFEST_NAME, *REVIEW_ARTIFACTS}
    for child in sorted(bundle.root.iterdir()):
        if not child.is_file() or child.name in tracked or child.name in ignored:
            continue
        findings.append(
            ReviewFinding(
                rule_id="MANIFEST_UNTRACKED_FILE",
                severity="warning",
                message=f"The manifest does not track a file in the bundle: {child.name}.",
                evidence=f"untracked {child.name}",
                remediation="Remove the file or re-render so the manifest covers it.",
            )
        )
    return findings


def review_colors(bundle: RunBundle) -> list[ReviewFinding]:
    if bundle.spec.chart.mark == "heatmap":
        return [
            ReviewFinding(
                rule_id="SEQUENTIAL_COLORMAP_NOT_REVIEWED",
                severity="info",
                message=(
                    "Heatmaps use a continuous colormap; colormap uniformity and "
                    "dichromat review of colormaps are not implemented yet."
                ),
                evidence="chart.mark=heatmap",
                remediation="Review the colormap manually before submission.",
            )
        ]

    colors = _reviewed_colors(bundle)
    if not colors:
        return [
            ReviewFinding(
                rule_id="PALETTE_NOT_REVIEWABLE",
                severity="info",
                message="The venue profile records no usable categorical palette.",
                evidence=f"venue={bundle.spec.venue}",
                remediation="Add hexadecimal palette entries to the venue profile.",
            )
        ]

    findings: list[ReviewFinding] = []
    hard_gate = bundle.spec.qa.color_vision_gate
    grayscale_required = bool(_constraints(bundle).get("grayscale_legibility_required"))

    for first, second in itertools.combinations(colors, 2):
        left = parse_hex(first)
        right = parse_hex(second)
        cvd_type, distance = worst_dichromat_delta_e(left, right)
        evidence = f"{first} vs {second}; simulated {cvd_type} deltaE76={distance:.1f}"
        if distance < COLLISION_DELTA_E:
            findings.append(
                ReviewFinding(
                    rule_id="CVD_COLOR_COLLISION",
                    severity="error" if hard_gate else "warning",
                    message=(
                        "Two series colours are effectively indistinguishable for a "
                        "simulated dichromat reader."
                    ),
                    evidence=evidence,
                    remediation="Separate the colours, or add shape or pattern encoding.",
                )
            )
        elif distance < MARGINAL_DELTA_E:
            findings.append(
                ReviewFinding(
                    rule_id="CVD_COLOR_MARGINAL",
                    severity="warning",
                    message=(
                        "Two series colours stay close together for a simulated "
                        "dichromat reader and may be hard to separate in print."
                    ),
                    evidence=evidence,
                    remediation="Increase the separation or add a non-colour encoding.",
                )
            )
        if not grayscale_required:
            continue
        gap = abs(relative_luminance(left) - relative_luminance(right))
        if gap < MIN_GRAYSCALE_LUMINANCE_GAP:
            findings.append(
                ReviewFinding(
                    rule_id="GRAYSCALE_LUMINANCE_COLLISION",
                    severity="warning",
                    message=(
                        "This venue expects greyscale legibility, but two series "
                        "colours share almost the same luminance."
                    ),
                    evidence=f"{first} vs {second}; luminance gap={gap:.3f}",
                    remediation="Vary lightness, not only hue, between series.",
                )
            )

    for color in colors:
        rgb = parse_hex(color)
        ratio = contrast_ratio(rgb, WHITE)
        if ratio < MIN_GRAPHICAL_CONTRAST:
            findings.append(
                ReviewFinding(
                    rule_id="LOW_CONTRAST_AGAINST_BACKGROUND",
                    severity="warning",
                    message=(
                        "A series colour falls below the WCAG 3:1 non-text contrast "
                        "ratio against a white background."
                    ),
                    evidence=f"{color}; contrast ratio={ratio:.2f}:1",
                    remediation="Darken the colour or outline the mark.",
                )
            )
        color_chroma = chroma(rgb)
        if len(colors) > 1 and color_chroma < NEUTRAL_CHROMA:
            findings.append(
                ReviewFinding(
                    rule_id="LOW_CHROMA_SERIES_COLOR",
                    severity="warning",
                    message=(
                        "A series colour is nearly neutral and can be confused with "
                        "grid lines and axis furniture."
                    ),
                    evidence=f"{color}; CIE chroma={color_chroma:.1f}",
                    remediation="Reserve near-grey tones for non-data elements.",
                )
            )
    return findings


def review_typography(bundle: RunBundle) -> list[ReviewFinding]:
    svg = bundle.read_text(_SVG_NAME)
    if svg is None:
        return [
            ReviewFinding(
                rule_id="TYPOGRAPHY_NOT_VERIFIABLE",
                severity="info",
                message="No SVG artifact is available, so label sizes were not measured.",
                evidence=f"{_SVG_NAME} is absent",
                remediation="Export SVG so typography can be reviewed automatically.",
            )
        ]

    sizes: set[float] = set()
    for value in _FONT_SIZE_PATTERN.findall(svg):
        try:
            sizes.add(float(value))
        except ValueError:
            continue
    if not sizes:
        return [
            ReviewFinding(
                rule_id="TYPOGRAPHY_NOT_VERIFIABLE",
                severity="info",
                message="The SVG declares no readable font sizes, so labels were not measured.",
                evidence="no font-size declaration matched",
                remediation="Keep SVG text as text rather than converting it to paths.",
            )
        ]

    ordered = sorted(sizes)
    observed = "observed sizes (pt): " + ", ".join(f"{size:g}" for size in ordered)
    bounds = _constraints(bundle).get("label_font_size_pt")
    if not isinstance(bounds, list) or len(bounds) != 2:
        return [
            ReviewFinding(
                rule_id="VENUE_FONT_RANGE_UNSPECIFIED",
                severity="info",
                message="This venue profile records no label font-size range to check.",
                evidence=observed,
                remediation="Add label_font_size_pt to the venue profile once verified.",
            )
        ]

    try:
        minimum = float(bounds[0])
    except (TypeError, ValueError):
        return []
    if ordered[0] < minimum - 0.05:
        return [
            ReviewFinding(
                rule_id="FONT_SIZE_BELOW_VENUE_MINIMUM",
                severity="warning",
                message="Some label text is smaller than the minimum size this venue states.",
                evidence=f"{observed}; venue minimum={minimum:g}",
                remediation="Raise the profile base font size or shorten the labels.",
            )
        ]
    return []


def review_dimensions(bundle: RunBundle) -> list[ReviewFinding]:
    raw_limit = _constraints(bundle).get("max_width_mm")
    if raw_limit is None:
        return []
    try:
        limit_mm = float(raw_limit)
    except (TypeError, ValueError):
        return []

    svg = bundle.read_text(_SVG_NAME)
    if svg is None:
        return []
    match = _SVG_WIDTH_PATTERN.search(svg[:_SVG_HEAD_CHARACTERS])
    unit = match.group(2) or "px" if match else "px"
    if match is None or unit not in _UNIT_TO_MM:
        return [
            ReviewFinding(
                rule_id="FIGURE_WIDTH_NOT_VERIFIABLE",
                severity="info",
                message="The SVG root declares no readable width, so size was not checked.",
                evidence=f"venue limit={limit_mm:g} mm",
                remediation="Inspect the exported width manually.",
            )
        ]
    width_mm = float(match.group(1)) * _UNIT_TO_MM[unit]
    if width_mm > limit_mm + 0.5:
        return [
            ReviewFinding(
                rule_id="FIGURE_WIDTH_EXCEEDS_VENUE",
                severity="warning",
                message="The exported figure is wider than this venue allows.",
                evidence=f"width={width_mm:.1f} mm; venue limit={limit_mm:g} mm",
                remediation="Use a narrower layout width in the FigureSpec.",
            )
        ]
    return []


def review_alt_text(bundle: RunBundle) -> list[ReviewFinding]:
    text = (bundle.read_text("figure.alt.txt") or "").strip()
    if not text:
        if bundle.spec.qa.require_alt_text:
            return [
                ReviewFinding(
                    rule_id="ALT_TEXT_MISSING",
                    severity="error",
                    message="The FigureSpec requires alt text, but the bundle has none.",
                    evidence="figure.alt.txt is absent or empty",
                    remediation="Re-render the figure so alt text is generated.",
                )
            ]
        return []
    if len(text) < MIN_ALT_TEXT_CHARACTERS:
        return [
            ReviewFinding(
                rule_id="ALT_TEXT_TOO_SHORT",
                severity="warning",
                message="The alt text is too short to describe the figure to a screen reader.",
                evidence=f"{len(text)} characters",
                remediation="Describe the encoding, the comparison, and the takeaway.",
            )
        ]
    return []


def review_encoding(bundle: RunBundle) -> list[ReviewFinding]:
    mark = bundle.spec.chart.mark
    if mark not in {"line", "scatter"} or not bundle.spec.chart.series:
        return []
    groups = _series_cardinality(bundle)
    if groups < 2:
        return []
    return [
        ReviewFinding(
            rule_id="REDUNDANT_ENCODING_MISSING",
            severity="warning",
            message=(
                "Series in line and scatter marks are currently separated by colour "
                "alone, so the figure is not robust to greyscale reproduction."
            ),
            evidence=f"chart.mark={mark}; series={bundle.spec.chart.series}; groups={groups}",
            remediation="Add marker or dash variation per series, or label series directly.",
        )
    ]


def review_bundle(path: str | Path) -> list[ReviewFinding]:
    """Review a rendered run bundle and return every deterministic finding."""
    bundle = load_bundle(path)
    findings: list[ReviewFinding] = []
    findings.extend(review_artifacts(bundle))
    findings.extend(review_manifest(bundle))
    findings.extend(review_colors(bundle))
    findings.extend(review_typography(bundle))
    findings.extend(review_dimensions(bundle))
    findings.extend(review_alt_text(bundle))
    findings.extend(review_encoding(bundle))
    return findings
