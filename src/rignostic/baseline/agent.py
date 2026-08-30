"""One-call Stage 0 baseline over coarse Blender observations."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from rignostic.baseline.prompt import BASELINE_PROMPT
from rignostic.config import BaselineConfig
from rignostic.models import create_model_client


def _parse_json(text: str) -> dict[str, Any]:
    value = text.strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[1].rsplit("```", 1)[0]
    parsed = json.loads(value)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("detected_defects"), list):
        raise ValueError("model output does not match the baseline result shape")
    return parsed


def _remove_unsupported_driver_conflicts(
    result: dict[str, Any], observations: dict[str, Any]
) -> dict[str, Any]:
    """Reject model conflict claims unless the exact driven property is duplicated."""
    drivers = observations.get("driver_summary", observations.get("drivers", []))
    paths = Counter(
        (driver.get("owner"), driver.get("data_path"))
        for driver in drivers
        if isinstance(driver, dict)
    )
    has_conflict = any(count > 1 for count in paths.values())
    if has_conflict:
        return result
    result["detected_defects"] = [
        finding
        for finding in result["detected_defects"]
        if not (
            "driver" in str(finding.get("defect_type", "")).lower()
            and "conflict" in str(finding.get("defect_type", "")).lower()
        )
    ]
    return result


def analyze_observations(
    observations: dict[str, Any], config: BaselineConfig
) -> tuple[dict[str, Any], dict[str, int | None]]:
    prompt = f"""{BASELINE_PROMPT}

You have already used the basic Blender tools. Their coarse outputs are below.
Do not claim visual or geometry evidence that is absent. Unknown is acceptable.
Shape keys on different owner objects are independent and are not conflicting merely because they
share a name. Different shape-key data paths on the same owner are also independent. Report a driver
conflict only when the same owner and exact data_path occur more than once. A shape key with zero
affected vertices cannot deform its mesh. Use average_delta as structural evidence about movement.
Compare left/right counterparts: mirrored controls normally share the same vertical direction and
similar magnitude. A smile corner moving downward while its counterpart moves upward is suspicious.
Use relative_displacement to identify deformation unusually large for its owner, but report only
clear outliers. Do not invent an expected direction unless it follows clearly from the control's
semantics.

Return JSON only with this exact top-level shape:
{{"detected_defects":[{{"defect_type":"...","affected_control":"...","description":"...","likely_root_cause":"...","confidence":0.0}}],"suggested_repairs":["..."]}}

TOOL OUTPUTS:
{json.dumps(observations, sort_keys=True)}
"""
    response = create_model_client(config).generate(prompt)
    result = _remove_unsupported_driver_conflicts(_parse_json(response.text), observations)
    return result, {
        "model_calls": 1,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
    }
