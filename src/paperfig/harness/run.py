# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import platform
import shutil
from datetime import UTC, datetime
from pathlib import Path

import matplotlib.pyplot as plt

from paperfig import __version__
from paperfig.data import load_csv_records
from paperfig.export import export_figure
from paperfig.profiles import load_profile
from paperfig.provenance.record import build_provenance, write_provenance
from paperfig.qa import write_audit
from paperfig.renderers.matplotlib import render_figure
from paperfig.spec import FigureSpec, load_spec


def _required_columns(spec: FigureSpec) -> set[str]:
    columns = {spec.chart.x, spec.chart.y}
    for optional in (spec.chart.series, spec.chart.error):
        if optional:
            columns.add(optional)
    return columns


def _write_replay_script(output: Path) -> None:
    content = (
        "# SPDX-License-Identifier: MIT\\n"
        "\\\"\\\"\\\"Replay this figure from the canonical FigureSpec.\\\"\\\"\\\"\\n"
        "from paperfig.harness import render_spec\\n\\n"
        "if __name__ == \\\"__main__\\\":\\n"
        "    render_spec(\\\"figure.spec.yaml\\\", \\\".\\\")\\n"
    )
    (output / "figure.py").write_text(content, encoding="utf-8")


def _write_alt_text(spec: FigureSpec, records: list[dict[str, object]], output: Path) -> None:
    text = (
        f"{spec.chart.mark.title()} chart supporting the claim: {spec.claim} "
        f"The chart compares {spec.chart.y} by {spec.chart.x}"
        + (f" and {spec.chart.series}" if spec.chart.series else "")
        + f" using {len(records)} plotted records. Verify values against the accompanying data and provenance."
    )
    (output / "figure.alt.txt").write_text(text + "\n", encoding="utf-8")


def render_spec(spec_path: str | Path, output_dir: str | Path) -> list[Path]:
    source_spec = Path(spec_path).resolve()
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    spec = load_spec(source_spec)
    data_path = (source_spec.parent / spec.data.source).resolve()
    records = load_csv_records(data_path, _required_columns(spec))
    profile = load_profile(spec.venue)

    started = datetime.now(UTC).isoformat()
    figure = render_figure(spec, records, profile)
    artifacts = export_figure(figure, output, spec.export.formats, spec.export.dpi)
    plt.close(figure)

    shutil.copy2(source_spec, output / "figure.spec.yaml")
    _write_replay_script(output)
    _write_alt_text(spec, records, output)
    write_audit(spec, output / "figure.audit.json", artifact_dir=output)

    provenance = build_provenance(spec, source_spec, data_path, artifacts, profile)
    write_provenance(provenance, output / "figure.provenance.json")

    (output / "environment.lock").write_text(
        f"paperfigure-agent=={__version__}\npython=={platform.python_version()}\n",
        encoding="utf-8",
    )
    log_entry = {
        "event": "render.completed",
        "started_at": started,
        "finished_at": datetime.now(UTC).isoformat(),
        "spec": str(source_spec),
        "data": str(data_path),
        "artifacts": [item.name for item in artifacts],
    }
    (output / "run.log.jsonl").write_text(json.dumps(log_entry) + "\n", encoding="utf-8")
    return artifacts
