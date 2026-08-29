# Architecture

## Stage 0 target

```text
.blend file
     |
     v
Basic Blender tools
     |
     v
One general-purpose LLM agent
     |
     v
Structured defect report
     |
     v
Deterministic evaluator
```

Stage 0 contains configuration, a headless process runner, a deterministic
synthetic rig and ten-case benchmark, coarse Blender tools, one fixed-prompt
Gemini agent, result schemas, deterministic matching, and trajectory logging.
The ten-case baseline evaluation is recorded and frozen.

Stage 0 does not contain RigInventory, semantic control mapping, adaptive test
planning, pairwise testing, repair, rollback, visual verification, or regression
loops.

## Web boundary

Flask routes validate requests and delegate analysis to `AnalysisService`. The
service runs existing coarse Blender tools, a local preview/GLB export, and the
same Stage 0 model client in a background thread, then writes run-local JSON and
JSONL artifacts. Routes never import `bpy` or manipulate rigs. Jinja templates
and locally bundled Tailwind/Three.js assets remain inside `rignostic.web` while
backend services remain reusable by CLI commands.
