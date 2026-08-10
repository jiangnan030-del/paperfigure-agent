# SPDX-License-Identifier: MIT
from __future__ import annotations

from importlib import resources
from typing import Any

import yaml


_PROFILE_ALIASES = {
    "nature machine intelligence": "nature_machine_intelligence",
    "nature-machine-intelligence": "nature_machine_intelligence",
    "natmachintell": "nature_machine_intelligence",
    "nmi": "nature_machine_intelligence",
    "icml": "icml_2026",
    "icml 2026": "icml_2026",
    "neurips": "neurips_2026",
    "neurips 2026": "neurips_2026",
    "eccv": "eccv_2026",
    "eccv 2026": "eccv_2026",
}


def load_profile(venue: str) -> dict[str, Any]:
    profile_name = _PROFILE_ALIASES.get(venue.lower())
    if profile_name is None:
        raise ValueError(
            f"unsupported venue profile '{venue}'; choose one of Nature Machine Intelligence, "
            "ICML 2026, NeurIPS 2026, or ECCV 2026"
        )
    target = resources.files("paperfig.profiles").joinpath(f"{profile_name}.yaml")
    with target.open("r", encoding="utf-8") as handle:
        profile = yaml.safe_load(handle)
    if not profile.get("sources"):
        raise ValueError(f"venue profile '{profile_name}' has no recorded source")
    return profile
