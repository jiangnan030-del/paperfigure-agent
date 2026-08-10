# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from matplotlib.axes import Axes

from paperfig.plots.common import finish_cartesian_axes, ordered_unique
from paperfig.spec.models import ChartSpec


def _sort_rows(rows: list[dict[str, Any]], x_column: str) -> list[dict[str, Any]]:
    values = [row[x_column] for row in rows]
    if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
        return sorted(rows, key=lambda row: float(row[x_column]))
    return sorted(rows, key=lambda row: str(row[x_column]))


def draw_line(
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
        rows = _sort_rows(rows, chart.x)
        x_values = [row[chart.x] for row in rows]
        y_values = [float(row[chart.y]) for row in rows]
        errors = [float(row[chart.error]) for row in rows] if chart.error else None
        color = (
            highlight_color
            if str(series_value) == chart.highlight
            else palette[index % len(palette)]
        )
        ax.errorbar(
            x_values,
            y_values,
            yerr=errors,
            color=color,
            marker="o",
            markersize=3.5,
            linewidth=1.2,
            capsize=2.0 if errors is not None else 0.0,
            label=str(series_value) if series_value is not None else None,
            zorder=3,
        )
    ax.set_xlabel(chart.x_label or chart.x.replace("_", " ").title())
    ax.set_ylabel(chart.y_label or chart.y.replace("_", " ").title())
    finish_cartesian_axes(ax)
    if chart.series:
        ax.legend(frameon=False, ncols=min(len(series_values), 3))
