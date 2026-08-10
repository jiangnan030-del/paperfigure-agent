# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class AuditIssue:
    rule_id: str
    severity: Literal["info", "warning", "error"]
    message: str
    evidence: str
    auto_fixable: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
