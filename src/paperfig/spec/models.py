# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

SUPPORTED_MARKS = frozenset(
    {"bar", "line", "scatter", "heatmap", "box", "violin", "interval"}
)


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


def _optional_text(mapping: Mapping[str, Any], key: str, scope: str) -> str | None:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise SpecError(f"{scope}.{key} must be a non-empty string when provided")
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
    value: str | None = None
    lower: str | None = None
    upper: str | None = None
    size: str | None = None
    x_label: str | None = None
    y_label: str | None = None

    def required_columns(self) -> tuple[str, ...]:
        columns = {self.x, self.y}
        for optional in (
            self.series,
            self.error,
            self.value,
            self.lower,
            self.upper,
            self.size,
        ):
            if optional:
                columns.add(optional)
        return tuple(sorted(columns))


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
    def from_mapping(cls, raw: Mapping[str, Any]) -> FigureSpec:
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
            license=_optional_text(data_raw, "license", "data"),
            citation=_optional_text(data_raw, "citation", "data"),
        )

        chart_raw = _as_mapping(raw.get("chart"), "chart")
        mark = _required_text(chart_raw, "mark", "chart").lower()
        if mark not in SUPPORTED_MARKS:
            raise SpecError(
                f"unsupported chart.mark='{mark}'; choose from {', '.join(sorted(SUPPORTED_MARKS))}"
            )
        chart = ChartSpec(
            family=_required_text(chart_raw, "family", "chart").lower(),
            mark=mark,
            x=_required_text(chart_raw, "x", "chart"),
            y=_required_text(chart_raw, "y", "chart"),
            series=_optional_text(chart_raw, "series", "chart"),
            error=_optional_text(chart_raw, "error", "chart"),
            highlight=_optional_text(chart_raw, "highlight", "chart"),
            value=_optional_text(chart_raw, "value", "chart"),
            lower=_optional_text(chart_raw, "lower", "chart"),
            upper=_optional_text(chart_raw, "upper", "chart"),
            size=_optional_text(chart_raw, "size", "chart"),
            x_label=_optional_text(chart_raw, "x_label", "chart"),
            y_label=_optional_text(chart_raw, "y_label", "chart"),
        )
        if mark == "heatmap" and not chart.value:
            raise SpecError("chart.value is required for heatmap marks")
        if mark == "interval" and (not chart.lower or not chart.upper):
            raise SpecError("chart.lower and chart.upper are required for interval marks")
        if mark in {"box", "violin"} and chart.series:
            raise SpecError("box and violin marks do not yet support chart.series")
        if chart.error and mark not in {"bar", "line"}:
            raise SpecError("chart.error is supported only for bar and line marks")
        if chart.size and mark != "scatter":
            raise SpecError("chart.size is supported only for scatter marks")

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
