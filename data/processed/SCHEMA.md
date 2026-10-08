# data/processed — Derived table schemas (SPEC-001 §4.2)

Governed scope. Write policy: `APPROVED_TASK` (TASK-002). Files here are
deterministic, regenerable outputs; tabular artifacts (`*.csv`, `*.parquet`)
are gitignored by default (DEC-004) and recreated by the pipeline.

## `survival_table` (one row per unit)

| Column | Type | Meaning |
|--------|------|---------|
| `unit_id` | int | Engine identifier (1-based, per subset) |
| `duration` | int | Train: cycle of failure (= max cycle). Test: last observed cycle (censoring time) |
| `event` | int {0,1} | 1 = failure observed (train); 0 = right-censored (test) |
| `<signal>_early` | float | Mean of `<signal>` over cycles `1..early_window` (default 20) |
| `<signal>_slope` | float | Least-squares slope of `<signal>` vs cycle over the observed trajectory |
| `rul_true` | int (optional) | Ground truth from `RUL_FD00x.txt`; **evaluation only**, excluded by `feature_columns()` |

Constant columns (e.g. `op_setting_3` in FD001) are dropped at build time.

Why early-window covariates: they exist for a censored test unit at the moment
of prediction, so the same feature contract serves training and scoring.

## `long_format` (counting process; one row per cycle)

| Column | Type | Meaning |
|--------|------|---------|
| `unit_id` | int | Engine identifier |
| `start`, `stop` | int | Interval `(cycle-1, cycle]` |
| `event` | int {0,1} | 1 only on the last cycle of a run-to-failure unit; all 0 for censored units |
| `cycle` | int | Observation cycle |
| `op_setting_1..3`, `sensor_1..21` | float | Raw signals at that cycle |

## Split

`grouped_unit_split(df, val_fraction, seed)` — disjoint `unit_id` sets; deterministic.
Default for SPEC-001 evaluation: `val_fraction = 0.2`, `seed = 42`.
