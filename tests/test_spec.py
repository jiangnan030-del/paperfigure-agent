# SPDX-License-Identifier: MIT
from pathlib import Path
import unittest

from paperfig.spec import SpecError, load_spec
from paperfig.spec.models import FigureSpec


class SpecTests(unittest.TestCase):
    def test_example_spec_loads(self) -> None:
        spec = load_spec(Path("examples/specs/grouped_bar.yaml"))
        self.assertEqual(spec.chart.mark, "bar")
        self.assertTrue(spec.qa.require_zero_baseline)
        self.assertEqual({"svg", "pdf", "png"}, set(spec.export.formats))

    def test_remote_data_is_rejected(self) -> None:
        raw = {
            "claim": "test",
            "venue": "nature",
            "stage": "draft",
            "backend": "matplotlib",
            "data": {"source": "https://example.com/data.csv"},
            "chart": {"family": "comparison", "mark": "bar", "x": "x", "y": "y"},
        }
        with self.assertRaisesRegex(SpecError, "local relative path"):
            FigureSpec.from_mapping(raw)


if __name__ == "__main__":
    unittest.main()
