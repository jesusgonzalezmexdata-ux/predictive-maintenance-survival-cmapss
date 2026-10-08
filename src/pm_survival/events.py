"""Event / censoring construction (TASK-002, SPEC-001 §4.2).

Event definition
----------------
An engine *fails* when its recorded run-to-failure trajectory ends. In the
C-MAPSS **train** files every unit runs to failure, so ``event = 1`` and
``duration = max(cycle)``. In the **test** files trajectories are truncated
before failure: they are **right-censored** at the last observed cycle
(``event = 0``). Ground-truth remaining life (``RUL_FD00x.txt``) is attached
only through :func:`attach_rul_truth` and is never a feature.

Covariates
----------
The first baseline uses *per-unit summary covariates* computed from an
early-life window so that they are available at prediction time for a censored
unit too, and so that later cycles cannot leak into the feature (HG-003 = B):
``<sensor>_early`` (mean over the first ``early_window`` cycles) and
``<sensor>_slope`` (least-squares slope over that same window only). Constant
columns are dropped. A counting-process long format for time-varying Cox is
provided by :func:`build_long_format`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import OP_SETTINGS, SENSORS

RESERVED = ("unit_id", "duration", "event", "rul_true")
EARLY_SUFFIX = "_early"
SLOPE_SUFFIX = "_slope"


def _slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n, dtype=float)
    x -= x.mean()
    denom = float((x * x).sum())
    return float((x * (y - y.mean())).sum() / denom) if denom else 0.0


def build_survival_table(
    df: pd.DataFrame,
    censored: bool,
    early_window: int = 20,
    signals: list[str] | None = None,
) -> pd.DataFrame:
    """Return one row per unit: ``unit_id, duration, event, <covariates>``.

    ``censored=False`` → run-to-failure (train): event = 1.
    ``censored=True``  → truncated (test): event = 0 at last observed cycle.
    """
    signals = list(signals) if signals is not None else [*OP_SETTINGS, *SENSORS]
    rows = []
    for unit, g in df.sort_values(["unit_id", "cycle"]).groupby("unit_id", sort=True):
        duration = int(g["cycle"].max())
        early = g[g["cycle"] <= early_window]
        row = {"unit_id": int(unit), "duration": duration, "event": 0 if censored else 1}
        for s in signals:
            y_early = early[s].to_numpy(dtype=float)
            row[f"{s}{EARLY_SUFFIX}"] = float(y_early.mean()) if len(y_early) else float("nan")
            row[f"{s}{SLOPE_SUFFIX}"] = _slope(y_early)
        rows.append(row)
    tbl = pd.DataFrame(rows)
    # Drop constant covariates (e.g. op_setting_3 == 100 in FD001); they carry no hazard information.
    const = [c for c in tbl.columns if c not in RESERVED and tbl[c].nunique(dropna=False) <= 1]
    return tbl.drop(columns=const)


def feature_columns(tbl: pd.DataFrame) -> list[str]:
    """Covariate columns: everything except identifiers, outcome and RUL truth."""
    return [c for c in tbl.columns if c not in RESERVED]


def attach_rul_truth(tbl: pd.DataFrame, rul: pd.Series) -> pd.DataFrame:
    """Join evaluation-only ground truth on ``unit_id``; column stays out of features."""
    out = tbl.merge(rul.rename("rul_true").reset_index(), on="unit_id", how="left")
    return out


def build_long_format(df: pd.DataFrame, signals: list[str] | None = None) -> pd.DataFrame:
    """Counting-process format for time-varying covariates.

    Columns: ``unit_id, start, stop, event, cycle, <signals>`` where
    ``(start, stop] = (cycle-1, cycle]`` and ``event = 1`` only on the last
    cycle of a run-to-failure unit. For censored units pass the frame through
    :func:`mark_censored_long` afterwards.
    """
    signals = list(signals) if signals is not None else [*OP_SETTINGS, *SENSORS]
    d = df.sort_values(["unit_id", "cycle"]).copy()
    last = d.groupby("unit_id")["cycle"].transform("max")
    out = pd.DataFrame(
        {
            "unit_id": d["unit_id"].astype("int64"),
            "start": (d["cycle"] - 1).astype("int64"),
            "stop": d["cycle"].astype("int64"),
            "event": (d["cycle"] == last).astype("int64"),
            "cycle": d["cycle"].astype("int64"),
        }
    )
    for s in signals:
        out[s] = d[s].to_numpy(dtype=float)
    return out.reset_index(drop=True)


def mark_censored_long(long: pd.DataFrame) -> pd.DataFrame:
    """Set ``event = 0`` everywhere (right-censored trajectories)."""
    out = long.copy()
    out["event"] = 0
    return out
