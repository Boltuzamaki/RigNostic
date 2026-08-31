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

It reports build hash `daeeeca98fb0`, successfully executes Python, and saves
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
output. Both commands were verified with Blender 4.5.13 LTS.

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

## Run the local web interface

```bash
npm install
npm run build
uv run python -m rignostic.web
```

Then open `http://127.0.0.1:5000`. For Flask's development command, use:

```bash
uv run flask --app rignostic.web run
```

This is the final/advanced solution. Upload a `.blend` file to run the bounded
adaptive diagnostic agent. From a completed run, explicitly choose **Repair this
run** to apply supported changes to a sandboxed copy, retest them, compare both
versions, and download the verified output. Run directories default to
`src/instance/runs/` locally and `/data/runs/` in Compose.

For the most reproducible clean-machine path, use Docker instead:

```bash
cp .env.example .env
# Fill GEMINI_API_KEY in .env
docker compose up --build
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

The validator must print `RIGNOSTIC_BENCHMARK_VALID=True`.

## Run and evaluate the Stage 0 baseline

```bash
uv run rignostic baseline-run
uv run rignostic baseline-evaluate
```

Or run both steps:

```bash
uv run rignostic baseline-all
```

Gold labels are opened only by `baseline-evaluate`, after all agent runs finish.

## Run Iteration 1

Build one inventory:

```bash
uv run rignostic inspect benchmark/cases/case_01/rig.blend \
  --output results/iteration_01/case_01/inventory.json
```

Run and evaluate the unchanged benchmark:

```bash
uv run rignostic iteration-01-run
uv run rignostic iteration-01-evaluate
# or both
uv run rignostic iteration-01-all
```

The agent never receives `gold.json`; only the evaluator reads it afterward.

## Expected outputs, runtime, and cost

- Benchmark generation writes ten `benchmark/cases/case_*/rig.blend` fixtures,
  their gold labels, and `benchmark/validation_report.json`.
- Baseline evaluation writes `results/baseline/results.json` and `summary.md`;
  the frozen recorded run took 35.66 seconds and 10 model calls.
- Iteration 1 writes inventories, results, metrics, and JSONL traces under
  `results/iteration_01/`; the recorded run took 60.59 seconds.
- A final web run writes `result.json`, `trajectory.jsonl`, a preview, and viewer
  asset under its isolated run directory. Runtime depends on selected tools and
  Blender startup speed; the loop is capped at 15 tool calls.
- Model cost depends on the configured LiteLLM provider. The committed result
  records include token counts, but the historical provider cost was not
  measured. Tests and Blender generation do not make model calls. The live model
  smoke test and agent runs can incur provider charges.

## Create the clean archive

After committing the final state:

```bash
bash scripts/create_submission_archive.sh
unzip -l dist/rignostic-submission.zip | head
```

`git archive` includes tracked submission material and excludes `.env`, local
databases, caches, downloaded toolchains, dependencies, and other ignored files.
