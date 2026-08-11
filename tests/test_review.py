# SPDX-License-Identifier: MIT
import json
import tempfile
import unittest
from pathlib import Path

from paperfig.harness import render_spec
from paperfig.review import ReviewFinding, exceeds_threshold, review_bundle, write_review
from paperfig.review.color import (
    CVD_TYPES,
    contrast_ratio,
    delta_e76,
    dichromat_delta_e,
    extract_hex_colors,
    lab,
    parse_hex,
    relative_luminance,
)

SPEC = "examples/specs/grouped_bar.yaml"


class ColorMathTests(unittest.TestCase):
    def test_luminance_endpoints_are_exact(self) -> None:
        self.assertAlmostEqual(0.0, relative_luminance(parse_hex("#000000")), places=9)
        self.assertAlmostEqual(1.0, relative_luminance(parse_hex("#ffffff")), places=9)

    def test_black_on_white_contrast_is_twenty_one(self) -> None:
        ratio = contrast_ratio(parse_hex("#000000"), parse_hex("#ffffff"))
        self.assertAlmostEqual(21.0, ratio, places=6)

    def test_identical_colors_never_separate_under_simulation(self) -> None:
        blue = parse_hex("#0072b2")
        for cvd_type in CVD_TYPES:
            with self.subTest(cvd_type=cvd_type):
                self.assertAlmostEqual(0.0, dichromat_delta_e(blue, blue, cvd_type), places=9)

    def test_deuteranopia_reduces_red_green_separation(self) -> None:
        red = parse_hex("#d62728")
        green = parse_hex("#2ca02c")
        normal = delta_e76(lab(red), lab(green))
        simulated = dichromat_delta_e(red, green, "deuteranopia")
        self.assertGreater(normal, simulated)

    def test_parse_hex_rejects_malformed_input(self) -> None:
        with self.assertRaises(ValueError):
            parse_hex("#12345")

    def test_extract_hex_colors_deduplicates_in_order(self) -> None:
        found = extract_hex_colors("fill:#0072B2; stroke:#0072b2; fill:#E69F00")
        self.assertEqual(["#0072b2", "#e69f00"], found)


class ThresholdTests(unittest.TestCase):
    @staticmethod
    def _finding(severity: str) -> ReviewFinding:
        return ReviewFinding(rule_id="X", severity=severity, message="m", evidence="e")

    def test_warnings_do_not_trip_the_default_threshold(self) -> None:
        findings = [self._finding("warning"), self._finding("info")]
        self.assertFalse(exceeds_threshold(findings, "error"))
        self.assertTrue(exceeds_threshold(findings, "warning"))
        self.assertFalse(exceeds_threshold(findings, "never"))

    def test_errors_trip_the_default_threshold(self) -> None:
        self.assertTrue(exceeds_threshold([self._finding("error")], "error"))


class BundleReviewTests(unittest.TestCase):
    def test_clean_bundle_has_no_error_findings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_spec(SPEC, output)
            findings = review_bundle(output)
            errors = [item.rule_id for item in findings if item.severity == "error"]
            self.assertEqual([], errors)
            self.assertIn(
                "LOW_CONTRAST_AGAINST_BACKGROUND",
                {item.rule_id for item in findings},
            )

    def test_review_reports_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_spec(SPEC, output)
            findings = review_bundle(output)
            json_path, markdown_path = write_review(output, findings)
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual("passed", payload["status"])
            self.assertEqual(1, payload["schema_version"])
            self.assertTrue(payload["human_review_required"])
            self.assertEqual(len(findings), len(payload["findings"]))
            self.assertIn("Figure review", markdown_path.read_text(encoding="utf-8"))

    def test_tampered_artifact_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_spec(SPEC, output)
            (output / "figure.alt.txt").write_text("tampered\n", encoding="utf-8")
            findings = review_bundle(output)
            errors = {item.rule_id for item in findings if item.severity == "error"}
            self.assertIn("MANIFEST_DIGEST_MISMATCH", errors)

    def test_missing_export_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_spec(SPEC, output)
            (output / "figure.png").unlink()
            findings = review_bundle(output)
            errors = {item.rule_id for item in findings if item.severity == "error"}
            self.assertIn("BUNDLE_ARTIFACT_MISSING", errors)
            self.assertIn("MANIFEST_ENTRY_MISSING", errors)

    def test_untracked_file_is_reported_as_a_warning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_spec(SPEC, output)
            (output / "notes.txt").write_text("scratch\n", encoding="utf-8")
            findings = review_bundle(output)
            warnings = {item.rule_id for item in findings if item.severity == "warning"}
            self.assertIn("MANIFEST_UNTRACKED_FILE", warnings)


if __name__ == "__main__":
    unittest.main()
