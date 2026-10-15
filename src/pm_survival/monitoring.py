"""Sensor monitoring for the condition-based policy.

Compares a new batch of engine cycles with a reference batch (normally the training engines at a
comparable range of ages). Three checks, none of which changes the model:

* drift: population stability index (PSI) per informative sensor;
* frozen sensor: a sensor that varied in the reference but is constant in the batch;
* out of range: share of readings outside the reference range.

Compare like with like: test engines are cut earlier in life than training engines, so a batch of
young engines will drift against a reference of whole trajectories without anything being wrong.
Filter both batches to the same age range before comparing.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PSI_MODERATE, PSI_MAJOR = 0.10, 0.25
OUT_OF_RANGE_ALERT = 0.05
EPS = 1e-4


def build_reference(raw: pd.DataFrame, sensors: list[str], bins: int = 10) -> dict:
    ref = {}
    for s in sensors:
        v = raw[s].to_numpy(dtype=float)
        edges = np.unique(np.quantile(v, np.linspace(0, 1, bins + 1)[1:-1]))
        counts = np.bincount(np.searchsorted(edges, v, side="right"), minlength=len(edges) + 1)
        ref[s] = dict(edges=edges.tolist(), proportions=(counts / len(v)).tolist(),
                      low=float(v.min()), high=float(v.max()), std=float(v.std()))
    return ref


def psi(expected, actual) -> float:
    e = np.clip(np.asarray(expected, dtype=float), EPS, None)
    a = np.clip(np.asarray(actual, dtype=float), EPS, None)
    return float(np.sum((a - e) * np.log(a / e)))


def drift_report(reference: dict, batch: pd.DataFrame) -> dict:
    rows = {}
    for s, ref in reference.items():
        v = batch[s].to_numpy(dtype=float)
        edges = np.asarray(ref["edges"])
        counts = np.bincount(np.searchsorted(edges, v, side="right"), minlength=len(edges) + 1)
        rows[s] = dict(
            psi=round(psi(ref["proportions"], counts / max(1, len(v))), 4),
            frozen=bool(ref["std"] > 0 and np.std(v) == 0),
            out_of_range=round(float(np.mean((v < ref["low"]) | (v > ref["high"]))), 4),
        )
    major = sorted(s for s, r in rows.items() if r["psi"] >= PSI_MAJOR)
    moderate = sorted(s for s, r in rows.items() if PSI_MODERATE <= r["psi"] < PSI_MAJOR)
    frozen = sorted(s for s, r in rows.items() if r["frozen"])
    out_of_range = sorted(s for s, r in rows.items() if r["out_of_range"] > OUT_OF_RANGE_ALERT)
    alert = bool(major or frozen or out_of_range)
    return dict(status="ALERT" if alert else ("WARN" if moderate else "OK"), cycles=int(len(batch)),
                psi_major=major, psi_moderate=moderate, frozen=frozen, out_of_range=out_of_range, sensors=rows)
