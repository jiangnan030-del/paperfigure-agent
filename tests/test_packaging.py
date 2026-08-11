# SPDX-License-Identifier: MIT
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from paperfig.harness import render_spec
from paperfig.packaging import PackageError, build_submission_package
from paperfig.provenance.record import sha256_file

SPEC = "examples/specs/grouped_bar.yaml"


class SubmissionPackageTests(unittest.TestCase):
    def test_archive_is_deterministic_and_self_describing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            render_spec(SPEC, bundle)
            first = build_submission_package(
                bundle,
                root / "first.zip",
                human_approved=True,
            )
            second = build_submission_package(
                bundle,
                root / "second.zip",
                human_approved=True,
            )
            self.assertEqual(sha256_file(first.archive), sha256_file(second.archive))
            with zipfile.ZipFile(first.archive) as archive:
                names = set(archive.namelist())
                self.assertIn("figure.svg", names)
                self.assertIn("figure.review.json", names)
                self.assertIn("submission.manifest.json", names)
                manifest = json.loads(archive.read("submission.manifest.json"))
            self.assertTrue(manifest["human_approved"])
            self.assertTrue(first.checksum.is_file())

    def test_human_approval_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            render_spec(SPEC, bundle)
            with self.assertRaises(PackageError):
                build_submission_package(
                    bundle,
                    root / "submission.zip",
                    human_approved=False,
                )

    def test_tampered_bundle_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "bundle"
            render_spec(SPEC, bundle)
            (bundle / "figure.alt.txt").write_text("tampered\n", encoding="utf-8")
            with self.assertRaises(PackageError):
                build_submission_package(
                    bundle,
                    root / "submission.zip",
                    human_approved=True,
                )


if __name__ == "__main__":
    unittest.main()
