# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from pathlib import Path

from paperfig.comparison.models import BundleComparison

COMPARISON_JSON_NAME = "figure.comparison.json"
COMPARISON_MARKDOWN_NAME = "figure.comparison.md"


def render_markdown(comparison: BundleComparison) -> str:
    payload = comparison.to_dict()
    summary = payload["summary"]
    lines = [
        f"# Figure comparison: {comparison.baseline} -> {comparison.candidate}",
        "",
        f"- status: **{payload['status']}**",
        f"- errors: {summary['error']}",
        f"- warnings: {summary['warning']}",
        f"- notes: {summary['info']}",
        "",
    ]
    if not comparison.findings:
        lines.extend(["The bundles are equivalent under the current rule set.", ""])
    for finding in comparison.findings:
        lines.extend(
            [
                f"## {finding.severity.upper()}: {finding.rule_id}",
                "",
                finding.message,
                "",
                f"- evidence: `{finding.evidence}`",
            ]
        )
        if finding.remediation:
            lines.append(f"- suggested action: {finding.remediation}")
        lines.append("")
    lines.extend(
        [
            "A passing comparison means no tracked regression was found; it does not "
            "validate the scientific claim.",
            "",
        ]
    )
    return "\n".join(lines)


def write_comparison(
    output_dir: str | Path, comparison: BundleComparison
) -> tuple[Path, Path]:
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / COMPARISON_JSON_NAME
    json_path.write_text(
        json.dumps(comparison.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path = root / COMPARISON_MARKDOWN_NAME
    markdown_path.write_text(render_markdown(comparison), encoding="utf-8")
    return json_path, markdown_path
