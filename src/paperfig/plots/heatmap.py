# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from matplotlib.axes import Axes

from paperfig.plots.common import ordered_unique
from paperfig.spec.models import ChartSpec


def draw_heatmap(
    ax: Axes,
    records: list[dict[str, Any]],
    chart: ChartSpec,
    palette: Sequence[str],
    highlight_color: str,
) -> None:
    del palette, highlight_color
    if chart.value is None:
        raise ValueError("heatmap requires chart.value")
    x_values = ordered_unique([row[chart.x] for row in records])
    y_values = ordered_unique([row[chart.y] for row in records])
    matrix = np.full((len(y_values), len(x_values)), np.nan, dtype=float)
    x_index = {value: index for index, value in enumerate(x_values)}
    y_index = {value: index for index, value in enumerate(y_values)}
    for row in records:
        matrix[y_index[row[chart.y]], x_index[row[chart.x]]] = float(row[chart.value])

    image = ax.imshow(matrix, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(x_values)), [str(value) for value in x_values])
    ax.set_yticks(range(len(y_values)), [str(value) for value in y_values])
    ax.set_xlabel(chart.x_label or chart.x.replace("_", " ").title())
    ax.set_ylabel(chart.y_label or chart.y.replace("_", " ").title())
    colorbar = ax.figure.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    colorbar.set_label(chart.value.replace("_", " ").title())

    finite = matrix[np.isfinite(matrix)]
    midpoint = float(np.nanmin(finite) + np.nanmax(finite)) / 2 if finite.size else 0.0
    for y_pos in range(matrix.shape[0]):
        for x_pos in range(matrix.shape[1]):
            value = matrix[y_pos, x_pos]
            if np.isfinite(value):
                ax.text(
                    x_pos,
                    y_pos,
                    f"{value:g}",
                    ha="center",
                    va="center",
                    color="white" if value < midpoint else "black",
                    fontsize="small",
                )
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
