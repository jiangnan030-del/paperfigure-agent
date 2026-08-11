# SPDX-License-Identifier: MIT
"""Build deterministic, integrity-checked submission archives."""
from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from paperfig.contracts.artifacts import REQUIRED_RUN_ARTIFACTS
from paperfig.provenance.record import sha256_file
from paperfig.review import exceeds_threshold, review_bundle
from paperfig.review.bundle import RunBundle, load_bundle
from paperfig.review.models import ReviewFinding, count_by_severity
from paperfig.review.report import (
    REVIEW_JSON_NAME,
    REVIEW_MARKDOWN_NAME,
    render_markdown,
    review_payload,
)

PACKAGE_MANIFEST_NAME = "submission.manifest.json"
PACKAGE_CHECKSUM_SUFFIX = ".sha256"
_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class PackageError(RuntimeError):
    """Raised when a bundle is not eligible for submission packaging."""


@dataclass(frozen=True)
class PackageResult:
    archive: Path
    checksum: Path
    findings: list[ReviewFinding]

    def to_dict(self) -> dict[str, Any]:
        return {
            "archive": str(self.archive),
            "checksum": str(self.checksum),
            "sha256": sha256_file(self.archive),
            "review_summary": count_by_severity(self.findings),
            "human_approved": True,
        }


def _validate_audit(bundle: RunBundle) -> None:
    path = bundle.path("figure.audit.json")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise PackageError(f"figure.audit.json cannot be verified: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("status") != "passed":
        raise PackageError("figure.audit.json does not record a passed audit")


def _archive_path(output: str | Path, bundle: RunBundle) -> Path:
    requested = Path(output).resolve()
    archive = requested if requested.suffix.lower() == ".zip" else requested / (
        f"{bundle.root.name}.submission.zip"
    )
    if archive.is_relative_to(bundle.root):
        raise PackageError("write submission packages outside the source run bundle")
    archive.parent.mkdir(parents=True, exist_ok=True)
    return archive


def _source_files(bundle: RunBundle) -> dict[str, bytes]:
    names = [
        *REQUIRED_RUN_ARTIFACTS,
        *(f"figure.{file_format}" for file_format in bundle.spec.export.formats),
    ]
    payload: dict[str, bytes] = {}
    for name in dict.fromkeys(names):
        source = bundle.path(name)
        if source.is_symlink():
            raise PackageError(f"submission input must not be a symlink: {name}")
        if not source.is_file():
            raise PackageError(f"submission input is missing: {name}")
        payload[name] = source.read_bytes()
    return payload


def _review_files(bundle: RunBundle, findings: list[ReviewFinding]) -> dict[str, bytes]:
    payload = review_payload(bundle.root, findings)
    payload.pop("generated_at", None)
    json_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return {
        REVIEW_JSON_NAME: json_text.encode("utf-8"),
        REVIEW_MARKDOWN_NAME: render_markdown(bundle.root, findings).encode("utf-8"),
    }


def _package_manifest(
    bundle: RunBundle,
    files: dict[str, bytes],
    findings: list[ReviewFinding],
    fail_on: str,
) -> bytes:
    payload = {
        "schema_version": 1,
        "bundle": bundle.root.name,
        "human_approved": True,
        "review_threshold": fail_on,
        "review_summary": count_by_severity(findings),
        "source_manifest_sha256": sha256_file(bundle.path("artifact.manifest.json")),
        "artifacts": [
            {
                "path": name,
                "size_bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for name, content in sorted(files.items())
        ],
    }
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _write_deterministic_zip(path: Path, files: dict[str, bytes]) -> None:
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".zip", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for name, content in sorted(files.items()):
                info = zipfile.ZipInfo(name, date_time=_ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content, compresslevel=9)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def build_submission_package(
    bundle_dir: str | Path,
    output: str | Path,
    *,
    human_approved: bool,
    fail_on: str = "error",
) -> PackageResult:
    """Review a bundle and build a deterministic, self-verifying ZIP archive."""
    if not human_approved:
        raise PackageError(
            "human approval is required; inspect the figure, then pass --approve"
        )
    bundle = load_bundle(bundle_dir)
    _validate_audit(bundle)
    findings = review_bundle(bundle.root)
    if exceeds_threshold(findings, fail_on):
        counts = count_by_severity(findings)
        raise PackageError(
            f"review findings exceed --fail-on {fail_on}: "
            f"errors={counts['error']}, warnings={counts['warning']}"
        )

    files = _source_files(bundle)
    files.update(_review_files(bundle, findings))
    files[PACKAGE_MANIFEST_NAME] = _package_manifest(bundle, files, findings, fail_on)
    archive = _archive_path(output, bundle)
    _write_deterministic_zip(archive, files)
    checksum = Path(f"{archive}{PACKAGE_CHECKSUM_SUFFIX}")
    checksum.write_text(f"{sha256_file(archive)}  {archive.name}\n", encoding="utf-8")
    return PackageResult(archive=archive, checksum=checksum, findings=findings)
