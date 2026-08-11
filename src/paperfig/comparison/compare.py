# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from paperfig.comparison.models import BundleComparison
from paperfig.provenance.record import sha256_file
from paperfig.regression import RegressionError, compare_fingerprints, fingerprint_from_bundle
from paperfig.review import review_bundle
from paperfig.review.bundle import RunBundle, load_bundle
from paperfig.review.models import (
    SEVERITY_ORDER,
    ReviewFinding,
    Severity,
    count_by_severity,
)

_SEMANTIC_PREFIXES = ("claim", "data.", "chart.", "references", "seed")
_SEVERITY_BY_RANK: dict[int, Severity] = {0: "info", 1: "warning", 2: "error"}
_PREVIEW_LIMIT = 8


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    if not isinstance(value, dict):
        return {prefix: value}
    flattened: dict[str, Any] = {}
    for key, item in value.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(item, dict):
            flattened.update(_flatten(item, path))
        else:
            flattened[path] = item
    return flattened


def _preview(changes: list[tuple[str, Any, Any]]) -> str:
    rendered = [
        f"{path}: {json.dumps(before, default=str)} -> {json.dumps(after, default=str)}"
        for path, before, after in changes[:_PREVIEW_LIMIT]
    ]
    if len(changes) > _PREVIEW_LIMIT:
        rendered.append(f"... (+{len(changes) - _PREVIEW_LIMIT} more)")
    return "; ".join(rendered)


def _spec_findings(baseline: RunBundle, candidate: RunBundle) -> list[ReviewFinding]:
    left = _flatten(asdict(baseline.spec))
    right = _flatten(asdict(candidate.spec))
    changes = [
        (path, left.get(path), right.get(path))
        for path in sorted(set(left) | set(right))
        if left.get(path) != right.get(path)
    ]
    semantic = [
        item
        for item in changes
        if any(item[0] == prefix or item[0].startswith(prefix) for prefix in _SEMANTIC_PREFIXES)
    ]
    presentation = [item for item in changes if item not in semantic]
    findings: list[ReviewFinding] = []
    if semantic:
        findings.append(
            ReviewFinding(
                rule_id="COMPARISON_SPEC_SEMANTICS_CHANGED",
                severity="error",
                message="The candidate changes scientific or data-encoding parts of the spec.",
                evidence=_preview(semantic),
                remediation="Review and approve the semantic change before choosing a candidate.",
            )
        )
    if presentation:
        findings.append(
            ReviewFinding(
                rule_id="COMPARISON_SPEC_PRESENTATION_CHANGED",
                severity="info",
                message="The candidate changes presentation or export settings.",
                evidence=_preview(presentation),
                remediation="Confirm that the presentation change is intentional.",
            )
        )
    return findings


def _data_digest(bundle: RunBundle) -> str | None:
    path = bundle.path(bundle.spec.data.source)
    return sha256_file(path) if path.is_file() else None


def _review_severities(findings: list[ReviewFinding]) -> dict[str, int]:
    severities: dict[str, int] = {}
    for finding in findings:
        rank = SEVERITY_ORDER.get(finding.severity, 0)
        severities[finding.rule_id] = max(rank, severities.get(finding.rule_id, -1))
    return severities


def _review_delta(
    baseline_findings: list[ReviewFinding], candidate_findings: list[ReviewFinding]
) -> list[ReviewFinding]:
    before = _review_severities(baseline_findings)
    after = _review_severities(candidate_findings)
    findings: list[ReviewFinding] = []
    for rule_id in sorted(set(before) | set(after)):
        baseline_rank = before.get(rule_id, -1)
        candidate_rank = after.get(rule_id, -1)
        if candidate_rank > baseline_rank:
            findings.append(
                ReviewFinding(
                    rule_id="COMPARISON_REVIEW_REGRESSION",
                    severity=_SEVERITY_BY_RANK[candidate_rank],
                    message="The candidate introduces or worsens a Reviewer Mode finding.",
                    evidence=(
                        f"rule={rule_id}; baseline rank={baseline_rank}; "
                        f"candidate rank={candidate_rank}"
                    ),
                    remediation="Resolve the candidate finding or retain the baseline.",
                )
            )
        elif candidate_rank < baseline_rank:
            findings.append(
                ReviewFinding(
                    rule_id="COMPARISON_REVIEW_IMPROVEMENT",
                    severity="info",
                    message="The candidate removes or reduces a Reviewer Mode finding.",
                    evidence=(
                        f"rule={rule_id}; baseline rank={baseline_rank}; "
                        f"candidate rank={candidate_rank}"
                    ),
                )
            )
    return findings


def compare_bundles(
    baseline_path: str | Path, candidate_path: str | Path
) -> BundleComparison:
    """Compare data, spec, environment, SVG structure, and review findings."""
    baseline = load_bundle(baseline_path)
    candidate = load_bundle(candidate_path)
    baseline_review = review_bundle(baseline.root)
    candidate_review = review_bundle(candidate.root)
    findings: list[ReviewFinding] = []

    baseline_digest = _data_digest(baseline)
    candidate_digest = _data_digest(candidate)
    if baseline_digest != candidate_digest:
        findings.append(
            ReviewFinding(
                rule_id="COMPARISON_DATA_CHANGED",
                severity="error",
                message="The baseline and candidate do not contain identical input data.",
                evidence=f"baseline={baseline_digest}; candidate={candidate_digest}",
                remediation="Use paperfig compare only for candidates based on the same data.",
            )
        )
    findings.extend(_spec_findings(baseline, candidate))

    baseline_environment = baseline.read_text("environment.lock")
    candidate_environment = candidate.read_text("environment.lock")
    if baseline_environment != candidate_environment:
        findings.append(
            ReviewFinding(
                rule_id="COMPARISON_ENVIRONMENT_CHANGED",
                severity="warning",
                message="The two bundles were rendered in different recorded environments.",
                evidence="environment.lock differs",
                remediation="Re-render both candidates in one pinned environment.",
            )
        )

    try:
        left = fingerprint_from_bundle(baseline.root, baseline.root.name)
        right = fingerprint_from_bundle(candidate.root, candidate.root.name)
        findings.extend(compare_fingerprints(left, right))
    except RegressionError as exc:
        findings.append(
            ReviewFinding(
                rule_id="COMPARISON_VISUAL_NOT_AVAILABLE",
                severity="error",
                message="The two SVG structures could not be compared.",
                evidence=str(exc),
                remediation="Render both candidates with SVG enabled.",
            )
        )

    findings.extend(_review_delta(baseline_review, candidate_review))
    return BundleComparison(
        baseline=baseline.root.name,
        candidate=candidate.root.name,
        findings=findings,
        baseline_review=count_by_severity(baseline_review),
        candidate_review=count_by_severity(candidate_review),
    )
