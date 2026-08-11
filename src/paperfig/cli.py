# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from paperfig.comparison import compare_bundles, write_comparison
from paperfig.harness import render_spec
from paperfig.packaging import PackageError, build_submission_package
from paperfig.qa import AuditError, audit_spec
from paperfig.regression import (
    DEFAULT_BASELINE_DIR,
    RegressionError,
    record_baseline,
    regress_spec,
)
from paperfig.review import ReviewError, exceeds_threshold, review_bundle, write_review
from paperfig.spec import SpecError, load_spec

_STARTER_DATA = """model,dataset,accuracy,std
Baseline,A,0.71,0.020
Ours,A,0.86,0.012
Baseline,B,0.68,0.024
Ours,B,0.83,0.014
"""

_STARTER_SPEC = """claim: "The proposed method improves accuracy on synthetic data."
venue: nature-machine-intelligence
stage: draft
backend: matplotlib

data:
  source: data.csv
  license: CC0-1.0
  citation: "Synthetic starter data created by paperfig init; not research evidence."

chart:
  family: comparison
  mark: bar
  x: model
  y: accuracy
  series: dataset
  error: std
  highlight: Ours

qa:
  require_zero_baseline: true
  color_vision_gate: true
  require_alt_text: true

export:
  formats: [svg, pdf, png]
  dpi: 300
"""


def _init_project(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    spec_path = destination / "figure.yaml"
    data_path = destination / "data.csv"
    for path in (spec_path, data_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite existing file: {path}")
    spec_path.write_text(_STARTER_SPEC, encoding="utf-8")
    data_path.write_text(_STARTER_DATA, encoding="utf-8")
    (destination / "README.md").write_text(
        "# PaperFigure project\n\n"
        "The included data is synthetic. Run "
        "`paperfig render figure.yaml --output runs/demo`.\n",
        encoding="utf-8",
    )


def _add_fail_on(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--fail-on",
        choices=("error", "warning", "never"),
        default="error",
        help="severity that makes the command exit non-zero (default: error)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paperfig",
        description="Render, audit, review, compare, and package scientific figures",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create a starter project")
    init_parser.add_argument("path", type=Path)

    validate_parser = subparsers.add_parser("validate", help="validate a FigureSpec")
    validate_parser.add_argument("spec", type=Path)

    render_parser = subparsers.add_parser("render", help="render a FigureSpec")
    render_parser.add_argument("spec", type=Path)
    render_parser.add_argument("--output", type=Path, required=True)

    audit_parser = subparsers.add_parser("audit", help="audit a FigureSpec and artifacts")
    audit_parser.add_argument("spec", type=Path)
    audit_parser.add_argument("--artifacts", type=Path)

    review_parser = subparsers.add_parser("review", help="review a rendered run bundle")
    review_parser.add_argument("bundle", type=Path)
    _add_fail_on(review_parser)

    regress_parser = subparsers.add_parser(
        "regress", help="compare a rendering against its recorded baseline"
    )
    regress_parser.add_argument("spec", type=Path)
    regress_parser.add_argument(
        "--baselines",
        type=Path,
        default=DEFAULT_BASELINE_DIR,
        help=f"directory holding recorded baselines (default: {DEFAULT_BASELINE_DIR})",
    )
    regress_parser.add_argument(
        "--update",
        action="store_true",
        help="record the current rendering as the new baseline",
    )
    _add_fail_on(regress_parser)

    compare_parser = subparsers.add_parser(
        "compare", help="compare baseline and candidate run bundles"
    )
    compare_parser.add_argument("baseline", type=Path)
    compare_parser.add_argument("candidate", type=Path)
    compare_parser.add_argument(
        "--output",
        type=Path,
        help="optional directory for JSON and Markdown comparison reports",
    )
    _add_fail_on(compare_parser)

    package_parser = subparsers.add_parser(
        "package", help="build an integrity-checked submission archive"
    )
    package_parser.add_argument("bundle", type=Path)
    package_parser.add_argument("--output", type=Path, required=True)
    package_parser.add_argument(
        "--approve",
        action="store_true",
        help="acknowledge human review of the figure and scientific content",
    )
    _add_fail_on(package_parser)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            _init_project(args.path)
            print(args.path.resolve())
            return
        if args.command == "validate":
            spec = load_spec(args.spec)
            print(json.dumps(asdict(spec), ensure_ascii=False, indent=2))
            return
        if args.command == "render":
            artifacts = render_spec(args.spec, args.output)
            print(json.dumps([str(item) for item in artifacts], indent=2))
            return
        if args.command == "audit":
            spec = load_spec(args.spec)
            issues = audit_spec(spec, artifact_dir=args.artifacts)
            print(json.dumps([issue.to_dict() for issue in issues], ensure_ascii=False, indent=2))
            if any(issue.severity == "error" for issue in issues):
                raise SystemExit(2)
            return
        if args.command == "review":
            findings = review_bundle(args.bundle)
            write_review(args.bundle, findings)
            print(json.dumps([item.to_dict() for item in findings], ensure_ascii=False, indent=2))
            if exceeds_threshold(findings, args.fail_on):
                raise SystemExit(2)
            return
        if args.command == "regress":
            if args.update:
                print(str(record_baseline(args.spec, args.baselines)))
                return
            _, findings = regress_spec(args.spec, args.baselines)
            print(json.dumps([item.to_dict() for item in findings], ensure_ascii=False, indent=2))
            if exceeds_threshold(findings, args.fail_on):
                raise SystemExit(2)
            return
        if args.command == "compare":
            comparison = compare_bundles(args.baseline, args.candidate)
            if args.output is not None:
                write_comparison(args.output, comparison)
            print(json.dumps(comparison.to_dict(), ensure_ascii=False, indent=2))
            if exceeds_threshold(comparison.findings, args.fail_on):
                raise SystemExit(2)
            return
        if args.command == "package":
            result = build_submission_package(
                args.bundle,
                args.output,
                human_approved=args.approve,
                fail_on=args.fail_on,
            )
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            return
    except (
        AuditError,
        PackageError,
        RegressionError,
        ReviewError,
        SpecError,
        FileExistsError,
    ) as exc:
        raise SystemExit(str(exc)) from exc
