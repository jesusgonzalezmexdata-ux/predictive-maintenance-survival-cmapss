"""Survival evaluation metrics (TASK-004, SPEC-001 §4.4).

* :func:`concordance`       — Harrell's C-index (DEC-011: primary metric).
* :func:`brier_score`       — time-dependent Brier score with IPCW (Graf et al. 1999).
* :func:`integrated_brier`  — IBS over the DEC-012 horizon grid (trapezoid rule).

Risk convention: **higher risk ⇒ earlier expected failure**.
"""
from __future__ import annotations

import numpy as np
from lifelines import KaplanMeierFitter
from lifelines.utils import concordance_index

DEFAULT_HORIZONS = [50, 100, 150, 200, 250]  # DEC-012 (cycles)


def concordance(durations: np.ndarray, risk: np.ndarray, events: np.ndarray) -> float:
    """C-index where larger ``risk`` means shorter predicted time."""
    return float(concordance_index(np.asarray(durations, float), -np.asarray(risk, float), np.asarray(events, int)))


def _censoring_survival(durations: np.ndarray, events: np.ndarray) -> KaplanMeierFitter:
    """Kaplan–Meier estimate of the censoring distribution G(t) (event = censored)."""
    km = KaplanMeierFitter()
    km.fit(durations, event_observed=1 - np.asarray(events, int))
    return km


def brier_score(durations: np.ndarray, events: np.ndarray, surv_at_t: np.ndarray, t: float) -> float:
    """IPCW Brier score at horizon ``t``.

    ``surv_at_t[i]`` is the predicted probability that subject ``i`` survives
    beyond ``t``. Without censoring this reduces to the MSE of the alive
    indicator.
    """
    d = np.asarray(durations, float)
    e = np.asarray(events, int)
    s = np.clip(np.asarray(surv_at_t, float), 0.0, 1.0)
    n = len(d)
    if n == 0:
        return float("nan")
    if (e == 1).all():
        alive = (d > t).astype(float)
        return float(np.mean((alive - s) ** 2))
    km = _censoring_survival(d, e)
    # G evaluated just before the observed time for failures, and at t for survivors
    g_ti = km.survival_function_at_times(np.maximum(d - 1e-9, 0.0)).to_numpy(dtype=float)
    g_t = float(km.survival_function_at_times([t]).to_numpy(dtype=float)[0])
    g_ti = np.where(g_ti <= 0, np.nan, g_ti)
    g_t = np.nan if g_t <= 0 else g_t
    died_before = (d <= t) & (e == 1)
    alive_after = d > t
    term1 = np.where(died_before, (s ** 2) / g_ti, 0.0)
    term2 = np.where(alive_after, ((1.0 - s) ** 2) / g_t, 0.0)
    total = np.nansum(term1 + term2)
    return float(total / n)


def integrated_brier(durations: np.ndarray, events: np.ndarray, surv_matrix: np.ndarray, times: np.ndarray) -> dict:
    """IBS over ``times`` given ``surv_matrix`` of shape ``(len(times), n_subjects)``."""
    times = np.asarray(times, float)
    surv_matrix = np.asarray(surv_matrix, float)
    if surv_matrix.shape[0] != len(times):
        raise ValueError("surv_matrix must have one row per horizon time")
    bs = np.array([brier_score(durations, events, surv_matrix[i], float(t)) for i, t in enumerate(times)])
    if len(times) > 1:
        ibs = float(np.trapezoid(bs, times) / (times[-1] - times[0]))
    else:
        ibs = float(bs[0])
    return {"times": times.tolist(), "brier": bs.tolist(), "ibs": ibs}
