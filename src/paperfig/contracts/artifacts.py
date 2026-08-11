# SPDX-License-Identifier: MIT
REQUIRED_RUN_ARTIFACTS = (
    "figure.spec.yaml",
    "figure.data.csv",
    "figure.py",
    "figure.audit.json",
    "figure.provenance.json",
    "figure.alt.txt",
    "run.log.jsonl",
    "environment.lock",
    "artifact.manifest.json",
)

# Written by `paperfig review`, not by `paperfig render`, so these stay out of
# REQUIRED_RUN_ARTIFACTS and out of the render-time artifact manifest.
REVIEW_ARTIFACTS = (
    "figure.review.json",
    "figure.review.md",
)
