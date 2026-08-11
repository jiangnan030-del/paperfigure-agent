# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
import platform
import random
import shutil
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from paperfig import __version__
from paperfig.data import load_csv_records, validate_records
from paperfig.export import export_figure
from paperfig.profiles import load_profile
from paperfig.provenance.record import build_provenance, sha256_file, write_provenance
from paperfig.qa import AuditError, write_audit
from paperfig.renderers.matplotlib import close_figure, render_figure
from paperfig.spec import FigureSpec, load_spec

_REPLAY_DATA_NAME = "figure.data.csv"


def _required_columns(spec: FigureSpec) -> set[str]:
    return set(spec.chart.required_columns())


def _write_replay_bundle(
    source_spec: Path,
    data_path: Path,
    output: Path,
) -> tuple[Path, Path]:
    raw = yaml.safe_load(source_spec.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("data"), dict):
        raise ValueError("validated FigureSpec did not contain a data mapping")

    replay_data = (output / _REPLAY_DATA_NAME).resolve()
    if data_path.resolve() != replay_data:
        shutil.copy2(data_path, replay_data)
    raw["data"]["source"] = replay_data.name

    replay_spec = output / "figure.spec.yaml"
    replay_spec.write_text(
        yaml.safe_dump(raw, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return replay_spec, replay_data


def _write_replay_script(output: Path) -> Path:
    content = '''# SPDX-License-Identifier: MIT
"""Replay this figure from the canonical FigureSpec."""
from paperfig.harness import render_spec

if __name__ == "__main__":
    render_spec("figure.spec.yaml", ".")
'''
    path = output / "figure.py"
    path.write_text(content, encoding="utf-8")
    return path


def _write_alt_text(
    spec: FigureSpec,
    records: list[dict[str, object]],
    output: Path,
) -> Path:
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
    path = output / "figure.alt.txt"
    path.write_text(text + "\n", encoding="utf-8")
    return path


def _write_environment_lock(output: Path) -> Path:
    lines = [
        f"paperfigure-agent=={__version__}",
        f"python=={platform.python_version()}",
        f"platform=={platform.platform()}",
    ]
    for distribution in ("matplotlib", "numpy", "PyYAML"):
        try:
            installed_version = version(distribution)
        except PackageNotFoundError:
            installed_version = "unknown"
        lines.append(f"{distribution}=={installed_version}")

    path = output / "environment.lock"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _write_artifact_manifest(output: Path, paths: list[Path]) -> Path:
    unique_paths = {path.name: path for path in paths}
    payload: dict[str, Any] = {
        "schema_version": 1,
        "artifacts": [
            {
                "path": name,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for name, path in sorted(unique_paths.items())
        ],
    }
    manifest_path = output / "artifact.manifest.json"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return manifest_path


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

    replay_spec, replay_data = _write_replay_bundle(source_spec, data_path, output)
    replay_script = _write_replay_script(output)
    alt_text = _write_alt_text(spec, records, output)

    audit_path = output / "figure.audit.json"
    audit_issues = write_audit(
        spec,
        audit_path,
        artifact_dir=output,
        data_validation_passed=True,
    )

    provenance = build_provenance(spec, source_spec, data_path, artifacts, profile)
    provenance_path = output / "figure.provenance.json"
    write_provenance(provenance, provenance_path)

    environment_path = _write_environment_lock(output)
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
    log_path = output / "run.log.jsonl"
    log_path.write_text(json.dumps(log_entry) + "\n", encoding="utf-8")

    _write_artifact_manifest(
        output,
        [
            *artifacts,
            replay_spec,
            replay_data,
            replay_script,
            alt_text,
            audit_path,
            provenance_path,
            environment_path,
            log_path,
        ],
    )

    if any(issue.severity == "error" for issue in audit_issues):
        raise AuditError(f"rendered artifacts failed audit; see {audit_path}")
    return artifacts
