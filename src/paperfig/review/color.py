# SPDX-License-Identifier: MIT
"""Deterministic colour math used by Reviewer Mode.

This module is an independent implementation of published colour-science
methods. No third-party source code was copied.

Method references:

- sRGB transfer function and primaries: IEC 61966-2-1.
- CIE L*a*b* conversion against the D65 white point: CIE 15:2004.
- Dichromat simulation matrices applied in linear RGB: Vienot, Brettel and
  Mollon (1999), "Digital video colourmaps for checking the legibility of
  displays by dichromats", Color Research & Application 24(4), 243-252.
- Relative luminance and contrast ratio: WCAG 2.1 sections 1.4.3 and 1.4.11.

The simulation is a linear approximation. It models dichromacy only and does
not describe anomalous trichromacy or individual adaptation.
"""
from __future__ import annotations

import math
import re

Rgb = tuple[float, float, float]
Lab = tuple[float, float, float]

WHITE: Rgb = (1.0, 1.0, 1.0)

_HEX_PATTERN = re.compile(r"#([0-9a-fA-F]{6})")

_WHITE_POINT_D65 = (0.95047, 1.0, 1.08883)

_CVD_MATRICES: dict[str, tuple[Rgb, Rgb, Rgb]] = {
    "deuteranopia": ((0.625, 0.375, 0.0), (0.700, 0.300, 0.0), (0.0, 0.300, 0.700)),
    "protanopia": ((0.567, 0.433, 0.0), (0.558, 0.442, 0.0), (0.0, 0.242, 0.758)),
    "tritanopia": ((0.950, 0.050, 0.0), (0.0, 0.433, 0.567), (0.0, 0.475, 0.525)),
}

CVD_TYPES: tuple[str, ...] = tuple(sorted(_CVD_MATRICES))


def parse_hex(value: str) -> Rgb:
    """Parse a ``#rrggbb`` string into sRGB channels in the 0..1 range."""
    text = value.strip().lstrip("#")
    if _HEX_PATTERN.fullmatch(f"#{text}") is None:
        raise ValueError(f"expected a #rrggbb colour, received {value!r}")
    return (
        int(text[0:2], 16) / 255.0,
        int(text[2:4], 16) / 255.0,
        int(text[4:6], 16) / 255.0,
    )


def extract_hex_colors(text: str) -> list[str]:
    """Return lowercase ``#rrggbb`` colours in first-seen order."""
    ordered: dict[str, None] = {}
    for match in _HEX_PATTERN.finditer(text):
        ordered.setdefault(f"#{match.group(1).lower()}", None)
    return list(ordered)


def _to_linear(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def linearize(color: Rgb) -> Rgb:
    return (_to_linear(color[0]), _to_linear(color[1]), _to_linear(color[2]))


def relative_luminance(color: Rgb) -> float:
    red, green, blue = linearize(color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(first: Rgb, second: Rgb) -> float:
    left = relative_luminance(first)
    right = relative_luminance(second)
    lighter = max(left, right)
    darker = min(left, right)
    return (lighter + 0.05) / (darker + 0.05)


def simulate_dichromacy(color: Rgb, cvd_type: str) -> Rgb:
    """Project an sRGB colour onto a dichromat gamut, returned as linear RGB."""
    matrix = _CVD_MATRICES.get(cvd_type)
    if matrix is None:
        raise ValueError(f"unknown dichromacy type: {cvd_type!r}")
    linear = linearize(color)
    projected: list[float] = []
    for row in matrix:
        total = sum(weight * channel for weight, channel in zip(row, linear, strict=True))
        projected.append(min(1.0, max(0.0, total)))
    return (projected[0], projected[1], projected[2])


def _pivot(value: float) -> float:
    if value > 0.008856:
        return value ** (1.0 / 3.0)
    return (903.3 * value + 16.0) / 116.0


def lab_from_linear(linear: Rgb) -> Lab:
    red, green, blue = linear
    x = 0.4124 * red + 0.3576 * green + 0.1805 * blue
    y = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    z = 0.0193 * red + 0.1192 * green + 0.9505 * blue
    fx = _pivot(max(0.0, x) / _WHITE_POINT_D65[0])
    fy = _pivot(max(0.0, y) / _WHITE_POINT_D65[1])
    fz = _pivot(max(0.0, z) / _WHITE_POINT_D65[2])
    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


def lab(color: Rgb) -> Lab:
    return lab_from_linear(linearize(color))


def delta_e76(first: Lab, second: Lab) -> float:
    total = sum((left - right) ** 2 for left, right in zip(first, second, strict=True))
    return math.sqrt(total)


def chroma(color: Rgb) -> float:
    _, a_star, b_star = lab(color)
    return math.hypot(a_star, b_star)


def dichromat_delta_e(first: Rgb, second: Rgb, cvd_type: str) -> float:
    return delta_e76(
        lab_from_linear(simulate_dichromacy(first, cvd_type)),
        lab_from_linear(simulate_dichromacy(second, cvd_type)),
    )


def worst_dichromat_delta_e(first: Rgb, second: Rgb) -> tuple[str, float]:
    """Return the dichromacy type that separates two colours the least."""
    scored = [(name, dichromat_delta_e(first, second, name)) for name in CVD_TYPES]
    return min(scored, key=lambda item: item[1])
