# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from matplotlib.axes import Axes

from paperfig.plots.common import finish_cartesian_axes, ordered_unique
from paperfig.spec.models import ChartSpec


def _marker_sizes(records: list[dict[str, Any]], column: str | None) -> list[float]:
    if column is None:
        return [24.0] * len(records)
    raw = [float(row[column]) for row in records]
    low, high = min(raw), max(raw)
    if high == low:
        return [36.0] * len(raw)
    return [20.0 + 80.0 * (value - low) / (high - low) for value in raw]


def draw_scatter(
    ax: Axes,
    records: list[dict[str, Any]],
    chart: ChartSpec,
    palette: Sequence[str],
    highlight_color: str,
) -> None:
    series_values = (
        ordered_unique([row[chart.series] for row in records])
        if chart.series
        else [None]
    )
    for index, series_value in enumerate(series_values):
        rows = [
            row
            for row in records
            if (row[chart.series] if chart.series else None) == series_value
        ]
        color = (
            highlight_color
            if str(series_value) == chart.highlight
            else palette[index % len(palette)]
        )
        ax.scatter(
            [float(row[chart.x]) for row in rows],
            [float(row[chart.y]) for row in rows],
            s=_marker_sizes(rows, chart.size),
            color=color,
            edgecolor="white",
            linewidth=0.5,
            alpha=0.88,
            label=str(series_value) if series_value is not None else None,
            zorder=3,
        )
    ax.set_xlabel(chart.x_label or chart.x.replace("_", " ").title())
    ax.set_ylabel(chart.y_label or chart.y.replace("_", " ").title())
    finish_cartesian_axes(ax)
    if chart.series:
        ax.legend(frameon=False, ncols=min(len(series_values), 3))
