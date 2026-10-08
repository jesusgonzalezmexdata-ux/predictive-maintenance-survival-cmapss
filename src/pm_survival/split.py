"""Grouped (by unit) deterministic split (TASK-002, SPEC-001 §4.2).

Leakage rule: all rows / the summary row of a given ``unit_id`` land in exactly
one partition. Works on the per-unit survival table or on raw cycle rows.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def grouped_unit_split(
    df: pd.DataFrame, val_fraction: float = 0.2, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(train, validation)`` with disjoint ``unit_id`` sets.

    The validation set gets ``ceil(val_fraction * n_units)`` units (at least 1
    when ``n_units > 1``). Deterministic for a fixed ``seed``.
    """
    if not 0.0 < val_fraction < 1.0:
        raise ValueError("val_fraction must be in (0, 1)")
    units = np.sort(df["unit_id"].unique())
    n_val = int(np.ceil(val_fraction * len(units)))
    if len(units) > 1:
        n_val = min(max(n_val, 1), len(units) - 1)
    rng = np.random.default_rng(seed)
    val_units = set(rng.choice(units, size=n_val, replace=False).tolist())
    mask = df["unit_id"].isin(val_units)
    return df[~mask].reset_index(drop=True), df[mask].reset_index(drop=True)
