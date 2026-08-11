# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from pathlib import Path

from paperfig.qa.models import AuditIssue
from paperfig.spec.models import FigureSpec


class AuditError(RuntimeError):
    """Raised after preserving a run whose audit contains an error."""


def audit_spec(spec: FigureSpec, artifact_dir: str | Path | None = None) -> list[AuditIssue]:
    issues: list[AuditIssue] = []

    if spec.chart.mark == "bar" and not spec.qa.require_zero_baseline:
        issues.append(
            AuditIssue(
                rule_id="BAR_ZERO_BASELINE",
                severity="warning",
                message="Bar chart zero-baseline enforcement is disabled.",
                evidence="qa.require_zero_baseline=false",
            )
        )

    if spec.chart.mark == "scatter" and spec.chart.size:
        issues.append(
            AuditIssue(
                rule_id="AREA_ENCODING_DISCLOSURE",
                severity="info",
                message=(
                    "Scatter marker area is normalized for display; "
                    "disclose the size encoding."
                ),
                evidence=f"chart.size={spec.chart.size}",
            )
        )

    if not spec.data.license:
        issues.append(
            AuditIssue(
                rule_id="DATA_LICENSE_MISSING",
                severity="warning",
                message="The input dataset has no recorded license or rights statement.",
                evidence=f"data.source={spec.data.source}",
            )
        )

    if not spec.data.citation:
        issues.append(
            AuditIssue(
                rule_id="DATA_CITATION_MISSING",
                severity="warning",
                message="The input dataset has no recorded citation or origin statement.",
                evidence=f"data.source={spec.data.source}",
            )
        )

    if not ({"svg", "pdf"} & set(spec.export.formats)):
        issues.append(
            AuditIssue(
                rule_id="EDITABLE_FORMAT_MISSING",
                severity="warning",
                message="No vector/editable output format is requested.",
                evidence=f"export.formats={list(spec.export.formats)}",
                auto_fixable=True,
            )
        )

    for reference in spec.references:
        ref_id = str(reference.get("id", "unnamed"))
        copied_files = reference.get("copied_files", [])
        license_status = str(reference.get("license_status", "unknown"))
        if not reference.get("url"):
            issues.append(
                AuditIssue(
                    rule_id="REFERENCE_URL_MISSING",
                    severity="error",
                    message=f"Reference '{ref_id}' has no stable URL/DOI.",
                    evidence=str(reference),
                )
            )
        if copied_files and license_status in {"unknown", "unverified", "none"}:
            issues.append(
                AuditIssue(
                    rule_id="UNLICENSED_MATERIAL",
                    severity="error",
                    message=f"Reference '{ref_id}' lists copied files without verified rights.",
                    evidence=f"copied_files={copied_files}; license_status={license_status}",
                )
            )
        elif license_status in {"unknown", "unverified", "none"}:
            issues.append(
                AuditIssue(
                    rule_id="REFERENCE_LICENSE_UNVERIFIED",
                    severity="info",
                    message=f"Reference '{ref_id}' is conceptual only; its license is unverified.",
                    evidence=f"license_status={license_status}; copied_files={copied_files}",
                )
            )

    if artifact_dir is not None:
        directory = Path(artifact_dir)
        for file_format in spec.export.formats:
            expected = directory / f"figure.{file_format}"
            if not expected.is_file():
                issues.append(
                    AuditIssue(
                        rule_id="ARTIFACT_MISSING",
                        severity="error",
                        message=f"Expected artifact is missing: {expected.name}",
                        evidence=str(expected),
                    )
                )

    return issues


def write_audit(
    spec: FigureSpec,
    output: str | Path,
    artifact_dir: str | Path | None = None,
    data_validation_passed: bool | None = None,
) -> list[AuditIssue]:
    issues = audit_spec(spec, artifact_dir=artifact_dir)
    payload = {
        "schema_version": 1,
        "status": "failed" if any(issue.severity == "error" for issue in issues) else "passed",
        "checks": {
            "figure_spec": "passed",
            "data_validation": (
                "passed" if data_validation_passed else "not_run"
                if data_validation_passed is None
                else "failed"
            ),
            "artifact_presence": "passed" if artifact_dir is not None else "not_run",
        },
        "issues": [issue.to_dict() for issue in issues],
        "limitations": [
            "Rule-based MVP audit of the FigureSpec; not peer review.",
            "Color-vision and contrast checks run in paperfig review, not here.",
            "Visual regression against a recorded baseline runs in paperfig regress.",
            "Semantic model checks of the claim are not implemented.",
            "Passing checks does not validate the scientific claim or statistical method.",
        ],
    }
    Path(output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return issues
