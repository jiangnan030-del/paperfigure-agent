# SPDX-License-Identifier: MIT
from __future__ import annotations

from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from paperfig.plots import draw_grouped_bar
from paperfig.spec.models import FigureSpec


def render_figure(
    spec: FigureSpec, records: list[dict[str, Any]], profile: dict[str, Any]
) -> Figure:
    width = float(profile["widths_in"].get(spec.layout.width, profile["widths_in"]["single_column"]))
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
        draw_grouped_bar(
            ax=ax,
            records=records,
            chart=spec.chart,
            palette=profile["palette"],
            highlight_color=profile["highlight_color"],
        )
        if spec.qa.require_zero_baseline:
            current_top = ax.get_ylim()[1]
            ax.set_ylim(bottom=0, top=current_top)
        # Publication profiles generally place the scientific claim in the caption,
        # not as a title embedded in the artwork. The claim remains in the spec,
        # alt text, audit, and provenance record.
        return figure
