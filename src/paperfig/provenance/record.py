# SPDX-License-Identifier: MIT
from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from paperfig import __version__
from paperfig.spec.models import FigureSpec


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_provenance(
    spec: FigureSpec,
    spec_path: str | Path,
    data_path: str | Path,
    artifacts: list[Path],
    profile: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "software": {"name": "paperfigure-agent", "version": __version__},
        "runtime": {"python": platform.python_version(), "platform": platform.platform()},
        "inputs": {
            "spec": {"path": str(Path(spec_path)), "sha256": sha256_file(spec_path)},
            "data": {
                "path": str(Path(data_path)),
                "sha256": sha256_file(data_path),
                "license": spec.data.license,
                "citation": spec.data.citation,
            },
        },
        "figure_spec": asdict(spec),
        "venue_profile": {
            "name": profile.get("name"),
            "status": profile.get("status", "legacy-starter"),
            "verified_on": profile.get("verified_on"),
            "source_status": profile.get("source_status"),
            "sources": profile.get("sources", []),
        },
        "artifacts": [
            {"path": item.name, "sha256": sha256_file(item)} for item in sorted(artifacts)
        ],
        "human_review_required": True,
    }


def write_provenance(payload: dict[str, Any], output: str | Path) -> None:
    Path(output).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
