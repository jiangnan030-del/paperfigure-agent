# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from matplotlib.axes import Axes

from paperfig.plots.common import finish_cartesian_axes
from paperfig.spec.models import ChartSpec


def draw_interval(
    ax: Axes,
    records: list[dict[str, Any]],
    chart: ChartSpec,
    palette: Sequence[str],
    highlight_color: str,
) -> None:
    if chart.lower is None or chart.upper is None:
        raise ValueError("interval requires chart.lower and chart.upper")
    positions = np.arange(len(records))[::-1]
    pairs = zip(positions, records, strict=True)
    for index, (position, row) in enumerate(pairs):
        estimate = float(row[chart.y])
        lower = float(row[chart.lower])
        upper = float(row[chart.upper])
        label = str(row[chart.x])
        color = highlight_color if label == chart.highlight else palette[index % len(palette)]
        ax.errorbar(
            [estimate],
            [position],
            xerr=np.array([[estimate - lower], [upper - estimate]]),
            fmt="o",
            color=color,
            markersize=4.5,
            capsize=2.5,
            linewidth=1.2,
            zorder=3,
        )
    ax.set_yticks(positions, [str(row[chart.x]) for row in records])
    ax.set_xlabel(chart.y_label or chart.y.replace("_", " ").title())
    ax.set_ylabel(chart.x_label or "")
    finish_cartesian_axes(ax, grid_axis="x")
