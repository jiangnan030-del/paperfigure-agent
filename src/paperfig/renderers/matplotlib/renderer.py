# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Any

import matplotlib
from matplotlib.figure import Figure

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from paperfig.plots import (
    draw_distribution,
    draw_grouped_bar,
    draw_heatmap,
    draw_interval,
    draw_line,
    draw_scatter,
)
from paperfig.spec.models import FigureSpec


def render_figure(
    spec: FigureSpec, records: list[dict[str, Any]], profile: dict[str, Any]
) -> Figure:
    width = float(
        profile["widths_in"].get(spec.layout.width, profile["widths_in"]["single_column"])
    )
    height = width * spec.layout.aspect_ratio
    rc = {
        "font.family": profile.get("font_family", "DejaVu Sans"),
        "font.size": float(profile.get("base_font_size", 8.0)),
        "axes.linewidth": float(profile.get("line_width", 0.8)),
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
    with plt.rc_context(rc):
        figure, ax = plt.subplots(figsize=(width, height), constrained_layout=True)
        common = {
            "ax": ax,
            "records": records,
            "chart": spec.chart,
            "palette": profile["palette"],
            "highlight_color": profile["highlight_color"],
        }
        if spec.chart.mark == "bar":
            draw_grouped_bar(**common)
        elif spec.chart.mark == "line":
            draw_line(**common)
        elif spec.chart.mark == "scatter":
            draw_scatter(**common)
        elif spec.chart.mark == "heatmap":
            draw_heatmap(**common)
        elif spec.chart.mark in {"box", "violin"}:
            draw_distribution(**common)
        elif spec.chart.mark == "interval":
            draw_interval(**common)
        else:  # guarded by FigureSpec validation
            raise ValueError(f"unsupported chart mark: {spec.chart.mark}")

        if spec.chart.mark == "bar" and spec.qa.require_zero_baseline:
            current_top = ax.get_ylim()[1]
            ax.set_ylim(bottom=0, top=current_top)
        # Publication profiles place the scientific claim in the caption rather
        # than embedding it as an artwork title. The claim remains in the spec,
        # alt text, audit, and provenance record.
        return figure


def close_figure(figure: Figure) -> None:
    plt.close(figure)
