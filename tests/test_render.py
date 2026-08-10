# SPDX-License-Identifier: MIT
import json
from pathlib import Path
import tempfile
import unittest

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
            audit = json.loads((output / "figure.audit.json").read_text(encoding="utf-8"))
            self.assertEqual("passed", audit["status"])
            provenance = json.loads(
                (output / "figure.provenance.json").read_text(encoding="utf-8")
            )
            self.assertTrue(provenance["human_review_required"])
            self.assertEqual(
                "nature-machine-intelligence-2026-starter",
                provenance["venue_profile"]["name"],
            )
            self.assertTrue(provenance["venue_profile"]["sources"])


if __name__ == "__main__":
    unittest.main()
