# SPDX-License-Identifier: MIT
from __future__ import annotations

from pathlib import Path

from matplotlib.figure import Figure


def export_figure(
    figure: Figure,
    output_dir: str | Path,
    formats: tuple[str, ...],
    dpi: int,
) -> list[Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for file_format in formats:
        suffix = "tiff" if file_format == "tiff" else file_format
        output = destination / f"figure.{suffix}"
        save_dpi = dpi if file_format in {"png", "tiff"} else None
        figure.savefig(output, format=file_format, dpi=save_dpi, bbox_inches="tight")
        outputs.append(output)
    return outputs
