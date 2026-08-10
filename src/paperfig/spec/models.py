# SPDX-License-Identifier: MIT
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

import yaml


class SpecError(ValueError):
    """Raised when a FigureSpec is invalid or unsafe."""


def _as_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SpecError(f"{name} must be a mapping")
    return value


def _required_text(mapping: Mapping[str, Any], key: str, scope: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SpecError(f"{scope}.{key} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class DataSpec:
    source: str
    license: str | None = None
    citation: str | None = None


@dataclass(frozen=True)
class ChartSpec:
    family: str
    mark: str
    x: str
    y: str
    series: str | None = None
    error: str | None = None
    highlight: str | None = None
    y_label: str | None = None


@dataclass(frozen=True)
class LayoutSpec:
    width: str = "single_column"
    panels: int = 1
    aspect_ratio: float = 0.68


@dataclass(frozen=True)
class QASpec:
    require_zero_baseline: bool = True
    color_vision_gate: bool = True
    require_alt_text: bool = True


@dataclass(frozen=True)
class ExportSpec:
    formats: tuple[str, ...] = ("svg", "pdf", "png")
    dpi: int = 300


@dataclass(frozen=True)
class FigureSpec:
    claim: str
    venue: str
    stage: str
    backend: str
    data: DataSpec
    chart: ChartSpec
    layout: LayoutSpec = field(default_factory=LayoutSpec)
    qa: QASpec = field(default_factory=QASpec)
    export: ExportSpec = field(default_factory=ExportSpec)
    references: tuple[Mapping[str, Any], ...] = ()
    seed: int = 0

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "FigureSpec":
        claim = _required_text(raw, "claim", "spec")
        venue = _required_text(raw, "venue", "spec").lower()
        stage = _required_text(raw, "stage", "spec").lower()
        backend = _required_text(raw, "backend", "spec").lower()
        if backend != "matplotlib":
            raise SpecError("MVP backend must be 'matplotlib'")

        data_raw = _as_mapping(raw.get("data"), "data")
        source = _required_text(data_raw, "source", "data")
        parsed = urlparse(source)
        if parsed.scheme or parsed.netloc:
            raise SpecError("MVP data.source must be a local relative path, not a URL")
        data = DataSpec(
            source=source,
            license=data_raw.get("license"),
            citation=data_raw.get("citation"),
        )

        chart_raw = _as_mapping(raw.get("chart"), "chart")
        chart = ChartSpec(
            family=_required_text(chart_raw, "family", "chart").lower(),
            mark=_required_text(chart_raw, "mark", "chart").lower(),
            x=_required_text(chart_raw, "x", "chart"),
            y=_required_text(chart_raw, "y", "chart"),
            series=chart_raw.get("series"),
            error=chart_raw.get("error"),
            highlight=chart_raw.get("highlight"),
            y_label=chart_raw.get("y_label"),
        )
        if chart.mark != "bar":
            raise SpecError("MVP currently implements chart.mark='bar' only")

        layout_raw = _as_mapping(raw.get("layout", {}), "layout")
        layout = LayoutSpec(
            width=str(layout_raw.get("width", "single_column")),
            panels=int(layout_raw.get("panels", 1)),
            aspect_ratio=float(layout_raw.get("aspect_ratio", 0.68)),
        )
        if layout.panels != 1:
            raise SpecError("MVP currently supports one panel per FigureSpec")
        if not 0.3 <= layout.aspect_ratio <= 2.0:
            raise SpecError("layout.aspect_ratio must be between 0.3 and 2.0")

        qa_raw = _as_mapping(raw.get("qa", {}), "qa")
        qa = QASpec(
            require_zero_baseline=bool(qa_raw.get("require_zero_baseline", True)),
            color_vision_gate=bool(qa_raw.get("color_vision_gate", True)),
            require_alt_text=bool(qa_raw.get("require_alt_text", True)),
        )

        export_raw = _as_mapping(raw.get("export", {}), "export")
        formats_value = export_raw.get("formats", ["svg", "pdf", "png"])
        if not isinstance(formats_value, list) or not formats_value:
            raise SpecError("export.formats must be a non-empty list")
        formats = tuple(str(item).lower() for item in formats_value)
        allowed_formats = {"svg", "pdf", "png", "tiff"}
        unsupported = sorted(set(formats) - allowed_formats)
        if unsupported:
            raise SpecError(f"unsupported export formats: {', '.join(unsupported)}")
        dpi = int(export_raw.get("dpi", 300))
        if not 72 <= dpi <= 1200:
            raise SpecError("export.dpi must be between 72 and 1200")
        export = ExportSpec(formats=formats, dpi=dpi)

        references_value = raw.get("references", [])
        if not isinstance(references_value, list):
            raise SpecError("references must be a list")
        references = tuple(_as_mapping(item, "reference") for item in references_value)

        return cls(
            claim=claim,
            venue=venue,
            stage=stage,
            backend=backend,
            data=data,
            chart=chart,
            layout=layout,
            qa=qa,
            export=export,
            references=references,
            seed=int(raw.get("seed", 0)),
        )


def load_spec(path: str | Path) -> FigureSpec:
    spec_path = Path(path)
    raw = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    return FigureSpec.from_mapping(_as_mapping(raw, "spec"))
