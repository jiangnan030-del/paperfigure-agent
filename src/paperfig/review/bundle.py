# SPDX-License-Identifier: MIT
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from paperfig.profiles import load_profile
from paperfig.review.models import ReviewError
from paperfig.spec import FigureSpec, SpecError, load_spec

BUNDLE_SPEC_NAME = "figure.spec.yaml"
BUNDLE_MANIFEST_NAME = "artifact.manifest.json"


@dataclass(frozen=True)
class RunBundle:
    """A rendered run directory plus the context needed to review it."""

    root: Path
    spec: FigureSpec
    profile: dict[str, Any]
    manifest: dict[str, Any] | None

    def path(self, name: str) -> Path:
        return self.root / name

    def read_text(self, name: str) -> str | None:
        target = self.path(name)
        if not target.is_file():
            return None
        return target.read_text(encoding="utf-8", errors="replace")


def load_bundle(path: str | Path) -> RunBundle:
    """Load a rendered run bundle without mutating it."""
    root = Path(path).resolve()
    if not root.is_dir():
        raise ReviewError(f"run bundle directory does not exist: {root}")

    spec_path = root / BUNDLE_SPEC_NAME
    if not spec_path.is_file():
        raise ReviewError(f"run bundle has no {BUNDLE_SPEC_NAME}: {root}")
    try:
        spec = load_spec(spec_path)
    except SpecError as exc:
        raise ReviewError(f"bundled FigureSpec is invalid: {exc}") from exc

    try:
        profile = load_profile(spec.venue)
    except ValueError as exc:
        raise ReviewError(f"bundled venue profile is unavailable: {exc}") from exc

    manifest: dict[str, Any] | None = None
    manifest_path = root / BUNDLE_MANIFEST_NAME
    if manifest_path.is_file():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ReviewError(f"{BUNDLE_MANIFEST_NAME} is not valid JSON: {exc}") from exc
        if not isinstance(loaded, dict):
            raise ReviewError(f"{BUNDLE_MANIFEST_NAME} must contain a JSON object")
        manifest = loaded

    return RunBundle(root=root, spec=spec, profile=profile, manifest=manifest)
