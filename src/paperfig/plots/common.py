# SPDX-License-Identifier: MIT
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from matplotlib.axes import Axes


def ordered_unique(values: Sequence[Any]) -> list[Any]:
    return list(dict.fromkeys(values))


def finish_cartesian_axes(ax: Axes, *, grid_axis: str = "y") -> None:
    ax.grid(axis=grid_axis, color="#D9D9D9", linewidth=0.6, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
