# Representative Codex prompts

Codex was the coding agent used to build, audit, test, document, and package
RigNostic. This file discloses representative user-authored prompts available
from the final submission-preparation session. It does not claim to be a private
chain-of-thought log or a complete export of earlier sessions that is not
available in this repository.

## Submission audit and packaging prompt

The user asked Codex to prepare the required submission package, including:

> Complete project code; baseline and final implementations; benchmark and
> evaluation code; tests; agent prompts/instructions; synthetic Blender-rig
> scripts; no credentials; a complete README; mandatory improvement changelog;
> exact reproduction commands; meaningful tests; agent trajectories; benchmark
> evidence; a video under five minutes; repository/archive preparation; and a
> final qualification checklist.

The prompt also emphasized that reproducibility is a qualification gate and
asked Codex to prioritize a clean clone-and-run path over additional polish.

## Judge-facing folder prompt

> create a seperate folder for all requirements

Outcome: Codex added `submission/` as the judge-facing index with a requirement
map, agent/tool disclosure, checklist, video guidance, and archive tooling.

## Video-caption prompt

> '/home/boltuzamaki/Downloads/timelaspe.mp4' can we add srt ?

Outcome: Codex transcribed and corrected English captions, removed inappropriate
wording, verified a 4:54.961 duration, and produced a subtitle-enabled MP4 while
preserving the original video.

## Complete delivery-folder prompt

> create a final folder which consist of evrything that needed to submit so that
> I can zip and submit it

Outcome: Codex assembled a local `final_submission/` bundle containing the clean
repository, video, SRT, checksums, setup note, and artifact manifest. That large
local bundle is intentionally ignored by Git; its source files remain in their
canonical repository locations.

## Prompt-and-trace verification prompt

> what abot other things improvement changelog code agent prompt and traces ?

Outcome: Codex verified all canonical paths and added a top-level artifact
manifest to the local delivery bundle.

## Final verification prompt

> okay checklist done ?

Outcome: Codex checked the public repository, created a fresh HTTPS clone,
installed Python and Node dependencies, ran 46 passing tests with one opt-in live
test skipped, built the frontend, and identified that the prepared local changes
still needed to be committed and pushed.

## Observable coding-agent trace

The evidence above maps each instruction to its outcome. Additional observable
evidence is available in Git history and the committed changed files. Product
agent traces are separate and live under `trajectories/` and `results/*/*/trajectory.jsonl`.
No hidden reasoning or fabricated historical prompt is included.
