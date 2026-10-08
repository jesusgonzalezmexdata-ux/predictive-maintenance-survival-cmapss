# Model Card — FD001 survival baseline (cox)

Status: EVIDENCE / IMPLEMENTED — **not VERIFIED, not PROMOTED**. Governance: SPEC-001, INTENT-446E2407EF97.

## Intended use

Baseline time-to-event evidence on NASA C-MAPSS FD001 to support later task-scoped work on cost-aware maintenance decisions. Outputs are **not a production recommendation**.

## Data boundary

- Source: DEC-003 archive declared in `data/raw/MANIFEST.json`; local extraction only (DEC-004).
- Event: end of recorded run-to-failure trajectory (train). Test trajectories are right-censored; RUL truth is evaluation-only.
- Covariates: early-life means (first 20 cycles) and per-unit slopes of operational settings / sensors; constant columns dropped.
- Split: grouped by `unit_id` (no unit in both partitions).

## Models

- Weibull: shape β = 4.6006, scale λ = 222.9760, regime wear_out.
- Cox PH on 8 covariates; PH check schoenfeld_rank → holds.
- Selected: **cox** — PH assumption holds (all Schoenfeld p > 0.05); Cox PH retained.

## Metrics (held-out units)

- C-index = 0.7778 (primary, DEC-011)
- IBS = 0.0640 over horizons ['50', '100', '150', '200', '250'] (DEC-012)

## Limitations

- Slope covariates are computed over the full training trajectory; because total drift at failure is bounded, slope is partially confounded with duration (≈ drift / cycles). For censored units the slope over the observed window is a legitimate degradation-rate signal, but the validation C-index on run-to-failure units is optimistic relative to true prognostic use.
- Per-unit summary covariates ignore within-trajectory dynamics; a time-varying (counting-process) Cox model is provided in events.build_long_format but not evaluated here.
- FD001 only (single operating condition, single fault mode). Generalisation to FD002–FD004 is out of scope (SPEC-001 §2).
- Cost parameters C_p, C_f are illustrative (DEC-013); t* is baseline evidence, not a production recommendation.
- Weibull parametric baseline is unconditional (no covariates); it informs the failure regime and the cost policy, not unit-level ranking.
- Censored-unit failure probabilities are reported from cycle 0; a decision surface must condition on the already-observed cycle (S(t+c)/S(c)). Ranking (concordance vs RUL truth) is unaffected.

## Open decisions (verbatim from SPEC-001 §6)

- DEC-009 — kernel tests (test/test_intent.py) assume MASTER_TEMPLATE state; 4 cases fail in PROJECT mode; governance test change deferred
- DEC-007 — whether intake/sources/** should be excluded from repoctl discover(); optional governance change

## Reproduction

```bash
.venv/Scripts/python -m pm_survival run --raw-dir data/raw/cmapss
```
