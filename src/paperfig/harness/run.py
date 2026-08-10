# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import platform
import random
import shutil
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from paperfig import __version__
from paperfig.data import load_csv_records, validate_records
from paperfig.export import export_figure
from paperfig.profiles import load_profile
from paperfig.provenance.record import build_provenance, write_provenance
from paperfig.qa import write_audit
from paperfig.renderers.matplotlib import close_figure, render_figure
from paperfig.spec import FigureSpec, load_spec


def _required_columns(spec: FigureSpec) -> set[str]:
    return set(spec.chart.required_columns())


def _write_replay_script(output: Path) -> None:
    content = '''# SPDX-License-Identifier: MIT
"""Replay this figure from the canonical FigureSpec."""
from paperfig.harness import render_spec

if __name__ == "__main__":
    render_spec("figure.spec.yaml", ".")
'''
    (output / "figure.py").write_text(content, encoding="utf-8")


def _write_alt_text(spec: FigureSpec, records: list[dict[str, object]], output: Path) -> None:
    series_text = f", grouped by {spec.chart.series}" if spec.chart.series else ""
    value_text = f", encoded by {spec.chart.value}" if spec.chart.value else ""
    interval_text = (
        f", with bounds {spec.chart.lower} to {spec.chart.upper}"
        if spec.chart.lower and spec.chart.upper
        else ""
    )
    text = (
        f"{spec.chart.mark.title()} chart related to the claim: {spec.claim} "
        f"It maps {spec.chart.x} and {spec.chart.y}{series_text}{value_text}{interval_text} "
        f"across {len(records)} records. Verify values and transformations against the "
        "accompanying data and provenance record."
    )
    (output / "figure.alt.txt").write_text(text + "\n", encoding="utf-8")


def render_spec(spec_path: str | Path, output_dir: str | Path) -> list[Path]:
    source_spec = Path(spec_path).resolve()
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    spec = load_spec(source_spec)
    data_path = (source_spec.parent / spec.data.source).resolve()
    records = load_csv_records(data_path, _required_columns(spec))
    validate_records(spec, records)
    profile = load_profile(spec.venue)

    random.seed(spec.seed)
    np.random.seed(spec.seed)
    started = datetime.now(UTC).isoformat()
    figure = render_figure(spec, records, profile)
    artifacts = export_figure(figure, output, spec.export.formats, spec.export.dpi)
    close_figure(figure)

    shutil.copy2(source_spec, output / "figure.spec.yaml")
    _write_replay_script(output)
    _write_alt_text(spec, records, output)
    write_audit(
        spec,
        output / "figure.audit.json",
        artifact_dir=output,
        data_validation_passed=True,
    )

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
        "mark": spec.chart.mark,
        "seed": spec.seed,
        "artifacts": [item.name for item in artifacts],
    }
    (output / "run.log.jsonl").write_text(json.dumps(log_entry) + "\n", encoding="utf-8")
    return artifacts
