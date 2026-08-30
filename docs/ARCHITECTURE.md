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

## Iteration 1 — Structured Rig Discovery

```text
Blender file
    ↓
Deterministic discovery tools
    ↓
Serializable RigInventory
    ↓
One general-purpose agent
    ↓
Same baseline-style inspection
    ↓
Structured defect report
```

Iteration 1 adds a structural map but still has no Dynamic Test Planner, interaction search,
visual verifier, repair engine, rollback, or regression loop.

## Guarded Reference Repair

The first repair capability is deliberately separate from the low-recall diagnostic agent. A user
supplies a defective rig and a trusted clean reference with matching object/control topology. The
pipeline snapshots supported Blender properties, emits a dry-run diff, and only mutates a temporary
copy after explicit `--apply`. It compares the saved copy with the reference and atomically publishes
the requested output only when no supported differences remain. Inputs are never overwritten.

Supported properties are driver mute state, expression and variables; shape-key slider bounds and
coordinates; and constraint mute state and influence. Missing reference topology blocks repair
rather than being created or silently skipped, so this mechanism is restoration from a known-good
rig rather than unrestricted repair.
