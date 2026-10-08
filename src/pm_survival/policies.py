"""Maintenance policies evaluated on run-to-failure engines (renewal-reward backtest).

Each engine is one renewal cycle. A policy ends it either preventively at cycle
``r < T`` (cost ``C_p``, cycle length ``r``) or by failure at ``T`` (cost ``C_f``,
length ``T``). The long-run cost per cycle is ``Σ cost / Σ length``.

Policies
--------
* ``run_to_failure``: never intervene.
* ``age``: replace at a fixed age ``t*`` for the whole fleet (Weibull age-replacement).
* ``condition``: inspect every ``step`` cycles; replace at the first inspection where
  the landmark model gives ``P(fail within h | condition) ≥ p*``. ``p*`` is tuned on
  training engines only.
* ``oracle``: replace at the last inspection before failure (perfect foresight, a bound).

Costs are in units of ``C_p`` (``C_p = 1``, ``C_f = ratio``).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PolicySummary:
    policy: str
    cost_per_1000_cycles: float
    failures: int
    preventive: int
    n_engines: int
    mean_wasted_cycles: float  # mean (T − r) over preventive replacements
    utilisation: float  # Σ length / Σ T: share of the fleet's potential life actually used

    def to_dict(self) -> dict:
        return asdict(self)


def outcomes(life: np.ndarray, replace_at: np.ndarray, ratio: float) -> pd.DataFrame:
    """Per-engine outcome given the planned replacement cycle (``inf`` = never)."""
    life = np.asarray(life, float)
    replace_at = np.asarray(replace_at, float)
    prevented = replace_at < life
    length = np.where(prevented, replace_at, life)
    cost = np.where(prevented, 1.0, float(ratio))
    return pd.DataFrame({"life": life, "length": length, "cost": cost, "prevented": prevented})


def summarise(name: str, out: pd.DataFrame) -> PolicySummary:
    wasted = (out["life"] - out["length"])[out["prevented"]]
    return PolicySummary(
        policy=name,
        cost_per_1000_cycles=float(1000.0 * out["cost"].sum() / out["length"].sum()),
        failures=int((~out["prevented"]).sum()),
        preventive=int(out["prevented"].sum()),
        n_engines=int(len(out)),
        mean_wasted_cycles=float(wasted.mean()) if len(wasted) else 0.0,
        utilisation=float(out["length"].sum() / out["life"].sum()),
    )


def condition_replacement(pred: pd.DataFrame, threshold: float) -> pd.Series:
    """First inspection cycle per engine with ``p_fail ≥ threshold`` (``inf`` if none).

    ``pred`` has one row per (unit_id, cycle) inspection with column ``p_fail``.
    """
    hit = pred[pred["p_fail"] >= threshold]
    first = hit.groupby("unit_id")["cycle"].min()
    return first.reindex(pred["unit_id"].unique()).fillna(np.inf).astype(float)


def oracle_replacement(pred: pd.DataFrame) -> pd.Series:
    return pred.groupby("unit_id")["cycle"].max().astype(float)


def cost_rate(life: pd.Series, replace_at: pd.Series, ratio: float) -> float:
    out = outcomes(life.loc[replace_at.index].to_numpy(), replace_at.to_numpy(), ratio)
    return float(out["cost"].sum() / out["length"].sum())


def tune_threshold(pred: pd.DataFrame, life: pd.Series, ratio: float, grid: np.ndarray | None = None) -> float:
    """Threshold that minimises the cost rate on the given (training) engines."""
    if grid is None:
        grid = np.unique(np.quantile(pred["p_fail"], np.linspace(0.0, 1.0, 201)))
    rates = [cost_rate(life, condition_replacement(pred, t), ratio) for t in grid]
    return float(grid[int(np.argmin(rates))])


def bootstrap_difference(
    a: pd.DataFrame, b: pd.DataFrame, n_boot: int = 2000, seed: int = 0
) -> dict[str, float]:
    """95 % CI of cost_per_1000(a) − cost_per_1000(b), resampling engines (paired)."""
    rng = np.random.default_rng(seed)
    n = len(a)
    ca, la = a["cost"].to_numpy(), a["length"].to_numpy()
    cb, lb = b["cost"].to_numpy(), b["length"].to_numpy()
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        diffs[i] = 1000.0 * (ca[idx].sum() / la[idx].sum() - cb[idx].sum() / lb[idx].sum())
    point = 1000.0 * (ca.sum() / la.sum() - cb.sum() / lb.sum())
    lo, hi = np.quantile(diffs, [0.025, 0.975])
    return {"diff": float(point), "ci_low": float(lo), "ci_high": float(hi), "p_a_better": float((diffs < 0).mean())}
