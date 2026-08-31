<div align="center">

# RigNostic

**Find broken Blender facial controls before animation starts.**

RigNostic opens a sandboxed copy of a `.blend` file, exercises facial controls,
records Blender evidence, proposes supported repairs, and repeats the failed test.

The diagnostic agent selects each Blender inspection from a fixed allowlist based
on the evidence collected so far. Every selection, tool result, and final report
is stored with the run.

[Quick start](#quick-start) · [How it works](#how-it-works) · [Demo rigs](#demo-rigs) · [Documentation](#documentation)

</div>

![RigNostic landing page](docs/assets/readme/landing-page.png)

## What it does

Facial rigs can look correct in a neutral pose while hiding broken drivers,
empty shape keys, reversed controls, bad limits, or asymmetric deformation.
RigNostic runs those checks before an animator has to find the problem manually.

| Stage | What RigNostic records |
| --- | --- |
| Inspect | Controls, shape keys, drivers, constraints, and object ownership |
| Test | Control values and the resulting deformation |
| Diagnose | Failed control, likely cause, supporting Blender data, and confidence |
| Repair | The exact change written to a new sandboxed copy |
| Retest | The original failing test replayed against the repaired rig |
| Compare | Synchronized before/after 3D viewers and a property diff |

The uploaded file is never overwritten. A repaired file is published only after
the verification step passes.

## Repair loop

The animation below is captured from the real Three.js landing-page component.
It follows a broken left blink from inspection through repair and verification.

<div align="center">
  <img src="docs/assets/readme/diagnostic-repair-loop.gif" alt="RigNostic inspecting, repairing, and verifying a broken eyelid control" width="1040">
</div>

## Quick start

### Docker Compose

```bash
cp .env.example .env
# Add GEMINI_API_KEY to .env
docker compose up --build
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

PostgreSQL, Blender 4.5.13 LTS, Python dependencies, frontend dependencies, and
the Flask development server are included in the Compose setup. Source files are
bind-mounted, so Python, Jinja, CSS, and JavaScript edits reload without rebuilding
the image. Rebuild only after changing dependencies or the Dockerfile.

### Run without Docker

```bash
uv sync --dev
npm install
npm run build
export BLENDER_EXECUTABLE=/absolute/path/to/blender
docker compose up -d postgres
uv run python -m rignostic.web
```

## How it works

![RigNostic inspection workflow](docs/assets/readme/inspection-workflow.png)

1. The web app stores the uploaded rig under an isolated run directory.
2. Blender opens the copy in a headless subprocess.
3. Inspection tools enumerate controls, drivers, constraints, and shape keys.
4. The analysis process chooses controls to test and records their response.
5. Findings are stored with their affected controls and supporting data.
6. Supported repairs are applied to another copy and the failed checks are rerun.
7. The user compares both versions and downloads the verified result.

## Current checks

| Area | Examples | State |
| --- | --- | --- |
| Drivers | Muted driver, multiplier, reversed direction, wrong target | Supported |
| Shape keys | Zero affected vertices, asymmetric movement, excessive range | Supported |
| Constraints | Muted constraint, influence, malformed limits | Supported |
| Control mapping | Swapped sides and unexpected targets | Review may be required |
| Combined controls | Pairwise and higher-order interactions | Planned |

Automatic repair is intentionally narrower than detection. The current repair
path handles high-confidence changes that can be checked deterministically, such
as restoring deformation from a matching counterpart and correcting known driver,
shape-key, or constraint properties.

## Model providers

Model calls go through the LiteLLM Python SDK. Gemini is the default, while the
rest of the analysis pipeline remains provider-independent.

```dotenv
# Default Gemini configuration
GEMINI_API_KEY=...
RIGNOSTIC_MODEL=gemini-3.5-flash-lite

# Other LiteLLM model names also work
RIGNOSTIC_MODEL=openai/gpt-5-mini
RIGNOSTIC_MODEL=anthropic/claude-sonnet-4-5
RIGNOSTIC_MODEL=openrouter/...
RIGNOSTIC_MODEL=ollama/...
```

Add the API key required by the selected provider and restart the application.

## Demo rigs

Ready-to-upload fixtures are included in [`demo_asset`](demo_asset):

| Rig | Clean | Broken |
| --- | --- | --- |
| Face | `rignostic_demo_face_v2.blend` | `rignostic_demo_face_v2_broken.blend` |
| Full body | `rignostic_demo_full_body_v1.blend` | `rignostic_demo_full_body_v1_broken.blend` |

The broken fixtures contain controlled defects including a frozen left blink,
a reversed right smile, and excessive jaw movement. The analysis process does
not receive the fixture ground truth in its prompt.

Regenerate the full-body fixture with:

```bash
.tools/blender/blender --background --python demo_asset/create_demo_full_body.py -- \
  --output demo_asset/rignostic_demo_full_body_v1.blend
```

## Command-line repair

Preview a repair plan without changing the file:

```bash
uv run rignostic repair broken.blend --reference trusted_clean.blend
```

Apply the reviewed plan to a new file:

```bash
uv run rignostic repair broken.blend --reference trusted_clean.blend \
  --apply --output repaired.blend
```

The web analysis flow can also infer supported repairs without requiring a clean
reference. The reference-guided CLI remains available for deterministic fixture
comparison and controlled repair work.

## Development checks

```bash
uv run rignostic doctor
uv run rignostic blender-version
uv run ruff check .
uv run pytest
```

Current automated test result: **46 passed, 1 skipped**. The skipped test is the
opt-in live model call, which can incur provider usage.

## Evaluation status

The checked-in synthetic benchmark contains ten controlled broken rigs. The
recorded Stage 0 result detected 2 of 11 defects with 4 false positives. Those
results are retained under [`results/baseline`](results/baseline) and
[`trajectories/baseline`](trajectories/baseline); they are not replaced with
marketing estimates.

## Stack

- Flask, Jinja2, and Tailwind CSS
- Three.js rig and comparison viewers
- Blender 4.5.13 LTS headless subprocesses
- PostgreSQL with Flask-SQLAlchemy
- LiteLLM model adapter, with Gemini as the default
- Docker Compose development environment

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Reproduction instructions](docs/REPRODUCTION.md)
- [Evaluation contract](docs/EVALUATION.md)
- [Improvement changelog](docs/IMPROVEMENT_CHANGELOG.md)
- [Hackathon demo script](docs/DEMO_SCRIPT.md)

---

Built for the Agentic Workflows Hackathon.
