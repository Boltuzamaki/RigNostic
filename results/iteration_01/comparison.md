# Baseline vs Iteration 1

| Metric | Baseline | Iteration 1 | Change |
|---|---:|---:|---:|
| Defect detection recall | 18.2% (2/11) | 18.2% (2/11) | 0.0 pp |
| False positives | 4 | 10 | +6 |
| Affected-control accuracy | 66.7% | 50.0% | -16.7 pp |
| Root-cause accuracy | 0.0% | 0.0% | 0.0 pp |
| Average agent actions | 7 | 15 | +8 |
| Average runtime | 3.57 s | 6.06 s | +2.49 s |
| Total runtime | 35.66 s | 60.59 s | +24.93 s |
| Model calls | 10 | 10 | 0 |
| Input tokens | 7,549 | 60,012 | +52,463 |
| Output tokens | 1,087 | 1,948 | +861 |
| Approximate cost | N/A | N/A | N/A |

| Case | Baseline | Iteration 1 | Difference |
|---|---|---|---|
| 01 | PASS | PASS | Both detected the muted left-blink driver. |
| 02 | FAIL | FAIL | Inventory was correct; agent invented a brow issue and missed jaw multiplier. |
| 03 | FAIL | FAIL | Agent noticed cross-wired smiles but emitted a non-matching label. |
| 04 | FAIL | FAIL | Agent noticed funnel range mismatch but emitted a non-matching label. |
| 05 | FAIL | FAIL | Constraint asymmetry did not match the normalized gold defect. |
| 06 | FAIL | FAIL | Reversed jaw direction remained structurally invisible. |
| 07 | FAIL | FAIL | Dependencies were followed but the wrong affected control was named. |
| 08 | FAIL | FAIL | Geometry-only excessive deformation remained invisible. |
| 09 | FAIL | FAIL | Two false constraint findings; no interaction testing exists. |
| 10 | FAIL | FAIL | Both found one of two defects; Iteration 1 added a non-match. |

Decision: **REVISE**. Inventory was correct, but its full presentation increased noise, false
positives, runtime, and tokens without improving formal recall. Do not proceed to Iteration 2.
