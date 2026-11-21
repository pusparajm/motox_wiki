#!/usr/bin/env python3
"""Reject motorcycle records that do not contain a usable model name."""
from __future__ import annotations

import re

# Names that describe a fitment trait, side, trim or import artefact rather
# than a motorcycle model. These must never become public model pages.
GENERIC_MODEL_NAMES = {
    "",
    "abs",
    "base",
    "centennial edition",
    "edition",
    "factory",
    "left",
    "limited edition",
    "model",
    "n/a",
    "na",
    "none",
    "right",
    "special",
    "special edition",
    "standard",
    "unknown",
}


def model_name_error(bike: dict) -> str:
    model = str(bike.get("model") or "").strip()
    if not model:
        return "missing model name"
    if model.lower() in GENERIC_MODEL_NAMES:
        return f"generic model name: {model!r}"
    if not re.sub(r"\([^)]*\)", "", model).strip():
        return f"parenthetical-only model name: {model!r}"
    return ""


def invalid_models(bikes: list[dict]) -> list[tuple[str, str]]:
    problems = []
    for bike in bikes:
        reason = model_name_error(bike)
        if reason:
            problems.append((str(bike.get("id") or "(no id)"), reason))
    return problems


def require_valid_models(bikes: list[dict]) -> None:
    problems = invalid_models(bikes)
    if not problems:
        return
    details = "; ".join(f"{model_id}: {reason}" for model_id, reason in problems[:12])
    if len(problems) > 12:
        details += f"; and {len(problems) - 12} more"
    raise SystemExit(f"Invalid motorcycle records: {details}")
