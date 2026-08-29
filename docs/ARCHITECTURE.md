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

The checked-in scaffolding currently contains configuration, a headless process
runner, result schemas, deterministic matching, and trajectory logging. Blender
is unavailable in the development environment, so the Blender tools, synthetic
rig, benchmark, and executable agent loop have not yet been implemented or run.

Stage 0 does not contain RigInventory, semantic control mapping, adaptive test
planning, pairwise testing, repair, rollback, visual verification, or regression
loops.

