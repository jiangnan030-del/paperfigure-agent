# SPDX-License-Identifier: MIT
import unittest

from paperfig.data import DataError, validate_records
from paperfig.spec.models import FigureSpec


class DataValidationTests(unittest.TestCase):
    def test_duplicate_bar_coordinate_is_rejected(self) -> None:
        spec = FigureSpec.from_mapping(self._mapping("bar"))
        records = [
            {"x": "A", "y": 1.0},
            {"x": "A", "y": 2.0},
        ]
        with self.assertRaisesRegex(DataError, "duplicate bar coordinate"):
            validate_records(spec, records)

    def test_negative_error_is_rejected(self) -> None:
        raw = self._mapping("bar")
        raw["chart"]["error"] = "std"  # type: ignore[index]
        spec = FigureSpec.from_mapping(raw)
        with self.assertRaisesRegex(DataError, "non-negative"):
            validate_records(spec, [{"x": "A", "y": 1.0, "std": -0.1}])

    def test_invalid_interval_order_is_rejected(self) -> None:
        raw = self._mapping("interval")
        raw["chart"].update({"lower": "low", "upper": "high"})  # type: ignore[union-attr]
        spec = FigureSpec.from_mapping(raw)
        with self.assertRaisesRegex(DataError, "lower <= estimate <= upper"):
            validate_records(spec, [{"x": "A", "y": 1.0, "low": 1.2, "high": 1.4}])

    def test_non_finite_numeric_value_is_rejected(self) -> None:
        spec = FigureSpec.from_mapping(self._mapping("scatter"))
        with self.assertRaisesRegex(DataError, "finite"):
            validate_records(spec, [{"x": 1.0, "y": float("nan")}])

    @staticmethod
    def _mapping(mark: str) -> dict[str, object]:
        return {
            "claim": "test",
            "venue": "nature-machine-intelligence",
            "stage": "draft",
            "backend": "matplotlib",
            "data": {"source": "data.csv"},
            "chart": {"family": "test", "mark": mark, "x": "x", "y": "y"},
        }


if __name__ == "__main__":
    unittest.main()
