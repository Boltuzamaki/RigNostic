# RigNostic

Agentic facial-rig diagnostics and repair for Blender.

RigNostic targets character artists and technical artists who receive facial
rigs that look correct at rest but contain broken blinks, reversed controls,
incorrect ranges, muted drivers, or bad constraints. The project is intentionally
developed as measured iterations for an Agentic Workflows Hackathon.

## Current status

Stage 0 is blocked before Blender-dependent implementation and evaluation:
Blender is not installed in the current environment and no LLM credential is
configured. The repository currently provides only tested, non-Blender
infrastructure. It contains no fabricated rigs, results, or claims.

The intended Stage 0 baseline is one general-purpose LLM agent with basic Blender
inspection and control-testing tools, a maximum of 15 tool calls, and a fixed
prompt. It will be evaluated on ten deterministic defective variants of a
synthetic facial rig. No structured RigInventory, specialized discovery phase,
adaptive planner, repair, or multi-agent system belongs to Stage 0.

## Setup and status check

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
export BLENDER_EXECUTABLE=/absolute/path/to/blender
.venv/bin/rignostic doctor
.venv/bin/rignostic blender-version
.venv/bin/python -m pytest
```

See [reproduction instructions](docs/REPRODUCTION.md), [architecture](docs/ARCHITECTURE.md),
and the [evaluation contract](docs/EVALUATION.md).
