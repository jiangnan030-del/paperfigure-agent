# SPDX-License-Identifier: MIT
import json
import os
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from paperfig.harness import render_spec
from paperfig.qa import AuditError


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
                "figure.data.csv",
                "figure.py",
                "figure.alt.txt",
                "figure.audit.json",
                "figure.provenance.json",
                "run.log.jsonl",
                "environment.lock",
                "artifact.manifest.json",
            }
            self.assertTrue(expected <= {item.name for item in output.iterdir()})
            py_compile.compile(str(output / "figure.py"), doraise=True)

            bundled_spec = yaml.safe_load(
                (output / "figure.spec.yaml").read_text(encoding="utf-8")
            )
            self.assertEqual("figure.data.csv", bundled_spec["data"]["source"])

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

            manifest = json.loads(
                (output / "artifact.manifest.json").read_text(encoding="utf-8")
            )
            manifest_names = {item["path"] for item in manifest["artifacts"]}
            self.assertTrue((expected - {"artifact.manifest.json"}) <= manifest_names)

            environment = (output / "environment.lock").read_text(encoding="utf-8")
            self.assertIn("matplotlib==", environment)
            self.assertIn("numpy==", environment)
            self.assertIn("PyYAML==", environment)

            env = os.environ.copy()
            python_path = [str(Path("src").resolve())]
            if env.get("PYTHONPATH"):
                python_path.append(env["PYTHONPATH"])
            env["PYTHONPATH"] = os.pathsep.join(python_path)
            replay = subprocess.run(
                [sys.executable, "figure.py"],
                cwd=output,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, replay.returncode, msg=replay.stderr)

    def test_render_preserves_failed_audit_then_raises(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "data.csv"
            data_path.write_text("label,value\nA,1.0\n", encoding="utf-8")
            spec_path = root / "figure.yaml"
            spec_path.write_text(
                """claim: "Synthetic audit gate test."
venue: nature-machine-intelligence
stage: draft
backend: matplotlib

data:
  source: data.csv
  license: CC0-1.0
  citation: "Synthetic test fixture."

chart:
  family: comparison
  mark: bar
  x: label
  y: value

references:
  - id: missing-url
    copied_files: []
    license_status: unknown
""",
                encoding="utf-8",
            )
            output = root / "run"
            with self.assertRaisesRegex(AuditError, "failed audit"):
                render_spec(spec_path, output)

            audit = json.loads((output / "figure.audit.json").read_text(encoding="utf-8"))
            self.assertEqual("failed", audit["status"])
            self.assertTrue((output / "figure.provenance.json").is_file())
            self.assertTrue((output / "artifact.manifest.json").is_file())

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
