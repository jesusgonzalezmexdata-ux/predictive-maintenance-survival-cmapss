"""Landmark (condition-based) survival model.

At an inspection ("landmark") cycle ``c`` an engine is known to be alive. Its
features are computed **only from cycles ≤ c** (rolling mean and least-squares
slope of each informative sensor over the last ``window`` cycles, plus the age
``c``). The target is the *residual* life ``T − c``. Stacking one row per
(engine, landmark) gives a training set for a Weibull AFT model of residual
life, i.e. the conditional survival ``S(c + u) / S(c)`` given the engine's
current condition.

This fixes the leakage removed in TASK-007 without discarding late-life signal:
nothing after ``c`` enters a row built at ``c``.

Rows are weighted ``1 / n_landmarks(engine)`` so that every engine counts the
same regardless of how long it lived.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from lifelines import WeibullAFTFitter
from lifelines.exceptions import StatisticalWarning

from .data import SENSORS

DEFAULT_WINDOW = 20
DEFAULT_STEP = 5
DEFAULT_START = 20
DEFAULT_PENALIZER = 0.05
MEAN_SUFFIX = "_mean"
SLOPE_SUFFIX = "_slope"


def informative_sensors(raw: pd.DataFrame, min_unique: int = 10) -> list[str]:
    """Sensors with real variation (FD001 has several constant or two-level channels)."""
    return [s for s in SENSORS if raw[s].nunique() >= min_unique]


def rolling_features(raw: pd.DataFrame, sensors: list[str], window: int = DEFAULT_WINDOW) -> pd.DataFrame:
    """Per-cycle features that use only the current and previous ``window − 1`` cycles of the same engine.

    Returns one row per (unit_id, cycle) with ``<sensor>_mean``, ``<sensor>_slope`` and ``age``.
    """
    df = raw.sort_values(["unit_id", "cycle"]).reset_index(drop=True)
    g = df.groupby("unit_id", sort=False)
    minp = min(5, window)
    x = df["cycle"].astype(float)
    mx = g["cycle"].transform(lambda s: s.astype(float).rolling(window, min_periods=minp).mean())
    mx2 = (x * x).groupby(df["unit_id"]).transform(lambda s: s.rolling(window, min_periods=minp).mean())
    varx = mx2 - mx * mx
    out = {"unit_id": df["unit_id"].to_numpy(), "cycle": df["cycle"].to_numpy(), "age": x.to_numpy()}
    for s in sensors:
        y = df[s].astype(float)
        my = y.groupby(df["unit_id"]).transform(lambda v: v.rolling(window, min_periods=minp).mean())
        mxy = (x * y).groupby(df["unit_id"]).transform(lambda v: v.rolling(window, min_periods=minp).mean())
        with np.errstate(divide="ignore", invalid="ignore"):
            slope = (mxy - mx * my) / varx
        out[f"{s}{MEAN_SUFFIX}"] = my.to_numpy()
        out[f"{s}{SLOPE_SUFFIX}"] = slope.to_numpy()
    return pd.DataFrame(out)


def feature_names(sensors: list[str]) -> list[str]:
    return ["age", *[f"{s}{MEAN_SUFFIX}" for s in sensors], *[f"{s}{SLOPE_SUFFIX}" for s in sensors]]


def landmark_table(
    train_raw: pd.DataFrame,
    sensors: list[str],
    window: int = DEFAULT_WINDOW,
    step: int = DEFAULT_STEP,
    start: int = DEFAULT_START,
) -> pd.DataFrame:
    """Run-to-failure engines → one row per (engine, landmark c) with c in start, start+step, … < T."""
    feats = rolling_features(train_raw, sensors, window)
    life = train_raw.groupby("unit_id")["cycle"].max().rename("life")
    feats = feats.join(life, on="unit_id")
    keep = (feats["cycle"] >= start) & (feats["cycle"] < feats["life"]) & ((feats["cycle"] - start) % step == 0)
    tbl = feats[keep].copy()
    tbl["residual"] = (tbl["life"] - tbl["cycle"]).astype(float)
    tbl["event"] = 1
    tbl["weight"] = 1.0 / tbl.groupby("unit_id")["cycle"].transform("size")
    return tbl.reset_index(drop=True)


def last_cycle_features(raw: pd.DataFrame, sensors: list[str], window: int = DEFAULT_WINDOW) -> pd.DataFrame:
    """Features at the last observed cycle of each engine (test set: the decision point)."""
    feats = rolling_features(raw, sensors, window)
    return feats.loc[feats.groupby("unit_id")["cycle"].idxmax()].reset_index(drop=True)


@dataclass
class LandmarkModel:
    features: list[str]
    mean: pd.Series = field(repr=False)
    std: pd.Series = field(repr=False)
    fitter: WeibullAFTFitter = field(repr=False)
    kind: str = "landmark_weibull_aft"

    def _design(self, df: pd.DataFrame) -> pd.DataFrame:
        return (df[self.features] - self.mean) / self.std

    def survival(self, df: pd.DataFrame, horizons: np.ndarray) -> np.ndarray:
        """Matrix (len(horizons), n_rows) of P(residual life > u | condition at the landmark)."""
        sf = self.fitter.predict_survival_function(self._design(df), times=np.asarray(horizons, float))
        return sf.to_numpy(dtype=float)

    def prob_fail_within(self, df: pd.DataFrame, h: float) -> np.ndarray:
        return 1.0 - self.survival(df, np.array([float(h)]))[0]

    def median_residual(self, df: pd.DataFrame) -> np.ndarray:
        return self.fitter.predict_median(self._design(df)).to_numpy(dtype=float).ravel()

    def coefficients(self) -> dict[str, float]:
        return {str(k[1]): float(v) for k, v in self.fitter.params_.items() if k[0] == "lambda_" and k[1] != "Intercept"}


def fit_landmark(tbl: pd.DataFrame, features: list[str], penalizer: float = DEFAULT_PENALIZER) -> LandmarkModel:
    mean = tbl[features].mean()
    std = tbl[features].std(ddof=0).replace(0.0, 1.0)
    design = (tbl[features] - mean) / std
    design["residual"] = tbl["residual"].to_numpy(float)
    design["event"] = tbl["event"].to_numpy(int)
    design["weight"] = tbl["weight"].to_numpy(float)
    aft = WeibullAFTFitter(penalizer=penalizer)
    with warnings.catch_warnings():
        # Non-integer weights only bias the coefficient *variances*, which are not used here.
        warnings.simplefilter("ignore", StatisticalWarning)
        aft.fit(design, duration_col="residual", event_col="event", weights_col="weight", robust=False)
    return LandmarkModel(features=list(features), mean=mean, std=std, fitter=aft)


def age_only_median_residual(train_lives: np.ndarray, ages: np.ndarray) -> np.ndarray:
    """Population baseline: median of (T − c | T > c) from the empirical lifetime distribution."""
    lives = np.sort(np.asarray(train_lives, float))
    out = np.empty(len(ages))
    for i, c in enumerate(np.asarray(ages, float)):
        alive = lives[lives > c]
        out[i] = float(np.median(alive - c)) if len(alive) else 0.0
    return out
