# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from matplotlib.axes import Axes

from paperfig.spec.models import ChartSpec


def _ordered_unique(values: Sequence[Any]) -> list[Any]:
    return list(dict.fromkeys(values))


def draw_grouped_bar(
    ax: Axes,
    records: list[dict[str, Any]],
    chart: ChartSpec,
    palette: Sequence[str],
    highlight_color: str,
) -> None:
    x_values = _ordered_unique([row[chart.x] for row in records])
    series_values = (
        _ordered_unique([row[chart.series] for row in records]) if chart.series else [None]
    )
    positions = np.arange(len(x_values), dtype=float)
    width = 0.8 / max(len(series_values), 1)

    lookup: Mapping[tuple[Any, Any], dict[str, Any]] = {
        (row[chart.x], row[chart.series] if chart.series else None): row for row in records
    }

    for index, series_value in enumerate(series_values):
        values: list[float] = []
        errors: list[float] | None = [] if chart.error else None
        colors: list[str] = []
        for x_value in x_values:
            row = lookup.get((x_value, series_value))
            if row is None:
                values.append(float("nan"))
                if errors is not None:
                    errors.append(float("nan"))
            else:
                values.append(float(row[chart.y]))
                if errors is not None:
                    errors.append(float(row[chart.error]))

            is_highlight = chart.highlight in {str(series_value), str(x_value)}
            colors.append(highlight_color if is_highlight else palette[index % len(palette)])

        offset = (index - (len(series_values) - 1) / 2) * width
        ax.bar(
            positions + offset,
            values,
            width=width * 0.92,
            yerr=errors,
            capsize=2.0 if errors is not None else 0.0,
            color=colors,
            edgecolor="white",
            linewidth=0.5,
            label=str(series_value) if series_value is not None else None,
            zorder=3,
        )

    ax.set_xticks(positions, [str(value) for value in x_values])
    ax.set_ylabel(chart.y_label or chart.y.replace("_", " ").title())
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.6, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    if chart.series:
        ax.legend(frameon=False, ncols=min(len(series_values), 3))
