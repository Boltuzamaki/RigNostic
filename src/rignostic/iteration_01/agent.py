"""Single-call Iteration 1 agent using RigInventory before baseline observations."""

from __future__ import annotations

import json
from typing import Any

from rignostic.baseline.agent import _parse_json
from rignostic.baseline.prompt import BASELINE_PROMPT
from rignostic.config import BaselineConfig
from rignostic.models import create_model_client


def analyze_with_inventory(
    inventory: dict[str, Any], observations: dict[str, Any], config: BaselineConfig
) -> tuple[dict[str, Any], dict[str, int | None]]:
    prompt = f"""{BASELINE_PROMPT}

Before inspecting individual controls, review the deterministic RigInventory below. Use it to
understand available controls and relationships among bones, drivers, shape keys, constraints,
meshes, and vertex groups. Treat semantic classifications as uncertain suggestions and prefer
structural dependency evidence. Shape keys owned by different objects do not conflict merely
because they share a name.

Then assess the same coarse baseline tool outputs. Do not perform pairwise interaction search,
adaptive test planning, geometry anomaly analysis, visual verification, or repair. Unknown is
acceptable. Return JSON only with this exact top-level shape:
{{"detected_defects":[{{"defect_type":"...","affected_control":"...","description":"...","likely_root_cause":"...","confidence":0.0}}],"suggested_repairs":["..."]}}

RIG INVENTORY:
{json.dumps(inventory, sort_keys=True)}

BASELINE TOOL OUTPUTS:
{json.dumps(observations, sort_keys=True)}
"""
    response = create_model_client(config).generate(prompt)
    return _parse_json(response.text), {
        "model_calls": 1,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
    }
