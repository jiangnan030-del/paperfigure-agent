# SPDX-License-Identifier: MIT
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


class DataError(ValueError):
    """Raised when local figure data is malformed."""


def _coerce(value: str) -> Any:
    stripped = value.strip()
    if stripped == "":
        return None
    try:
        return int(stripped)
    except ValueError:
        try:
            return float(stripped)
        except ValueError:
            return stripped


def load_csv_records(path: str | Path, required_columns: set[str]) -> list[dict[str, Any]]:
    source = Path(path).resolve()
    if not source.is_file():
        raise DataError(f"data file does not exist: {source}")
    if source.suffix.lower() != ".csv":
        raise DataError("MVP accepts CSV data only")

    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = sorted(required_columns - fields)
        if missing:
            raise DataError(f"missing required columns: {', '.join(missing)}")
        records = [{key: _coerce(value or "") for key, value in row.items()} for row in reader]

    if not records:
        raise DataError("data file contains no records")
    return records
