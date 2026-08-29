# Reproduction

## Current prerequisites

- Python 3.11 or newer (development environment: Python 3.14.4)
- uv 0.11 or newer
- Blender 4.5.13 LTS
- An OpenAI API key for the configured baseline model (not currently available)

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

Install the repository hook once per clone:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Commands for generating the rig and cases, running the baseline, and evaluating
it are intentionally not documented yet because those commands do not exist or
work until the Blender and model prerequisites are available.
