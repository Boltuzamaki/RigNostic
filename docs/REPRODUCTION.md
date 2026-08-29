# Reproduction

## Current prerequisites

- Python 3.11 or newer (development environment: Python 3.14.4)
- uv 0.11 or newer
- Blender 4.5.13 LTS
- A Gemini or OpenAI API key for the configured baseline model

## Configure the model

The Stage 0 default is Gemini `gemini-3.5-flash-lite` with temperature `0`, a
2,000-token output limit, and at most 15 tool calls. Create the local secret file:

```bash
cp .env.example .env
```

Then set `GEMINI_API_KEY` in `.env`. To use OpenAI instead, set
`RIGNOSTIC_MODEL` to an OpenAI model name and provide `OPENAI_API_KEY`. Provider
selection is automatic from the model name or explicit through
`RIGNOSTIC_PROVIDER=gemini|openai`.

Blender 4.5.13 LTS is pinned for Stage 0. The benchmark development executable is:

```text
/home/boltuzamaki/Work/get_a_job/RigNostic/.tools/blender/blender
```

It reports build hash `daeeeca98fb0` and successfully executes Python and saves
`.blend` files in background mode. The project-relative default is configured as
`.tools/blender/blender`; `BLENDER_EXECUTABLE` overrides it.

## Install the Python project

```bash
uv sync --dev
```

## Configure and verify Blender

Install Blender 4.5.13 LTS from the official Blender distribution, then either put
it on `PATH` or configure it without changing global `PATH`:

```bash
export BLENDER_EXECUTABLE=/absolute/path/to/blender
uv run rignostic doctor
uv run rignostic blender-version
```

The second command invokes `blender --background` and prints Blender's real
output. It has not succeeded in this environment because Blender is absent.

## Run infrastructure tests

```bash
uv run ruff check .
uv run pytest
```

Run the opt-in live model smoke test (one potentially billable API call):

```bash
RIGNOSTIC_RUN_LIVE_MODEL_TESTS=1 \
  uv run pytest tests/integration/test_gemini_api.py -q
```

Install the repository hook once per clone:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## Regenerate and validate the benchmark

```bash
uv run rignostic doctor
.tools/blender/blender --background --factory-startup \
  --python benchmark/scripts/create_reference_rig.py -- \
  --output benchmark/clean_reference/rig.blend
.tools/blender/blender --background \
  --python benchmark/scripts/create_cases.py
.tools/blender/blender --background --factory-startup \
  --python benchmark/scripts/validate_benchmark.py
```

The validator must print `RIGNOSTIC_BENCHMARK_VALID=True`. Baseline run and
evaluation commands are not documented yet because model access is blocked and
the executable agent loop has not been run.
