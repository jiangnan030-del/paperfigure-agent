# SPDX-License-Identifier: MIT
from __future__ import annotations

import math
from numbers import Real
from typing import Any

from paperfig.data.loaders import DataError
from paperfig.spec.models import FigureSpec


def _number(value: Any, column: str, row_number: int) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise DataError(f"row {row_number}: column '{column}' must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise DataError(f"row {row_number}: column '{column}' must be finite")
    return result


def _reject_duplicate_keys(
    records: list[dict[str, Any]], columns: tuple[str, ...], mark: str
) -> None:
    seen: dict[tuple[Any, ...], int] = {}
    for row_number, row in enumerate(records, start=2):
        key = tuple(row[column] for column in columns)
        if key in seen:
            pairs = zip(columns, key, strict=True)
            rendered = ", ".join(
                f"{column}={value!r}" for column, value in pairs
            )
            raise DataError(
                f"duplicate {mark} coordinate at rows {seen[key]} and {row_number}: {rendered}"
            )
        seen[key] = row_number


def validate_records(spec: FigureSpec, records: list[dict[str, Any]]) -> None:
    chart = spec.chart
    required = chart.required_columns()
    numeric_columns = {chart.y}
    if chart.mark == "heatmap":
        numeric_columns = {chart.value} if chart.value else set()
    elif chart.mark == "scatter":
        numeric_columns.add(chart.x)
    for optional in (chart.error, chart.lower, chart.upper, chart.size):
        if optional:
            numeric_columns.add(optional)

    for row_number, row in enumerate(records, start=2):
        for column in required:
            if column not in row or row[column] is None:
                raise DataError(f"row {row_number}: required column '{column}' is missing or empty")
        for column in numeric_columns:
            _number(row[column], column, row_number)
        if chart.error and _number(row[chart.error], chart.error, row_number) < 0:
            raise DataError(f"row {row_number}: error values must be non-negative")
        if chart.size and _number(row[chart.size], chart.size, row_number) < 0:
            raise DataError(f"row {row_number}: size values must be non-negative")
        if chart.mark == "interval":
            estimate = _number(row[chart.y], chart.y, row_number)
            lower = _number(row[chart.lower], chart.lower, row_number)  # type: ignore[index]
            upper = _number(row[chart.upper], chart.upper, row_number)  # type: ignore[index]
            if lower > estimate or estimate > upper:
                raise DataError(
                    f"row {row_number}: interval must satisfy lower <= estimate <= upper"
                )

    key_columns: tuple[str, ...] | None = None
    if chart.mark in {"bar", "line"}:
        key_columns = (chart.x,) + ((chart.series,) if chart.series else ())
    elif chart.mark == "heatmap":
        key_columns = (chart.x, chart.y)
    elif chart.mark == "interval":
        key_columns = (chart.x,) + ((chart.series,) if chart.series else ())
    if key_columns:
        _reject_duplicate_keys(records, key_columns, chart.mark)
