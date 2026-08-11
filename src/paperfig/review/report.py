# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from paperfig import __version__
from paperfig.review.models import ReviewFinding, count_by_severity

REVIEW_JSON_NAME = "figure.review.json"
REVIEW_MARKDOWN_NAME = "figure.review.md"

LIMITATIONS = (
    "Reviewer Mode is deterministic and rule-based; it is not peer review.",
    "Dichromat simulation is a linear approximation and omits anomalous trichromacy.",
    "Continuous colormaps, panel composition, and statistics are not reviewed yet.",
    "A passing review does not validate the scientific claim behind the figure.",
)


def review_payload(root: Path, findings: Sequence[ReviewFinding]) -> dict[str, Any]:
    counts = count_by_severity(findings)
    return {
        "schema_version": 1,
        "status": "failed" if counts["error"] else "passed",
        "generated_at": datetime.now(UTC).isoformat(),
        "tool": {"name": "paperfigure-agent", "version": __version__},
        "bundle": root.name,
        "summary": counts,
        "findings": [finding.to_dict() for finding in findings],
        "limitations": list(LIMITATIONS),
        "human_review_required": True,
    }


def render_markdown(root: Path, findings: Sequence[ReviewFinding]) -> str:
    counts = count_by_severity(findings)
    status = "failed" if counts["error"] else "passed"
    lines = [
        f"# Figure review: {root.name}",
        "",
        f"- status: **{status}**",
        f"- errors: {counts['error']}",
        f"- warnings: {counts['warning']}",
        f"- notes: {counts['info']}",
        "",
    ]
    if not findings:
        lines.extend(["The current rule set produced no findings.", ""])
    for severity in ("error", "warning", "info"):
        selected = [item for item in findings if item.severity == severity]
        if not selected:
            continue
        lines.extend([f"## {severity.title()} ({len(selected)})", ""])
        for finding in selected:
            lines.extend([f"### {finding.rule_id}", "", finding.message, ""])
            lines.append(f"- evidence: `{finding.evidence}`")
            if finding.remediation:
                lines.append(f"- suggested action: {finding.remediation}")
            lines.append("")
    lines.extend(["## Limitations", ""])
    lines.extend(f"- {item}" for item in LIMITATIONS)
    lines.extend(["", "This report supports human review. It does not replace it.", ""])
    return "\n".join(lines)


def write_review(bundle_dir: str | Path, findings: Sequence[ReviewFinding]) -> tuple[Path, Path]:
    """Write the JSON and Markdown reviewer reports into the run bundle."""
    root = Path(bundle_dir).resolve()
    json_path = root / REVIEW_JSON_NAME
    json_path.write_text(
        json.dumps(review_payload(root, findings), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path = root / REVIEW_MARKDOWN_NAME
    markdown_path.write_text(render_markdown(root, findings), encoding="utf-8")
    return json_path, markdown_path
