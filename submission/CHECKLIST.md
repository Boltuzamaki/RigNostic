# Final submission checklist

Verified locally on 2026-08-31:

- [x] Complete source, baseline, final implementation, benchmark, prompts, tests, and rig generators tracked
- [x] README, architecture, changelog, reproduction, evaluation, and pre-existing-work documents present
- [x] Fixed benchmark rigs, gold labels, validation report, and recorded results committed
- [x] Baseline and structured-discovery trajectories committed
- [x] Representative final adaptive trajectory committed
- [x] Formal final benchmark committed: 11/11 recall and 0 false positives
- [x] Coding-agent and external-tool use disclosed
- [x] Representative Codex prompts and outcomes disclosed
- [x] Representative machine-readable Codex trajectory disclosed
- [x] `uv run ruff check .` passes
- [x] `uv run pytest -q` passes: 46 passed, 1 opt-in live-model test skipped
- [x] `npm run build` passes
- [x] Blender reports 4.5.13 LTS and the configured doctor/version commands pass
- [x] Repository text and generated SRT scanned for inappropriate wording
- [x] `.env` and local credentials ignored; `.env.example` contains placeholders only
- [x] Demo video duration is 294.961 seconds (4:54.961)
- [x] Standalone English SRT and subtitle-enabled MP4 prepared

External actions that cannot be completed from repository code:

- [x] Confirm the public GitHub URL is accessible while signed out (HTTP 200 verified)
- [x] Push the final repository package to GitHub (`168b81c` verified remotely)
- [ ] Upload the final video and confirm platform playback/subtitles
- [ ] Upload the clean ZIP if the form requests it
- [x] Re-run install, tests, and frontend build from a fresh public GitHub clone
  (46 passed, 1 skipped; npm build passed)

The pushed public repository now contains `submission/`, `results/final/`, and
`trajectories/final/`.
