# Agent and coding-tool disclosure

## Product agent

RigNostic uses one bounded diagnostic agent. Its fixed Stage 0 instruction is
defined in `src/rignostic/baseline/prompt.py`. The final observe/select/evaluate
instructions, tool allowlist, rejection rules, deterministic evidence guard,
and forced-report instruction are in `src/rignostic/baseline/agent.py`.

The agent may only select read-only Blender inspections from the allowlist. It
does not receive benchmark gold labels and does not directly mutate `.blend`
files. Repair is performed by deterministic, confidence-gated code against a
sandboxed copy and is published only after verification.

Representative machine-readable traces are committed under:

- `trajectories/baseline/`: frozen Stage 0 observations, calls, results, and reports.
- `results/iteration_01/*/trajectory.jsonl`: discovery and classification decisions.
- `trajectories/final/`: final adaptive tool decisions, results, and final report.
- `results/final_benchmark/case_*/trajectory.jsonl`: formal final ten-case traces.

Human checkpoints are explicit: upload/select the source rig, request repair,
review the before/after comparison, and choose whether to download the verified
copy. Automatic repair is never triggered merely by uploading a rig.

## Coding agent

OpenAI Codex was used to scaffold, implement, test, review, and document this
repository. It was used through terminal/file-editing tools and Git-aware code
review. The repository history and the staged improvement changelog show the
resulting progression. Codex did not supply benchmark gold labels to the product
agent, and no private chain-of-thought is claimed or included. Submitted traces
record the product agent's observable instructions, actions, tool results, and
decisions required to reproduce behavior.

Representative user-authored Codex instructions and their observable outcomes
are recorded in `submission/CODEX_PROMPTS.md`. This is intentionally labeled as
a representative record rather than a fabricated complete transcript.
The machine-readable representative coding-agent trajectory is committed at
`trajectories/codex/submission_packaging.jsonl`; it records instructions,
observations, tool calls, results, retry feedback, human checkpoints, and the
final outcome without private hidden reasoning.

External tools used: Blender 4.5.13 LTS, Python/uv, LiteLLM with Gemini, Flask,
PostgreSQL, Node/npm, Tailwind CSS, Three.js, Docker Compose, Git, Ruff, Pytest,
and FFmpeg for the demo video's subtitle track.
