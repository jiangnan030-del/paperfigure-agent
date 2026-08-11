# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from paperfig.review.models import ReviewFinding, count_by_severity


@dataclass(frozen=True)
class BundleComparison:
    """Deterministic comparison of a baseline and candidate run bundle."""

    baseline: str
    candidate: str
    findings: list[ReviewFinding]
    baseline_review: dict[str, int]
    candidate_review: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        counts = count_by_severity(self.findings)
        return {
            "schema_version": 1,
            "status": "failed" if counts["error"] else "passed",
            "baseline": self.baseline,
            "candidate": self.candidate,
            "summary": counts,
            "baseline_review": self.baseline_review,
            "candidate_review": self.candidate_review,
            "findings": [finding.to_dict() for finding in self.findings],
            "human_review_required": True,
        }
