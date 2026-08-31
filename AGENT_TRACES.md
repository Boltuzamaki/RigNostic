# Agent prompts and trajectories

This page is the judge-facing entry point for RigNostic's agent-use evidence.

## Coding-agent evidence

- [Coding-agent prompts](submission/CODEX_PROMPTS.md)
- [Agent/tool disclosure](submission/AGENT_USE.md)
- [Representative Codex trajectory](trajectories/codex/submission_packaging.jsonl)

## RigNostic product-agent evidence

- [Stage 0 baseline trajectories](trajectories/baseline/)
- [Representative final trajectory](trajectories/final/demo_face.jsonl)
- [Formal final benchmark traces](results/final_benchmark/)

The formal benchmark directory contains one `trajectory.jsonl` per fixed case,
alongside the corresponding evidence and agent result. Each trajectory captures
the instruction, observations, tool calls and results, subsequent decisions,
retries where applicable, and final report. Human checkpoints and the complete
tool disclosure are described in `submission/AGENT_USE.md`.

No API keys or private credentials are contained in these files.
