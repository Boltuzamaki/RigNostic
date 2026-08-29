# Reproduction

## Current prerequisites

- Python 3.11 or newer (development environment: Python 3.14.4)
- Blender 4.3 LTS (pinned target; not installed in the current environment)
- An OpenAI API key for the configured baseline model (not currently available)

Blender 4.3 LTS is selected as the stable target for Stage 0. Its exact patch
version cannot be recorded until an executable is installed and tested.

## Install the Python project

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
```

## Configure and verify Blender

Install Blender 4.3 LTS from the official Blender distribution, then either put
it on `PATH` or configure it without changing global `PATH`:

```bash
export BLENDER_EXECUTABLE=/absolute/path/to/blender
.venv/bin/rignostic doctor
.venv/bin/rignostic blender-version
```

The second command invokes `blender --background` and prints Blender's real
output. It has not succeeded in this environment because Blender is absent.

## Run infrastructure tests

```bash
.venv/bin/python -m pytest
```

Commands for generating the rig and cases, running the baseline, and evaluating
it are intentionally not documented yet because those commands do not exist or
work until the Blender and model prerequisites are available.
