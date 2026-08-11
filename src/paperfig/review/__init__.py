# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path

from paperfig.review.bundle import load_bundle
from paperfig.review.colormap import DEFAULT_HEATMAP_COLORMAP, review_sequential_colormap
from paperfig.review.models import (
    SEVERITY_ORDER,
    ReviewError,
    ReviewFinding,
    count_by_severity,
    exceeds_threshold,
)
from paperfig.review.report import REVIEW_JSON_NAME, REVIEW_MARKDOWN_NAME, write_review
from paperfig.review.rules import review_bundle as _review_bundle


def review_bundle(path: str | Path) -> list[ReviewFinding]:
    """Run Reviewer Mode, including continuous-colormap checks for heatmaps."""
    findings = _review_bundle(path)
    bundle = load_bundle(path)
    if bundle.spec.chart.mark != "heatmap":
        return findings
    findings = [
        finding
        for finding in findings
        if finding.rule_id != "SEQUENTIAL_COLORMAP_NOT_REVIEWED"
    ]
    findings.extend(
        review_sequential_colormap(
            DEFAULT_HEATMAP_COLORMAP,
            hard_gate=bundle.spec.qa.color_vision_gate,
        )
    )
    return findings


__all__ = [
    "REVIEW_JSON_NAME",
    "REVIEW_MARKDOWN_NAME",
    "SEVERITY_ORDER",
    "ReviewError",
    "ReviewFinding",
    "count_by_severity",
    "exceeds_threshold",
    "review_bundle",
    "write_review",
]
