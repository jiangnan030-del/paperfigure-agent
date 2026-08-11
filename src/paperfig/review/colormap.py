# SPDX-License-Identifier: MIT
"""Deterministic perceptual checks for continuous scientific colormaps."""
from __future__ import annotations

import math

from matplotlib import colormaps

from paperfig.review.color import (
    CVD_TYPES,
    Lab,
    Rgb,
    delta_e76,
    lab,
    lab_from_linear,
    simulate_dichromacy,
)
from paperfig.review.models import ReviewFinding

DEFAULT_HEATMAP_COLORMAP = "viridis"
COLORMAP_SAMPLE_COUNT = 17
LIGHTNESS_REVERSAL_TOLERANCE = 0.5
MAX_STEP_COEFFICIENT_OF_VARIATION = 0.30
MIN_CVD_STEP_DELTA_E = 1.5
MIN_ENDPOINT_DELTA_E = 20.0


def _samples(name: str) -> list[Rgb]:
    try:
        colormap = colormaps[name]
    except KeyError as exc:
        raise ValueError(f"unknown Matplotlib colormap: {name}") from exc
    maximum = COLORMAP_SAMPLE_COUNT - 1
    return [
        tuple(float(channel) for channel in colormap(index / maximum)[:3])
        for index in range(COLORMAP_SAMPLE_COUNT)
    ]


def _simulated_labs(colors: list[Rgb], cvd_type: str | None) -> list[Lab]:
    if cvd_type is None:
        return [lab(color) for color in colors]
    return [lab_from_linear(simulate_dichromacy(color, cvd_type)) for color in colors]


def _steps(values: list[Lab]) -> list[float]:
    return [
        delta_e76(left, right)
        for left, right in zip(values, values[1:], strict=False)
    ]


def _coefficient_of_variation(values: list[float]) -> float:
    mean = sum(values) / len(values)
    if mean == 0.0:
        return math.inf
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance) / mean


def _lightness_reversals(values: list[Lab]) -> tuple[str, int, float]:
    direction = 1.0 if values[-1][0] >= values[0][0] else -1.0
    changes = [
        direction * (right[0] - left[0])
        for left, right in zip(values, values[1:], strict=False)
    ]
    reversals = [change for change in changes if change < -LIGHTNESS_REVERSAL_TOLERANCE]
    label = "increasing" if direction > 0.0 else "decreasing"
    worst = min(changes, default=0.0)
    return label, len(reversals), worst


def review_sequential_colormap(name: str, hard_gate: bool) -> list[ReviewFinding]:
    """Review sampled lightness, perceptual steps, endpoints, and CVD behaviour."""
    try:
        colors = _samples(name)
    except ValueError as exc:
        return [
            ReviewFinding(
                rule_id="COLORMAP_NOT_REVIEWABLE",
                severity="error",
                message="The configured continuous colormap could not be sampled.",
                evidence=str(exc),
                remediation="Use a registered sequential Matplotlib colormap.",
            )
        ]

    findings: list[ReviewFinding] = []
    normal = _simulated_labs(colors, None)
    direction, reversals, worst = _lightness_reversals(normal)
    if reversals:
        findings.append(
            ReviewFinding(
                rule_id="COLORMAP_LIGHTNESS_REVERSAL",
                severity="error" if hard_gate else "warning",
                message="The sequential colormap reverses lightness within its data range.",
                evidence=(
                    f"colormap={name}; samples={COLORMAP_SAMPLE_COUNT}; direction={direction}; "
                    f"reversals={reversals}; worst signed step={worst:.2f} L*"
                ),
                remediation="Use a perceptually ordered sequential colormap such as viridis.",
            )
        )

    normal_steps = _steps(normal)
    variation = _coefficient_of_variation(normal_steps)
    if variation > MAX_STEP_COEFFICIENT_OF_VARIATION:
        findings.append(
            ReviewFinding(
                rule_id="COLORMAP_NONUNIFORM_STEPS",
                severity="warning",
                message="Equal data intervals do not produce reasonably uniform colour changes.",
                evidence=(
                    f"colormap={name}; step CV={variation:.3f}; "
                    f"allowed={MAX_STEP_COEFFICIENT_OF_VARIATION:.2f}"
                ),
                remediation="Use a perceptually uniform sequential colormap.",
            )
        )

    endpoint_scores = [("normal", delta_e76(normal[0], normal[-1]))]
    minimum_step = math.inf
    minimum_mode = ""
    for cvd_type in CVD_TYPES:
        simulated = _simulated_labs(colors, cvd_type)
        cvd_direction, cvd_reversals, cvd_worst = _lightness_reversals(simulated)
        if cvd_reversals:
            findings.append(
                ReviewFinding(
                    rule_id="COLORMAP_CVD_LIGHTNESS_REVERSAL",
                    severity="error" if hard_gate else "warning",
                    message=(
                        "The colormap loses monotonic lightness under dichromat simulation."
                    ),
                    evidence=(
                        f"colormap={name}; simulated={cvd_type}; direction={cvd_direction}; "
                        f"reversals={cvd_reversals}; worst signed step={cvd_worst:.2f} L*"
                    ),
                    remediation="Choose a colormap whose lightness ordering survives CVD.",
                )
            )
        steps = _steps(simulated)
        if min(steps) < minimum_step:
            minimum_step = min(steps)
            minimum_mode = cvd_type
        endpoint_scores.append((cvd_type, delta_e76(simulated[0], simulated[-1])))

    if minimum_step < MIN_CVD_STEP_DELTA_E:
        findings.append(
            ReviewFinding(
                rule_id="COLORMAP_CVD_FLAT_SPOT",
                severity="warning",
                message="Part of the colormap becomes nearly flat under dichromat simulation.",
                evidence=(
                    f"colormap={name}; simulated={minimum_mode}; minimum adjacent "
                    f"deltaE76={minimum_step:.2f}; required={MIN_CVD_STEP_DELTA_E:.1f}"
                ),
                remediation="Use a CVD-robust colormap or add numeric cell labels.",
            )
        )

    endpoint_mode, endpoint_score = min(endpoint_scores, key=lambda item: item[1])
    if endpoint_score < MIN_ENDPOINT_DELTA_E:
        findings.append(
            ReviewFinding(
                rule_id="COLORMAP_ENDPOINT_COLLISION",
                severity="error" if hard_gate else "warning",
                message="The two ends of the sequential colormap are not clearly separated.",
                evidence=(
                    f"colormap={name}; mode={endpoint_mode}; endpoint "
                    f"deltaE76={endpoint_score:.1f}; required={MIN_ENDPOINT_DELTA_E:.1f}"
                ),
                remediation="Increase endpoint separation or choose another colormap.",
            )
        )
    return findings
