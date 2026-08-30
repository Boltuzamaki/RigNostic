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

A guarded reference-guided repair pipeline is now available. It dry-runs by default, requires an
explicit trusted reference, never overwrites the input, and verifies an applied repair before
publishing the output. This is a deterministic healing path, not yet an autonomous model-driven
repair system.

The intended Stage 0 baseline is one general-purpose LLM agent with basic Blender
inspection and control-testing tools, a maximum of 15 tool calls, and a fixed
prompt. It will be evaluated on ten deterministic defective variants of a
synthetic facial rig. No structured RigInventory, specialized discovery phase,
adaptive planner, repair, or multi-agent system belongs to Stage 0.

Model calls use the LiteLLM Python SDK. Gemini remains the default with
`gemini-3.5-flash-lite`. Set `RIGNOSTIC_MODEL` to a LiteLLM model name such as
`openai/gpt-5-mini`, `anthropic/claude-sonnet-4-5`, `openrouter/...`, or
`ollama/...` to use another provider. Copy `.env.example` to `.env`, add the
provider API key, and restart the application.

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

## Guarded repair

Review a repair plan without changing a file:

```bash
uv run rignostic repair broken.blend --reference trusted_clean.blend
```

Apply the plan to a new file only after review:

```bash
uv run rignostic repair broken.blend --reference trusted_clean.blend \
  --apply --output healed.blend
```

The pipeline currently restores matching driver state, expressions and variable targets; shape-key
ranges and coordinates; and constraint mute/influence values. A failed post-repair comparison does
not publish the temporary output.

See [reproduction instructions](docs/REPRODUCTION.md), [architecture](docs/ARCHITECTURE.md),
and the [evaluation contract](docs/EVALUATION.md).

## Local web interface

The Flask/Jinja interface uses locally built Tailwind CSS and vanilla JavaScript:

```bash
docker compose up -d postgres
npm install
npm run build
uv run python -m rignostic.web
```

For the complete containerized development environment, use:

```bash
docker compose up --build app
```

The app is available at `http://127.0.0.1:5000`. The repository is bind-mounted into `/app`, while
named volumes preserve the container virtual environment, `node_modules`, PostgreSQL data, and run
artifacts. Flask reloads Python and template changes automatically; Tailwind and both Three.js
bundles run in watch mode, so frontend source changes are rebuilt inside the running container. Run
`docker compose build app` again only after changing dependencies or the Dockerfile.

To run the production image locally instead:

```bash
docker build --target production -t rignostic:local .
docker run --rm -p 5000:5000 --env-file .env \
  -e DATABASE_URL=postgresql+psycopg://rignostic:rignostic@host.docker.internal:5432/rignostic \
  rignostic:local
```

Open `http://127.0.0.1:5000`. Uploaded `.blend` files are isolated under the
ignored Flask instance directory and limited to 250 MB.

Accounts, password hashes, run ownership, progress events, status, and analysis results are stored in
PostgreSQL. The default local connection is
`postgresql+psycopg://rignostic:rignostic@127.0.0.1:5432/rignostic`; override it with
`DATABASE_URL`. Uploaded `.blend` files and generated binary viewer assets remain in isolated run
directories, with their locations recorded in PostgreSQL.

## Demo rigs

Ready-to-upload clean/broken examples are in `demo_asset/`:

- `rignostic_demo_face_v2.blend` and `rignostic_demo_face_v2_broken.blend`
- `rignostic_demo_full_body_v1.blend` and `rignostic_demo_full_body_v1_broken.blend`

Both pairs expose the same eight facial controls. The broken versions contain a frozen left blink,
a reversed right smile, and an excessive jaw range. The mouth uses separate lip rims, a dark inner
mouth, and visible teeth so jaw and smile behavior remains readable in previews and comparisons.

Regenerate the full-body clean asset with:

```bash
.tools/blender/blender --background --python demo_asset/create_demo_full_body.py -- \
  --output demo_asset/rignostic_demo_full_body_v1.blend
```

The **Repair + Compare** page accepts a broken rig and trusted matching reference, runs the guarded
healing pipeline, and presents synchronized before/after 3D viewers. Shared morph sliders drive both
models at once, repaired controls are prioritized, nonvisual property changes appear in a diff table,
and the verified healed `.blend` can be downloaded.
