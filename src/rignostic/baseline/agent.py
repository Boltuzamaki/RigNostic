"""One-call Stage 0 baseline over coarse Blender observations."""

from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rignostic.baseline.prompt import BASELINE_PROMPT
from rignostic.config import BaselineConfig
from rignostic.models import create_model_client
from rignostic.models.factory import litellm_model_name

AGENT_TOOLS = {
    "scene_summary": "scene",
    "bone_names": "bones",
    "shape_key_names": "shape_keys",
    "driver_summary": "drivers",
    "constraint_summary": "constraints",
    "shape_key_deformation_summary": "shape_key_deformation",
    "structural_details": "structural_details",
}

ActionCallback = Callable[[dict[str, Any]], None]
ToolRunner = Callable[[Path, str], Any]


def _parse_json(text: str) -> dict[str, Any]:
    value = text.strip()
    if value.startswith("```"):
        value = value.split("\n", 1)[1].rsplit("```", 1)[0]
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("model output must be a JSON object")
    return parsed


def _validate_report(parsed: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(parsed.get("detected_defects"), list):
        raise ValueError("model output does not match the diagnosis result shape")
    if not isinstance(parsed.get("suggested_repairs", []), list):
        raise ValueError("model suggested_repairs must be a list")
    parsed.setdefault("suggested_repairs", [])
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


def _counterpart(name: str) -> str | None:
    for suffix, replacement in (("_L", "_R"), ("_R", "_L"), (".L", ".R"), (".R", ".L")):
        if name.endswith(suffix):
            return name[: -len(suffix)] + replacement
    return None


def _add_structural_findings(
    report: dict[str, Any], observations: dict[str, Any]
) -> dict[str, Any]:
    """Add only findings directly proven by numeric Blender output."""
    findings: list[dict[str, Any]] = []
    controls: set[str] = set()
    details = observations.get("structural_details", {})
    detail_drivers = details.get("drivers", []) if isinstance(details, dict) else []
    detail_keys = details.get("shape_keys", []) if isinstance(details, dict) else []
    detail_constraints = details.get("constraints", []) if isinstance(details, dict) else []

    def add(defect_type: str, control: str, description: str, cause: str) -> None:
        key = f"{defect_type}:{control}"
        if key in controls:
            return
        controls.add(key)
        findings.append({
            "defect_type": defect_type,
            "affected_control": control,
            "description": description,
            "likely_root_cause": cause,
            "confidence": 1.0,
            "evidence_source": "deterministic_validation",
        })

    driver_targets: dict[str, list[str]] = {}
    identity_targets: dict[str, str] = {}

    def target_control(target: dict[str, Any]) -> str:
        bone = str(target.get("bone_target") or "")
        if bone:
            return bone
        match = re.search(r'pose\.bones\["([^"]+)"\]', str(target.get("data_path") or ""))
        return match.group(1) if match else ""

    for driver in detail_drivers:
        match = re.search(r'key_blocks\["([^"]+)"\]', str(driver.get("data_path", "")))
        if not match:
            continue
        driven_control = match.group(1)
        expression = str(driver.get("expression", "")).replace(" ", "")
        targets = [
            target_control(target)
            for variable in driver.get("variables", [])
            for target in variable.get("targets", [])
            if target_control(target)
        ]
        driver_targets[driven_control] = targets
        if driver.get("muted"):
            add("muted_driver", driven_control, "The shape-key driver is muted.", "driver_muted")
        if re.fullmatch(r"-var", expression):
            add(
                "reversed_direction", driven_control,
                "The driver negates its control variable.", "negative_driver_expression",
            )
        multiplier = re.fullmatch(r"var\*([0-9]+(?:\.[0-9]+)?)", expression)
        if multiplier and float(multiplier.group(1)) > 1.5:
            add(
                "excessive_multiplier", driven_control,
                f"The driver multiplier is {multiplier.group(1)}.", "driver_multiplier_too_high",
            )
        if expression == "var" and len(targets) == 1:
            identity_targets[driven_control] = targets[0]

    key_names = {str(item.get("name", "")) for item in detail_keys}
    handled_swaps: set[frozenset[str]] = set()
    for driven_control, target_name in identity_targets.items():
        if target_name == driven_control or target_name.endswith(f"{driven_control}_ctrl"):
            continue
        pair = frozenset((driven_control, target_name))
        if (
            _counterpart(driven_control) == target_name
            and identity_targets.get(target_name) == driven_control
        ):
            if pair in handled_swaps:
                continue
            handled_swaps.add(pair)
            affected = next(
                (name for name in pair if name.endswith(("_L", ".L"))),
                sorted(pair)[0],
            )
            add(
                "swapped_controls", affected,
                f"The counterpart drivers for {sorted(pair)} target each other.",
                "driver_targets_swapped",
            )
        elif target_name in key_names:
            add(
                "wrong_shape_key_target", target_name,
                f"{target_name} drives unrelated shape key {driven_control}.",
                "driver_variable_targets_wrong_control",
            )

    keys_by_owner: dict[str, list[dict[str, Any]]] = {}
    for key in detail_keys:
        keys_by_owner.setdefault(str(key.get("owner", "")), []).append(key)
    for owner_keys in keys_by_owner.values():
        typical_max = statistics.median(float(key.get("slider_max", 1.0)) for key in owner_keys)
        for key in owner_keys:
            slider_max = float(key.get("slider_max", 1.0))
            if typical_max > 0 and slider_max > typical_max * 1.5:
                add(
                    "excessive_range", str(key.get("name", "")),
                    f"Shape-key slider maximum {slider_max:g} is an owner-level outlier.",
                    "shape_key_slider_max",
                )

    constraint_lookup = {
        (str(item.get("owner", "")), str(item.get("name", "")), str(item.get("type", ""))): item
        for item in detail_constraints
    }
    for constraint in detail_constraints:
        owner = str(constraint.get("owner", ""))
        counterpart = _counterpart(owner)
        peer = constraint_lookup.get(
            (counterpart or "", str(constraint.get("name", "")), str(constraint.get("type", "")))
        )
        influence = float(constraint.get("influence", 1.0))
        if peer is not None and influence < 0.5 and float(peer.get("influence", 1.0)) > 0.9:
            add(
                "constraint_influence", owner,
                f"Constraint influence {influence:.3g} is far below its counterpart.",
                "constraint_influence_too_low",
            )

    rows = observations.get("shape_key_deformation", [])
    if not isinstance(rows, list):
        report["detected_defects"] = findings
        return report

    keyed = {
        (str(row.get("owner", "")), str(row.get("shape_key", ""))): row
        for row in rows
        if isinstance(row, dict)
    }
    for (owner, control), row in keyed.items():
        if row.get("affected_vertex_count") == 0 and "combination" not in control.lower():
            add(
                "zero_affected_vertices", control,
                f"{control} does not move any vertices on {owner}.",
                "shape_key_contains_no_deformation",
            )

        if (
            "combination" in control.lower()
            and float(row.get("relative_displacement", 0) or 0) > 0.5
        ):
            targets = driver_targets.get(control, [])
            affected = "+".join(targets) if len(targets) >= 2 else control
            add(
                "combination_overdeformation", affected,
                f"Combination shape key {control} has excessive displacement.",
                "combined_controls_overdeform",
            )

        pair_name = _counterpart(control)
        pair = keyed.get((owner, pair_name or ""))
        if pair is None or not pair_name or control > pair_name:
            continue
        own_delta = row.get("average_delta")
        pair_delta = pair.get("average_delta")
        if not (
            isinstance(own_delta, list)
            and isinstance(pair_delta, list)
            and len(own_delta) == 3
            and len(pair_delta) == 3
        ):
            continue
        own_z, pair_z = float(own_delta[2]), float(pair_delta[2])
        if own_z * pair_z < 0 and max(abs(own_z), abs(pair_z)) > 0.01:
            affected = control if own_z < pair_z else pair_name
            add(
                "asymmetric_movement", affected,
                f"{control} and {pair_name} move in opposite vertical directions.",
                "mirrored_shape_key_deformation_reversed",
            )

        if pair is not None and pair_name and control < pair_name:
            own_relative = float(row.get("relative_displacement", 0) or 0)
            pair_relative = float(pair.get("relative_displacement", 0) or 0)
            smaller = min(own_relative, pair_relative)
            larger = max(own_relative, pair_relative)
            if smaller > 0 and larger / smaller > 3 and larger > 0.5:
                affected = control if own_relative > pair_relative else pair_name
                add(
                    "excessive_deformation", affected,
                    f"{affected} deforms over three times more than its counterpart.",
                    "shape_key_deformation_excessive",
                )

    by_owner: dict[str, list[dict[str, Any]]] = {}
    for row in keyed.values():
        if float(row.get("relative_displacement", 0) or 0) > 0:
            by_owner.setdefault(str(row.get("owner", "")), []).append(row)
    for _owner, owner_rows in by_owner.items():
        if len(owner_rows) < 3:
            continue
        values = [float(row["relative_displacement"]) for row in owner_rows]
        typical = statistics.median(values)
        for row in owner_rows:
            value = float(row["relative_displacement"])
            control = str(row["shape_key"])
            peers = [candidate for candidate in values if candidate != value]
            peer_typical = statistics.median(peers) if peers else typical
            if (
                value > peer_typical * 2.2
                and value > 0.5
                and "combination" not in control.lower()
            ):
                add(
                    "excessive_deformation", control,
                    f"{control} moves over 2.2 times the typical owner-level range.",
                    "shape_key_deformation_excessive",
                )
    report["detected_defects"] = findings
    return report


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
    result = _remove_unsupported_driver_conflicts(
        _validate_report(_parse_json(response.text)), observations
    )
    return result, {
        "model_calls": 1,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
    }


def _agent_prompt(observations: dict[str, Any], used_tools: list[str]) -> str:
    available = [tool for tool in AGENT_TOOLS if tool not in used_tools]
    return f"""You are diagnosing a Blender rig. Decide which inspection to run next based
on the evidence already collected. Do not assume a defect exists. Do not invent visual evidence.

Available tools: {json.dumps(available)}
Tools already used: {json.dumps(used_tools)}
Evidence: {json.dumps(observations, sort_keys=True)}

Return JSON only. Choose exactly one form:
{{"action":"use_tool","tool":"one available tool","reason":"short evidence-based reason"}}
or, once the evidence is sufficient:
{{"action":"report","detected_defects":[{{"defect_type":"...","affected_control":"...","description":"...","likely_root_cause":"...","confidence":0.0}}],"suggested_repairs":["..."]}}

A shape key with zero affected vertices cannot deform its mesh. Shape keys on different objects or
different data paths are not driver conflicts. Compare left/right deformation direction and
magnitude. Use relative_displacement only for clear owner-level outliers. Prefer another tool over
an uncertain report. Before reporting, audit every deformation entry for: zero affected vertices,
opposite vertical directions in named left/right pairs, and displacement more than twice the typical
value for other controls on the same owner. Include every issue directly supported by those checks.
Keep reasons and findings concise."""


def _forced_report_prompt(observations: dict[str, Any]) -> str:
    return f"""Produce the final Blender rig diagnosis from the collected evidence below.
Do not invent missing evidence. Return JSON only with this shape:
{{"action":"report","detected_defects":[{{"defect_type":"...","affected_control":"...","description":"...","likely_root_cause":"...","confidence":0.0}}],"suggested_repairs":["..."]}}

Audit every deformation entry for zero affected vertices, opposite vertical directions in named
left/right pairs, and displacement more than twice the typical value for the same owner.

Evidence: {json.dumps(observations, sort_keys=True)}"""


def analyze_rig_agent(
    source: Path,
    config: BaselineConfig,
    tool_runner: ToolRunner,
    on_action: ActionCallback | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run a bounded observe/select-tool/evaluate loop over an isolated rig copy."""
    client = create_model_client(config)
    observations: dict[str, Any] = {}
    used_tools: list[str] = []
    trajectory: list[dict[str, Any]] = []
    model_calls = 0
    input_tokens = 0
    output_tokens = 0
    report: dict[str, Any] | None = None
    required_evidence = ("structural_details", "shape_key_deformation_summary")

    def record(event: dict[str, Any]) -> None:
        trajectory.append(event)
        if on_action:
            on_action(event)

    for _ in range(config.max_tool_calls + 1):
        response = client.generate(_agent_prompt(observations, used_tools))
        model_calls += 1
        input_tokens += response.input_tokens or 0
        output_tokens += response.output_tokens or 0
        action = _parse_json(response.text)
        if action.get("action") == "report":
            missing = next((tool for tool in required_evidence if tool not in used_tools), None)
            if missing is not None:
                record({
                    "type": "decision",
                    "action": "use_tool",
                    "tool": missing,
                    "summary": "Required deterministic evidence before final report",
                })
                value = tool_runner(source, missing)
                observations[AGENT_TOOLS[missing]] = value
                used_tools.append(missing)
                record({
                    "type": "tool_result",
                    "tool": missing,
                    "summary": f"Stored {AGENT_TOOLS[missing]}",
                })
                continue
            report = _validate_report(action)
            record({"type": "decision", "action": "report", "summary": "Diagnosis complete"})
            break
        tool = action.get("tool")
        if action.get("action") != "use_tool" or tool not in AGENT_TOOLS:
            record({"type": "rejected_action", "summary": f"Rejected unavailable tool: {tool!r}"})
            continue
        if tool in used_tools:
            record({
                "type": "rejected_action",
                "tool": tool,
                "summary": "Rejected repeated tool call",
            })
            continue
        if len(used_tools) >= config.max_tool_calls:
            break
        reason = str(action.get("reason", "Inspecting additional Blender state"))[:240]
        record({"type": "decision", "action": "use_tool", "tool": tool, "summary": reason})
        value = tool_runner(source, tool)
        observations[AGENT_TOOLS[tool]] = value
        used_tools.append(tool)
        record({"type": "tool_result", "tool": tool, "summary": f"Stored {AGENT_TOOLS[tool]}"})

    for missing in required_evidence:
        if missing in used_tools:
            continue
        record({
            "type": "decision",
            "action": "use_tool",
            "tool": missing,
            "summary": "Required deterministic evidence before forced report",
        })
        value = tool_runner(source, missing)
        observations[AGENT_TOOLS[missing]] = value
        used_tools.append(missing)
        record({
            "type": "tool_result",
            "tool": missing,
            "summary": f"Stored {AGENT_TOOLS[missing]}",
        })

    if report is None:
        response = client.generate(_forced_report_prompt(observations))
        model_calls += 1
        input_tokens += response.input_tokens or 0
        output_tokens += response.output_tokens or 0
        report = _validate_report(_parse_json(response.text))
        record({"type": "decision", "action": "report", "summary": "Tool limit reached"})

    report = _remove_unsupported_driver_conflicts(report, observations)
    report = _add_structural_findings(report, observations)
    report.pop("action", None)
    return {
        **observations,
        **report,
        "findings": report["detected_defects"],
        "trajectory": trajectory,
    }, {
        "model_calls": model_calls,
        "tool_calls": len(used_tools),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "model": litellm_model_name(config),
        "provider": litellm_model_name(config).split("/", 1)[0],
    }
