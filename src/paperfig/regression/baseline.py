# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from pathlib import Path

from paperfig.regression.fingerprint import FigureFingerprint, RegressionError

BASELINE_SUFFIX = ".baseline.json"

#: Baselines are committed to the repository so that a rendering change shows
#: up as a reviewable diff rather than an opaque binary blob.
DEFAULT_BASELINE_DIR = Path("tests/baselines")


def baseline_path(baselines_dir: str | Path, spec_name: str) -> Path:
    return Path(baselines_dir) / f"{spec_name}{BASELINE_SUFFIX}"


def write_baseline(baselines_dir: str | Path, fingerprint: FigureFingerprint) -> Path:
    """Record a fingerprint as the baseline for its FigureSpec."""
    target = baseline_path(baselines_dir, fingerprint.spec_name)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(fingerprint.to_dict(), ensure_ascii=False, indent=2)
    target.write_text(payload + "\n", encoding="utf-8")
    return target


def load_baseline(baselines_dir: str | Path, spec_name: str) -> FigureFingerprint | None:
    """Load a recorded baseline, or return None when none exists yet."""
    target = baseline_path(baselines_dir, spec_name)
    if not target.is_file():
        return None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RegressionError(f"baseline is not valid JSON: {target}") from exc
    if not isinstance(payload, dict):
        raise RegressionError(f"baseline must contain a JSON object: {target}")
    return FigureFingerprint.from_dict(payload)
