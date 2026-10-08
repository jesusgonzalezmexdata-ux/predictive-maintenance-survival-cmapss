"""Cost-optimal age-replacement policy (TASK-005, SPEC-001 §4.5).

Classic age-replacement model (Barlow & Proschan): replace preventively at age
``t`` (cost ``C_p``) or correctively at failure (cost ``C_f``). The long-run
expected cost per unit time is

    C(t) = ( C_p · R(t) + C_f · (1 − R(t)) ) / ∫₀ᵗ R(x) dx

where ``R(t)`` is the reliability (survival) function. ``t* = argmin C(t)``.

Properties relied on by the tests (AC-6):
* an interior optimum exists only when the hazard is increasing (Weibull β > 1)
  and ``C_f > C_p``;
* raising ``C_f / C_p`` moves ``t*`` earlier;
* as ``C_f / C_p → 1`` the optimum moves to the horizon (run-to-failure).

Pure numpy; no model dependency. The result is **baseline evidence**, not a
production recommendation.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass

import numpy as np

Reliability = Callable[[np.ndarray], np.ndarray]


def _validate_costs(cp: float, cf: float) -> None:
    if not (cp > 0.0):
        raise ValueError("C_p must be > 0")
    if not (cf > cp):
        raise ValueError("C_f must exceed C_p; otherwise preventive replacement is never economical")


def expected_cost_rate(t: float, cp: float, cf: float, R: Reliability, n_grid: int = 2001) -> float:
    """C(t) evaluated with a trapezoid integral of R over [0, t]."""
    _validate_costs(cp, cf)
    if t <= 0.0:
        return float("inf")
    grid = np.linspace(0.0, float(t), n_grid)
    integral = float(np.trapezoid(np.asarray(R(grid), float), grid))
    if integral <= 0.0:
        return float("inf")
    r_t = float(np.asarray(R(np.array([t])), float)[0])
    return (cp * r_t + cf * (1.0 - r_t)) / integral


@dataclass(frozen=True)
class CostPolicyResult:
    t_star: float
    cost_rate_at_t_star: float
    reliability_at_t_star: float
    cost_ratio: float
    c_p: float
    c_f: float
    horizon: float
    at_horizon: bool  # True ⇒ no interior optimum: run-to-failure is cheapest within the horizon

    def to_dict(self) -> dict:
        return asdict(self)


def optimal_time(cp: float, cf: float, R: Reliability, horizon: float = 1000.0, n_points: int = 2000) -> CostPolicyResult:
    """Grid-search ``t*`` on (0, horizon]; the cumulative integral is computed once."""
    _validate_costs(cp, cf)
    if horizon <= 0.0:
        raise ValueError("horizon must be > 0")
    t = np.linspace(0.0, float(horizon), n_points + 1)
    r = np.clip(np.asarray(R(t), float), 0.0, 1.0)
    # cumulative ∫₀ᵗ R via trapezoid
    seg = 0.5 * (r[1:] + r[:-1]) * np.diff(t)
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    with np.errstate(divide="ignore", invalid="ignore"):
        cost = (cp * r + cf * (1.0 - r)) / cum
    cost[0] = np.inf
    i = int(np.nanargmin(cost))
    # A *strictly* interior optimum must beat the horizon cost by more than numerical noise.
    # Otherwise the curve is flat/decreasing (e.g. β ≤ 1 or C_f ≈ C_p): run-to-failure is cheapest.
    rel_tol = 1e-6
    interior = np.isfinite(cost[i]) and np.isfinite(cost[-1]) and cost[i] < cost[-1] * (1.0 - rel_tol)
    at_horizon = not interior
    if at_horizon:
        i = n_points
    return CostPolicyResult(
        t_star=float(t[i]),
        cost_rate_at_t_star=float(cost[i]),
        reliability_at_t_star=float(r[i]),
        cost_ratio=float(cf / cp),
        c_p=float(cp),
        c_f=float(cf),
        horizon=float(horizon),
        at_horizon=bool(at_horizon),
    )


def tabulated_reliability(times: np.ndarray, values: np.ndarray) -> Reliability:
    """Wrap a tabulated survival curve as a callable with linear interpolation (R(0)=1, R(∞)=last)."""
    times = np.asarray(times, float)
    values = np.clip(np.asarray(values, float), 0.0, 1.0)
    if times.ndim != 1 or times.shape != values.shape:
        raise ValueError("times and values must be 1-D arrays of equal length")
    order = np.argsort(times)
    times, values = times[order], values[order]

    def R(t: np.ndarray) -> np.ndarray:
        t = np.asarray(t, float)
        return np.interp(t, times, values, left=1.0, right=float(values[-1]))

    return R
