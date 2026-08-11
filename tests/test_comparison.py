# SPDX-License-Identifier: MIT
import tempfile
import unittest
from pathlib import Path

import yaml

from paperfig.comparison import compare_bundles, write_comparison
from paperfig.harness import render_spec

SPEC = "examples/specs/grouped_bar.yaml"


class BundleComparisonTests(unittest.TestCase):
    def test_two_equivalent_renders_have_no_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline"
            candidate = root / "candidate"
            render_spec(SPEC, baseline)
            render_spec(SPEC, candidate)
            comparison = compare_bundles(baseline, candidate)
            self.assertEqual([], comparison.findings)
            json_path, markdown_path = write_comparison(root / "report", comparison)
            self.assertTrue(json_path.is_file())
            self.assertIn("equivalent", markdown_path.read_text(encoding="utf-8"))

    def test_changed_data_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline"
            candidate = root / "candidate"
            render_spec(SPEC, baseline)
            render_spec(SPEC, candidate)
            with (candidate / "figure.data.csv").open("a", encoding="utf-8") as handle:
                handle.write("Unexpected,A,0.1,0.1\n")
            comparison = compare_bundles(baseline, candidate)
            errors = {
                finding.rule_id
                for finding in comparison.findings
                if finding.severity == "error"
            }
            self.assertIn("COMPARISON_DATA_CHANGED", errors)
            self.assertIn("COMPARISON_REVIEW_REGRESSION", errors)

    def test_semantic_spec_change_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline"
            candidate = root / "candidate"
            render_spec(SPEC, baseline)
            render_spec(SPEC, candidate)
            spec_path = candidate / "figure.spec.yaml"
            payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
            payload["claim"] = "A different scientific claim."
            spec_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
            comparison = compare_bundles(baseline, candidate)
            rules = {finding.rule_id for finding in comparison.findings}
            self.assertIn("COMPARISON_SPEC_SEMANTICS_CHANGED", rules)


if __name__ == "__main__":
    unittest.main()
