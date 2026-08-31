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
service starts a bounded diagnostic loop in a background thread. On each turn,
the model sees the evidence collected so far and either selects one unused tool
from a fixed allowlist or returns the final report. Tool decisions, short reasons,
and results are written to the run trajectory. Repeated or unavailable tools are
rejected, and `max_tool_calls` bounds the loop. Preview and GLB export remain
deterministic post-analysis steps.

Routes never import `bpy` or manipulate rigs. Jinja templates and locally bundled
Tailwind/Three.js assets remain inside `rignostic.web`, while backend services
remain reusable by CLI commands.

```text
Observe collected Blender evidence
              |
              v
      Select allowed tool  <----+
              |                  |
              v                  |
       Run headless Blender      |
              |                  |
              +---- evaluate ----+
              |
              v
       Structured report
```

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

## Reference-free web repair

Completed web analyses can run a narrower confidence-gated repair without a
reference upload. The repair code independently verifies supported structural
defects, writes changes to a temporary copy, reruns those checks, and atomically
publishes the repaired `.blend` only when no supported finding remains. The model
does not directly edit Blender data.

## Final evidence gate

Before accepting a final report, the adaptive workflow always collects detailed
driver/shape-key/constraint structure and deformation summaries. A deterministic
validation layer normalizes only directly supported findings: muted or malformed
drivers, reciprocal swaps, unrelated targets, peer-relative range/constraint
outliers, mirrored deformation anomalies, and combined-control overdeformation.
Model-selected inspections remain adaptive, but unsupported model findings are
not published. This separation reduced the fixed benchmark from 22 false
positives in the rejected trial to zero in the committed final run.
