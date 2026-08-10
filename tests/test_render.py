# SPDX-License-Identifier: MIT
import json
import py_compile
import tempfile
import unittest
from pathlib import Path

from paperfig.harness import render_spec


class RenderTests(unittest.TestCase):
    def test_render_emits_auditable_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_spec("examples/specs/grouped_bar.yaml", output)
            expected = {
                "figure.svg",
                "figure.pdf",
                "figure.png",
                "figure.spec.yaml",
                "figure.py",
                "figure.alt.txt",
                "figure.audit.json",
                "figure.provenance.json",
                "run.log.jsonl",
                "environment.lock",
            }
            self.assertTrue(expected <= {item.name for item in output.iterdir()})
            py_compile.compile(str(output / "figure.py"), doraise=True)
            audit = json.loads((output / "figure.audit.json").read_text(encoding="utf-8"))
            self.assertEqual("passed", audit["status"])
            self.assertEqual("passed", audit["checks"]["data_validation"])
            provenance = json.loads(
                (output / "figure.provenance.json").read_text(encoding="utf-8")
            )
            self.assertTrue(provenance["human_review_required"])
            self.assertEqual(
                "nature-machine-intelligence-2026-starter",
                provenance["venue_profile"]["name"],
            )
            self.assertTrue(provenance["venue_profile"]["sources"])

    def test_every_supported_mark_renders(self) -> None:
        specs = sorted(Path("examples/specs").glob("*.yaml"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for spec_path in specs:
                with self.subTest(spec=spec_path.name):
                    output = root / spec_path.stem
                    render_spec(spec_path, output)
                    self.assertTrue((output / "figure.svg").is_file())
                    self.assertTrue((output / "figure.audit.json").is_file())


if __name__ == "__main__":
    unittest.main()
