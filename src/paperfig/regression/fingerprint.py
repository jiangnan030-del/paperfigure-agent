# SPDX-License-Identifier: MIT
"""Structural fingerprints of exported SVG figures.

A fingerprint records what a figure *contains* rather than how its pixels
happen to be rasterized.

This matters because an exported figure is not byte-reproducible. Matplotlib
writes a creation timestamp into SVG metadata, so rendering the same spec
twice produces two different files with two different digests. Hashing the
artifact therefore cannot answer "did this figure change?", and pixel diffing
answers it only within one exact rendering stack.

The fingerprint is stable under both kinds of noise: it ignores metadata, and
it quantises path coordinates before hashing them.

Only SVG is fingerprinted, because the renderer sets ``svg.fonttype='none'``,
which keeps label text as text instead of converting it to outlines.
"""
from __future__ import annotations

import hashlib
import platform
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from paperfig.review.color import extract_hex_colors

FINGERPRINT_SCHEMA_VERSION = 1

#: Path coordinates are rounded to this many points before hashing, which
#: absorbs float noise without hiding a real change in plotted geometry.
GEOMETRY_QUANTUM_PT = 1.0

_SVG_NAME = "figure.svg"

# Matches both `font-size: 7px` and the `font: 7px 'DejaVu Sans'` shorthand.
_FONT_SIZE_PATTERN = re.compile(r'font(?:-size)?:\s*(?:[^;"]*?\s)?([0-9.]+)px')
_LENGTH_PATTERN = re.compile(r"^([0-9.]+)\s*([a-z%]*)$")
_NUMBER_PATTERN = re.compile(r"-?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?")
_UNIT_TO_PT = {
    "": 1.0,
    "pt": 1.0,
    "px": 0.75,
    "in": 72.0,
    "mm": 72.0 / 25.4,
    "cm": 720.0 / 25.4,
}


class RegressionError(RuntimeError):
    """Raised when a fingerprint or baseline cannot be read or built."""


@dataclass(frozen=True)
class FigureFingerprint:
    """A structural summary of one exported SVG figure."""

    schema_version: int
    spec_name: str
    canvas_width_pt: float
    canvas_height_pt: float
    element_counts: dict[str, int]
    text_content: list[str]
    colors: list[str]
    font_sizes_pt: list[float]
    geometry_digest: str
    geometry_points: int
    environment: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> FigureFingerprint:
        try:
            return cls(
                schema_version=int(payload["schema_version"]),
                spec_name=str(payload["spec_name"]),
                canvas_width_pt=float(payload["canvas_width_pt"]),
                canvas_height_pt=float(payload["canvas_height_pt"]),
                element_counts={
                    str(key): int(value) for key, value in payload["element_counts"].items()
                },
                text_content=[str(item) for item in payload["text_content"]],
                colors=[str(item) for item in payload["colors"]],
                font_sizes_pt=[float(item) for item in payload["font_sizes_pt"]],
                geometry_digest=str(payload["geometry_digest"]),
                geometry_points=int(payload["geometry_points"]),
                environment={
                    str(key): str(value) for key, value in payload["environment"].items()
                },
            )
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise RegressionError(f"baseline fingerprint is malformed: {exc}") from exc


def current_environment() -> dict[str, str]:
    """Describe the rendering stack closely enough to explain layout drift."""
    try:
        matplotlib_version = version("matplotlib")
    except PackageNotFoundError:
        matplotlib_version = "unknown"
    return {
        "matplotlib": matplotlib_version,
        "python": platform.python_version(),
        "platform": f"{platform.system()}-{platform.machine()}",
    }


def _local_name(tag: object) -> str:
    if not isinstance(tag, str):
        return "unknown"
    return tag.rsplit("}", 1)[-1]


def _length_to_pt(value: str | None) -> float:
    if not value:
        return 0.0
    match = _LENGTH_PATTERN.match(value.strip())
    if match is None:
        return 0.0
    return float(match.group(1)) * _UNIT_TO_PT.get(match.group(2), 1.0)


def _quantize(value: float) -> float:
    return round(value / GEOMETRY_QUANTUM_PT) * GEOMETRY_QUANTUM_PT


def _element_counts(root: ET.Element) -> dict[str, int]:
    counts = Counter(_local_name(element.tag) for element in root.iter())
    return dict(sorted(counts.items()))


def _text_content(root: ET.Element) -> list[str]:
    values: list[str] = []
    for element in root.iter():
        if _local_name(element.tag) != "text":
            continue
        text = "".join(element.itertext()).strip()
        if text:
            values.append(text)
    return values


def _font_sizes(svg_text: str) -> list[float]:
    sizes: set[float] = set()
    for value in _FONT_SIZE_PATTERN.findall(svg_text):
        try:
            sizes.add(round(float(value), 2))
        except ValueError:
            continue
    return sorted(sizes)


def _geometry_signature(root: ET.Element) -> tuple[str, int]:
    coordinates: list[str] = []
    for element in root.iter():
        if _local_name(element.tag) != "path":
            continue
        data = element.get("d")
        if not data:
            continue
        for number in _NUMBER_PATTERN.findall(data):
            try:
                coordinates.append(f"{_quantize(float(number)):.1f}")
            except ValueError:
                continue
    joined = "|".join(coordinates).encode("utf-8")
    return hashlib.sha256(joined).hexdigest(), len(coordinates)


def build_fingerprint(svg_text: str, spec_name: str) -> FigureFingerprint:
    """Build a structural fingerprint from exported SVG markup."""
    try:
        root = ET.fromstring(svg_text)  # noqa: S314 - self-generated markup
    except ET.ParseError as exc:
        raise RegressionError(f"exported SVG could not be parsed: {exc}") from exc
    digest, points = _geometry_signature(root)
    return FigureFingerprint(
        schema_version=FINGERPRINT_SCHEMA_VERSION,
        spec_name=spec_name,
        canvas_width_pt=round(_length_to_pt(root.get("width")), 2),
        canvas_height_pt=round(_length_to_pt(root.get("height")), 2),
        element_counts=_element_counts(root),
        text_content=_text_content(root),
        colors=sorted(extract_hex_colors(svg_text)),
        font_sizes_pt=_font_sizes(svg_text),
        geometry_digest=digest,
        geometry_points=points,
        environment=current_environment(),
    )


def fingerprint_from_bundle(bundle_dir: str | Path, spec_name: str) -> FigureFingerprint:
    """Build a fingerprint from the SVG inside a rendered run bundle."""
    svg_path = Path(bundle_dir) / _SVG_NAME
    if not svg_path.is_file():
        raise RegressionError(f"run bundle has no {_SVG_NAME}: {bundle_dir}")
    return build_fingerprint(svg_path.read_text(encoding="utf-8"), spec_name)
