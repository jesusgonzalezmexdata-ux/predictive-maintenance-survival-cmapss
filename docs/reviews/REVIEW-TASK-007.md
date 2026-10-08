# Review — TASK-007 early-window slopes (HG-003 = B)

Status: **PARTIAL**  
Reviewer: same session as the implementer (`executor != verifier` incomplete)  
Date: 2026-10-08  
Task: `docs/tasks/TASK-007-early-window-slopes.json`

## What changed

`build_survival_table` now fits `<signal>_slope` on cycles `<= early_window` only. A late jump that moved the full-trajectory slope from 1.0 to 45.49 no longer changes the feature (`test_slope_excludes_cycles_after_early_window`).

## Claims

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Slope excludes cycles after the window | SUPPORTED | RED 45.49 ≠ 1.0; GREEN test passes |
| Product tests still pass offline | SUPPORTED | 49 tests OK |
| FD001 evidence regenerated | SUPPORTED | `provenance.slope_window = 20`; model card states first 20 cycles only |
| PH fallback is real | SUPPORTED | `sensor_6_early` p = 0.0397 → selected `weibull_aft` |
| Validation C-index is a remaining-life score without future slope | SUPPORTED as method; number is 0.6667 (was 0.7778) | `reports/eval_FD001.json` |
| Censored units rank by RUL | UNSUPPORTED | concordance vs RUL truth **0.4596** (was 0.8155); below 0.5 |
| Cost \(t^*\) changed | UNSUPPORTED (unchanged, correctly) | still 104.7 from unconditional Weibull |
| Promotion | not claimed | |

## Residual limitation

Early-window summaries on FD001 carry little prognostic signal. The counting-process Cox in `events.build_long_format` is still not the evaluated model. A public claim that this baseline ranks remaining life on censored engines is not supported.

## Verdict

**PARTIAL** — the leakage fix and the republished evidence are in place. The honest score does not support a strong RUL-ranking claim. Not promoted.
