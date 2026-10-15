# Model Card — FD001 survival baseline (weibull_aft)

Status: EVIDENCE / IMPLEMENTED — **not VERIFIED, not PROMOTED**. Governance: SPEC-001, INTENT-446E2407EF97.

## Intended use

Baseline time-to-event evidence on NASA C-MAPSS FD001 to support later task-scoped work on cost-aware maintenance decisions. Outputs are **not a production recommendation**.

## Data boundary

- Source: DEC-003 archive declared in `data/raw/MANIFEST.json`; local extraction only (DEC-004).
- Event: end of recorded run-to-failure trajectory (train). Test trajectories are right-censored; RUL truth is evaluation-only.
- Covariates: early-life means and slopes over the first 20 cycles only; later cycles are excluded (TASK-007). Constant columns dropped.
- Split: grouped by `unit_id` (no unit in both partitions).

## Models

- Weibull: shape β = 4.6006, scale λ = 222.9760, regime wear_out.
- Cox PH on 8 covariates; PH check schoenfeld_rank → violated.
- Selected: **weibull_aft** — PH assumption violated for ['sensor_6_early'] (p <= 0.05); fell back to Weibull AFT.

## Metrics (held-out units)

- C-index = 0.6667 (primary, DEC-011)
- IBS = 0.0940 over horizons ['50', '100', '150', '200', '250'] (DEC-012)

## Limitations

- Slope covariates use only the first early_window cycles (HG-003 = B / TASK-007). Cycles after that window, including the failure time, do not enter the feature. Early-life drift on FD001 is often weak, so concordance is expected to be lower than a full-trajectory slope; that lower number is the prognostic score.
- Per-unit summary covariates ignore within-trajectory dynamics; a time-varying (counting-process) Cox model is provided in events.build_long_format but not evaluated here.
- FD001 only (single operating condition, single fault mode). Generalisation to FD002–FD004 is out of scope (SPEC-001 §2).
- Cost parameters C_p, C_f are illustrative (DEC-013); t* is baseline evidence, not a production recommendation.
- Weibull parametric baseline is unconditional (no covariates); it informs the failure regime and the cost policy, not unit-level ranking.
- Censored-unit failure probabilities are reported from cycle 0; a decision surface must condition on the already-observed cycle (S(t+c)/S(c)). Concordance versus RUL truth is a separate evaluation and is reported in censored_scoring.

## Open decisions (verbatim from SPEC-001 §6)

- None.

## Reproduction

```bash
.venv/Scripts/python -m pm_survival run --raw-dir data/raw/cmapss
```
