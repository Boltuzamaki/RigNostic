# RigNostic

Agentic facial-rig diagnostics and repair for Blender.

RigNostic targets character artists and technical artists who receive facial
rigs that look correct at rest but contain broken blinks, reversed controls,
incorrect ranges, muted drivers, or bad constraints. The project is intentionally
developed as measured iterations for an Agentic Workflows Hackathon.

## Current status

Blender 4.5.13 LTS is installed project-locally and configured for headless use.
The synthetic reference rig and ten defective variants pass deterministic
validation. The recorded Stage 0 baseline detected 2 of 11 defects (18.2%
recall) with 4 false positives. Complete results and trajectories are checked in
under `results/baseline` and `trajectories/baseline`.

Iteration 1 Structured Rig Discovery has also been evaluated. It produced deterministic inventories
and dependency graphs, but formal recall remained 18.2% while false positives increased to 10. The
evidence-based decision is **REVISE**; Iteration 2 has not started.

The intended Stage 0 baseline is one general-purpose LLM agent with basic Blender
inspection and control-testing tools, a maximum of 15 tool calls, and a fixed
prompt. It will be evaluated on ten deterministic defective variants of a
synthetic facial rig. No structured RigInventory, specialized discovery phase,
adaptive planner, repair, or multi-agent system belongs to Stage 0.

Gemini is the default provider using `gemini-3.5-flash-lite`. OpenAI remains
supported through the same provider factory. Copy `.env.example` to `.env` and
set `GEMINI_API_KEY`; the application loads `.env` automatically.

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

## Local web interface

The Flask/Jinja interface uses locally built Tailwind CSS and vanilla JavaScript:

```bash
npm install
npm run build
uv run python -m rignostic.web
```

Open `http://127.0.0.1:5000`. Uploaded `.blend` files are isolated under the
ignored Flask instance directory and limited to 250 MB.
