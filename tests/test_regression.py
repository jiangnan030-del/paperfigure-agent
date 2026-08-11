# SPDX-License-Identifier: MIT
import json
import tempfile
import unittest
from typing import Any

from paperfig.regression import (
    FINGERPRINT_SCHEMA_VERSION,
    FigureFingerprint,
    build_fingerprint,
    compare_fingerprints,
    record_baseline,
    regress_spec,
)
from paperfig.regression.baseline import load_baseline, write_baseline

SPEC = "examples/specs/grouped_bar.yaml"

_BASE_ENV = {"matplotlib": "3.9.0", "python": "3.12.3", "platform": "Linux-x86_64"}
_OTHER_ENV = {"matplotlib": "3.10.0", "python": "3.12.3", "platform": "Linux-x86_64"}

_SAMPLE_SVG = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<svg xmlns="http://www.w3.org/2000/svg" width="252pt" height="180pt">'
    '<g id="axes">'
    '<path d="M 10.04 20.02 L 30.4 40.48 z" style="fill:#0072B2;"/>'
    '<path d="M 50 60 L 70 80 z" style="stroke:#e69f00;"/>'
    "<text style=\"font: 7px 'DejaVu Sans'\">Accuracy</text>"
    "</g>"
    "</svg>"
)


def _fingerprint(**overrides: Any) -> FigureFingerprint:
    fields: dict[str, Any] = {
        "schema_version": FINGERPRINT_SCHEMA_VERSION,
        "spec_name": "demo",
        "canvas_width_pt": 252.0,
        "canvas_height_pt": 180.0,
        "element_counts": {"path": 40, "text": 12},
        "text_content": ["Baseline", "Ours", "Accuracy"],
        "colors": ["#0072b2", "#e69f00"],
        "font_sizes_pt": [7.0],
        "geometry_digest": "a" * 64,
        "geometry_points": 900,
        "environment": dict(_BASE_ENV),
    }
    fields.update(overrides)
    return FigureFingerprint(**fields)


def _by_rule(findings: list[Any]) -> dict[str, str]:
    return {item.rule_id: item.severity for item in findings}


class FingerprintContentTests(unittest.TestCase):
    def test_structure_is_extracted_from_svg(self) -> None:
        fingerprint = build_fingerprint(_SAMPLE_SVG, "demo")
        self.assertEqual(252.0, fingerprint.canvas_width_pt)
        self.assertEqual(180.0, fingerprint.canvas_height_pt)
        self.assertEqual(["Accuracy"], fingerprint.text_content)
        self.assertEqual(["#0072b2", "#e69f00"], fingerprint.colors)
        self.assertEqual([7.0], fingerprint.font_sizes_pt)
        self.assertEqual(2, fingerprint.element_counts["path"])
        self.assertEqual(1, fingerprint.element_counts["text"])
        self.assertEqual(8, fingerprint.geometry_points)

    def test_geometry_digest_ignores_sub_quantum_movement(self) -> None:
        moved = _SAMPLE_SVG.replace("10.04", "10.09")
        self.assertEqual(
            build_fingerprint(_SAMPLE_SVG, "demo").geometry_digest,
            build_fingerprint(moved, "demo").geometry_digest,
        )

    def test_geometry_digest_reacts_to_real_movement(self) -> None:
        moved = _SAMPLE_SVG.replace("10.04", "48.0")
        self.assertNotEqual(
            build_fingerprint(_SAMPLE_SVG, "demo").geometry_digest,
            build_fingerprint(moved, "demo").geometry_digest,
        )


class ComparisonTests(unittest.TestCase):
    def test_identical_fingerprints_produce_no_findings(self) -> None:
        self.assertEqual([], compare_fingerprints(_fingerprint(), _fingerprint()))

    def test_text_change_is_an_error(self) -> None:
        current = _fingerprint(text_content=["Baseline", "Ours", "Precision"])
        self.assertEqual("error", _by_rule(compare_fingerprints(_fingerprint(), current))[
            "FIGURE_TEXT_CHANGED"
        ])

    def test_color_change_is_an_error(self) -> None:
        current = _fingerprint(colors=["#0072b2", "#ff0000"])
        rules = _by_rule(compare_fingerprints(_fingerprint(), current))
        self.assertEqual("error", rules["FIGURE_COLORS_CHANGED"])

    def test_font_size_change_is_an_error(self) -> None:
        rules = _by_rule(compare_fingerprints(_fingerprint(), _fingerprint(font_sizes_pt=[5.0])))
        self.assertEqual("error", rules["FIGURE_FONT_SIZES_CHANGED"])

    def test_geometry_change_warns_inside_one_environment(self) -> None:
        current = _fingerprint(geometry_digest="b" * 64, geometry_points=901)
        rules = _by_rule(compare_fingerprints(_fingerprint(), current))
        self.assertEqual("warning", rules["FIGURE_GEOMETRY_CHANGED"])
        self.assertNotIn("BASELINE_ENVIRONMENT_DRIFT", rules)

    def test_geometry_change_is_a_note_after_environment_drift(self) -> None:
        current = _fingerprint(geometry_digest="b" * 64, environment=dict(_OTHER_ENV))
        rules = _by_rule(compare_fingerprints(_fingerprint(), current))
        self.assertEqual("info", rules["FIGURE_GEOMETRY_CHANGED"])
        self.assertEqual("warning", rules["BASELINE_ENVIRONMENT_DRIFT"])

    def test_text_change_stays_an_error_after_environment_drift(self) -> None:
        current = _fingerprint(
            text_content=["Baseline", "Ours", "Precision"],
            environment=dict(_OTHER_ENV),
        )
        rules = _by_rule(compare_fingerprints(_fingerprint(), current))
        self.assertEqual("error", rules["FIGURE_TEXT_CHANGED"])

    def test_small_canvas_drift_is_tolerated(self) -> None:
        current = _fingerprint(canvas_width_pt=252.0 * 1.005)
        self.assertEqual([], compare_fingerprints(_fingerprint(), current))

    def test_large_canvas_drift_is_reported(self) -> None:
        rules = _by_rule(compare_fingerprints(_fingerprint(), _fingerprint(canvas_width_pt=300.0)))
        self.assertIn("FIGURE_CANVAS_RESIZED", rules)


class BaselineStorageTests(unittest.TestCase):
    def test_round_trip_preserves_the_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = _fingerprint()
            path = write_baseline(directory, original)
            self.assertTrue(path.is_file())
            self.assertEqual(original, load_baseline(directory, "demo"))

    def test_absent_baseline_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(load_baseline(directory, "absent"))


class RenderedFingerprintTests(unittest.TestCase):
    def test_two_renders_produce_the_same_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = record_baseline(SPEC, first)
            two = record_baseline(SPEC, second)
            self.assertEqual(
                json.loads(one.read_text(encoding="utf-8")),
                json.loads(two.read_text(encoding="utf-8")),
            )

    def test_recorded_baseline_matches_the_next_render(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            record_baseline(SPEC, directory)
            _, findings = regress_spec(SPEC, directory)
            self.assertEqual([], findings)

    def test_absent_baseline_is_reported_as_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            _, findings = regress_spec(SPEC, directory)
            self.assertEqual(["BASELINE_MISSING"], [item.rule_id for item in findings])
            self.assertEqual("error", findings[0].severity)


if __name__ == "__main__":
    unittest.main()
