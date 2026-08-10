# SPDX-License-Identifier: MIT
import unittest
from pathlib import Path

from paperfig.spec import SpecError, load_spec
from paperfig.spec.models import FigureSpec


class SpecTests(unittest.TestCase):
    def test_example_spec_loads(self) -> None:
        spec = load_spec(Path("examples/specs/grouped_bar.yaml"))
        self.assertEqual(spec.chart.mark, "bar")
        self.assertTrue(spec.qa.require_zero_baseline)
        self.assertEqual({"svg", "pdf", "png"}, set(spec.export.formats))

    def test_all_supported_example_marks_load(self) -> None:
        expected = {"bar", "line", "scatter", "heatmap", "box", "violin", "interval"}
        actual = {
            load_spec(path).chart.mark
            for path in Path("examples/specs").glob("*.yaml")
        }
        self.assertEqual(expected, actual)

    def test_remote_data_is_rejected(self) -> None:
        raw = self._base_mapping("bar")
        raw["data"] = {"source": "https://example.com/data.csv"}
        with self.assertRaisesRegex(SpecError, "local relative path"):
            FigureSpec.from_mapping(raw)

    def test_heatmap_requires_value_column(self) -> None:
        raw = self._base_mapping("heatmap")
        with self.assertRaisesRegex(SpecError, "chart.value"):
            FigureSpec.from_mapping(raw)

    def test_interval_requires_bounds(self) -> None:
        raw = self._base_mapping("interval")
        with self.assertRaisesRegex(SpecError, "chart.lower and chart.upper"):
            FigureSpec.from_mapping(raw)

    @staticmethod
    def _base_mapping(mark: str) -> dict[str, object]:
        return {
            "claim": "test",
            "venue": "nature-machine-intelligence",
            "stage": "draft",
            "backend": "matplotlib",
            "data": {"source": "data.csv"},
            "chart": {
                "family": "test",
                "mark": mark,
                "x": "x",
                "y": "y",
            },
        }


if __name__ == "__main__":
    unittest.main()
