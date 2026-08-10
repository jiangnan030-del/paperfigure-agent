# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from matplotlib.axes import Axes

from paperfig.plots.common import finish_cartesian_axes, ordered_unique
from paperfig.spec.models import ChartSpec


def draw_distribution(
    ax: Axes,
    records: list[dict[str, Any]],
    chart: ChartSpec,
    palette: Sequence[str],
    highlight_color: str,
) -> None:
    categories = ordered_unique([row[chart.x] for row in records])
    groups = [
        [float(row[chart.y]) for row in records if row[chart.x] == category]
        for category in categories
    ]

    if chart.mark == "box":
        artists = ax.boxplot(
            groups,
            patch_artist=True,
            showfliers=True,
            widths=0.62,
        )
        ax.set_xticks(
            range(1, len(categories) + 1),
            [str(category) for category in categories],
        )
        for index, patch in enumerate(artists["boxes"]):
            category = str(categories[index])
            color = (
                highlight_color
                if category == chart.highlight
                else palette[index % len(palette)]
            )
            patch.set_facecolor(color)
            patch.set_alpha(0.85)
    elif chart.mark == "violin":
        artists = ax.violinplot(groups, showmeans=False, showmedians=True, showextrema=True)
        for index, body in enumerate(artists["bodies"]):
            category = str(categories[index])
            color = (
                highlight_color
                if category == chart.highlight
                else palette[index % len(palette)]
            )
            body.set_facecolor(color)
            body.set_edgecolor("white")
            body.set_alpha(0.85)
        ax.set_xticks(range(1, len(categories) + 1), [str(category) for category in categories])
    else:
        raise ValueError(f"unsupported distribution mark: {chart.mark}")

    ax.set_xlabel(chart.x_label or chart.x.replace("_", " ").title())
    ax.set_ylabel(chart.y_label or chart.y.replace("_", " ").title())
    finish_cartesian_axes(ax)
