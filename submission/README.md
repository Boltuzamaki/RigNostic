# RigNostic submission package

This folder is the judge-facing index for the complete repository. The archive
created by `scripts/create_submission_archive.sh` contains this folder and every
tracked source, fixture, result, test, prompt, and trajectory listed below.

## Requirement map

| Requirement | Canonical location |
| --- | --- |
| Complete project code | `src/`, `frontend/`, `Dockerfile`, `compose.yaml` |
| Frozen baseline | `src/rignostic/baseline/` |
| Final agent workflow | `src/rignostic/services/analysis.py`, `src/rignostic/repair/` |
| Agent prompts/instructions | `src/rignostic/baseline/prompt.py`, `src/rignostic/baseline/agent.py` |
| Benchmark and evaluator | `benchmark/`, `src/rignostic/evaluation/` |
| Synthetic-rig generators | `benchmark/scripts/`, `demo_asset/create_demo_*.py` |
| Tests | `tests/` |
| Baseline evidence | `results/baseline/`, `trajectories/baseline/` |
| Structured-discovery evidence | `results/iteration_01/` |
| Final representative evidence | `results/final/`, `trajectories/final/` |
| Architecture | `docs/ARCHITECTURE.md` |
| Improvement changelog | `docs/IMPROVEMENT_CHANGELOG.md` |
| Clean-machine commands | `docs/REPRODUCTION.md` |
| Evaluation contract | `docs/EVALUATION.md` |
| Pre-existing-work disclosure | `docs/PRE_EXISTING_WORK.md` |
| Coding-agent disclosure | `submission/AGENT_USE.md` |
| Representative Codex prompts | `submission/CODEX_PROMPTS.md` |
| Representative Codex trajectory | `trajectories/codex/submission_packaging.jsonl` |
| Video plan | `submission/VIDEO.md` |
| Final qualification checklist | `submission/CHECKLIST.md` |

## Fast judge path

```bash
cp .env.example .env
# Set GEMINI_API_KEY in .env
docker compose up --build
```

Open `http://127.0.0.1:5000`. For deterministic verification without a model
call, follow `docs/REPRODUCTION.md` and run the committed test/evaluation checks.

Repository: https://github.com/Boltuzamaki/RigNostic
