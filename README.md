# RigNostic

Agentic facial-rig diagnostics and repair for Blender.

RigNostic targets character artists and technical artists who receive facial
rigs that look correct at rest but contain broken blinks, reversed controls,
incorrect ranges, muted drivers, or bad constraints. The project is intentionally
developed as measured iterations for an Agentic Workflows Hackathon.

## Current status

Blender 4.5.13 LTS is installed project-locally and configured for headless use.
Stage 0 benchmark development can proceed, but baseline model access has not yet
been verified. The repository contains no fabricated results or claims.

The intended Stage 0 baseline is one general-purpose LLM agent with basic Blender
inspection and control-testing tools, a maximum of 15 tool calls, and a fixed
prompt. It will be evaluated on ten deterministic defective variants of a
synthetic facial rig. No structured RigInventory, specialized discovery phase,
adaptive planner, repair, or multi-agent system belongs to Stage 0.

## Setup and status check

```bash
uv sync --dev
uv run pre-commit install
export BLENDER_EXECUTABLE=/absolute/path/to/blender
uv run rignostic doctor
uv run rignostic blender-version
uv run pre-commit run --all-files
uv run ruff check .
uv run pytest
```

See [reproduction instructions](docs/REPRODUCTION.md), [architecture](docs/ARCHITECTURE.md),
and the [evaluation contract](docs/EVALUATION.md).
