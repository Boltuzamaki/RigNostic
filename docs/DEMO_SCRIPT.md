# Hackathon demo script

Target length: 4:30 to 4:59 (hard maximum: 5:00).

## Before recording

```bash
docker compose up -d
docker compose ps
```

Confirm both services are healthy and open `http://127.0.0.1:5000` in a clean
browser window. Keep the terminal ready with:

```bash
docker compose logs -f app
```

## Recording sequence

1. **Problem, 15 seconds**
   - Show the landing page.
   - Explain that a neutral facial rig can hide broken controls.
   - Point to the animated inspect, diagnose, repair, and retest sequence.

2. **Start a run, 15 seconds**
   - Sign in and click **Break a Demo Rig**.
   - Explain that the benchmark defects are not included in the model prompt.

3. **Agent loop, 40 seconds**
   - Show the progress bar while it advances.
   - Open the terminal briefly to show different model-selected Blender tools.
   - Return to the run when analysis completes.

4. **Finding, 25 seconds**
   - Open **Findings** and show `eyeBlink_L` with zero affected vertices.
   - Open **Agent trajectory** and show the ordered tool selections and results.
   - Point out the recorded model name and tool/model call counts.

5. **Repair, 35 seconds**
   - Click **Repair this run**.
   - Explain that the model does not directly mutate Blender data.
   - Show the original and repaired 3D viewers.
   - Move the shared blink slider and compare both versions.
   - Show the exact changes table and download the repaired `.blend`.

6. **Close, 20 seconds**
   - Show the architecture diagram or repository README.
   - Mention the sandboxed copies, PostgreSQL history, LiteLLM provider support,
     Docker Compose setup, and deterministic verification gate.

7. **Required evidence, 45 seconds**
   - Show the baseline/final comparison and the committed result files.
   - Name adaptive evidence selection as the biggest improvement.
   - Name the removed full-inventory experiment: it increased false positives
     and input tokens without improving formal recall.
   - Close with the hot take: a control working alone does not make the rig
     valid; interaction behavior and deformation evidence matter.

## Claims to use

- The model chooses the next inspection from a fixed allowlist.
- Every model decision and Blender tool result is logged.
- The original `.blend` is never overwritten.
- Supported repairs are applied by deterministic code to a copy.
- A repaired file is published only after the failing checks pass.

## Claims to avoid

- Do not claim that every Blender rig or defect can be repaired.
- Do not describe the deterministic repair engine as model-generated editing.
- Do not present the historical 18.2% baseline as the current agent-loop result.
- Do not claim combined-control testing; it remains planned.
