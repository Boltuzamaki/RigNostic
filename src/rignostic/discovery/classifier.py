"""Conservative semantic classification using names plus structural evidence."""

from __future__ import annotations

import re

from .schemas import ControlClassification

CATEGORIES = {
    "blink": ("blink", "eyelid", "eyesclose"), "brow": ("brow", "eyebrow"),
    "jaw": ("jaw",), "smile": ("smile",), "frown": ("frown",),
    "funnel": ("funnel",), "pucker": ("pucker",), "viseme": ("viseme",),
    "cheek": ("cheek",), "eye": ("eye",), "mouth": ("mouth", "lip"),
    "nose": ("nose",),
}


def side_for(name: str) -> str | None:
    lowered = name.lower()
    if re.search(r"(^l[_\-.]|[_\-.]l$|left)", lowered):
        return "left"
    if re.search(r"(^r[_\-.]|[_\-.]r$|right)", lowered):
        return "right"
    return None


def classify(name: str, evidence: list[str]) -> ControlClassification:
    lowered = name.lower()
    matches = [
        category
        for category, terms in CATEGORIES.items()
        if any(term in lowered for term in terms)
    ]
    category = matches[0] if matches else "unknown"
    structural = bool(evidence)
    if category == "unknown":
        confidence = 0.25
    else:
        confidence = 0.9 if structural else 0.7
    reasons = (
        [f"name matches {category}"]
        if category != "unknown"
        else ["no unique category match"]
    )
    reasons.extend(evidence)
    return ControlClassification(name, category, side_for(name), confidence, tuple(reasons), name)
