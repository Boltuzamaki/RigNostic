# Final representative result

The final bounded diagnostic agent was run on
`demo_asset/rignostic_demo_face_v2_broken.blend` on 2026-08-31 using Blender
4.5.13 LTS and `gemini/gemini-3.5-flash-lite`.

- Injected demo defects detected: **3/3**
- Findings: empty `eyeBlink_L`, reversed `mouthSmile_R`, excessive `jawOpen`
- Model calls: 7
- Blender inspection tool calls: 6
- Tokens: 6,089 input / 370 output
- Agent wall time before preview/export: approximately 11 seconds
- Provider cost: not measured

This is representative final-workflow evidence, not a rerun of the fixed ten-case
benchmark. Formal cross-iteration claims remain the committed Stage 0 and
Iteration 1 results. The raw result and trace are in `results/final/demo_face/`;
the judge-facing trace with instruction and human checkpoints is
`trajectories/final/demo_face.jsonl`.
