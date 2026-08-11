# SPDX-License-Identifier: MIT
import tempfile
import unittest
from pathlib import Path

from paperfig.harness import render_spec
from paperfig.review import review_bundle
from paperfig.review.colormap import review_sequential_colormap

HEATMAP_SPEC = "examples/specs/heatmap.yaml"


class ColormapReviewTests(unittest.TestCase):
    def test_viridis_passes_the_perceptual_checks(self) -> None:
        self.assertEqual([], review_sequential_colormap("viridis", hard_gate=True))

    def test_jet_has_a_lightness_reversal(self) -> None:
        rules = {
            finding.rule_id: finding.severity
            for finding in review_sequential_colormap("jet", hard_gate=True)
        }
        self.assertEqual("error", rules["COLORMAP_LIGHTNESS_REVERSAL"])

    def test_unknown_colormap_is_an_error(self) -> None:
        findings = review_sequential_colormap("not-a-colormap", hard_gate=True)
        self.assertEqual(["COLORMAP_NOT_REVIEWABLE"], [item.rule_id for item in findings])
        self.assertEqual("error", findings[0].severity)

    def test_heatmap_bundle_no_longer_has_the_placeholder_finding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_spec(HEATMAP_SPEC, output)
            findings = review_bundle(output)
            rules = {finding.rule_id for finding in findings}
            self.assertNotIn("SEQUENTIAL_COLORMAP_NOT_REVIEWED", rules)
            self.assertFalse(any(finding.severity == "error" for finding in findings))


if __name__ == "__main__":
    unittest.main()
