# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any, Literal

Severity = Literal["info", "warning", "error"]

SEVERITY_ORDER: dict[str, int] = {"info": 0, "warning": 1, "error": 2}


class ReviewError(RuntimeError):
    """Raised when a run bundle cannot be reviewed at all."""


@dataclass(frozen=True)
class ReviewFinding:
    """A single deterministic observation about a rendered run bundle."""

    rule_id: str
    severity: Severity
    message: str
    evidence: str
    remediation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def count_by_severity(findings: Sequence[ReviewFinding]) -> dict[str, int]:
    counts = dict.fromkeys(SEVERITY_ORDER, 0)
    for finding in findings:
        if finding.severity in counts:
            counts[finding.severity] += 1
    return counts


def exceeds_threshold(findings: Sequence[ReviewFinding], fail_on: str) -> bool:
    """Return True when any finding is at or above the requested severity."""
    if fail_on == "never":
        return False
    if fail_on not in SEVERITY_ORDER:
        raise ReviewError(f"unsupported failure threshold: {fail_on}")
    threshold = SEVERITY_ORDER[fail_on]
    return any(SEVERITY_ORDER.get(item.severity, 0) >= threshold for item in findings)
