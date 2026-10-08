"""Baseline survival models (TASK-003, SPEC-001 §4.3).

* :func:`fit_weibull`  — parametric Weibull on durations (shape ⇒ failure regime).
* :func:`fit_cox`      — Cox proportional hazards on selected, standardized covariates.
* :func:`check_ph`     — proportional-hazards assumption test (scaled Schoenfeld residuals).
* :func:`select_model` — keeps Cox when PH holds, otherwise falls back to Weibull AFT,
  recording the reason (SPEC-001 §4.3 SHOULD).

All fits are deterministic (no stochastic optimisation) so repeated runs on the
same table produce identical parameters.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, WeibullAFTFitter, WeibullFitter
from lifelines.statistics import proportional_hazard_test

from .events import feature_columns

PH_ALPHA = 0.05
DEFAULT_PENALIZER = 0.05  # small L2 ridge for stability with few units / many covariates


# --------------------------------------------------------------------------- Weibull


def weibull_regime(shape: float, tol: float = 0.1) -> str:
    """Interpret the Weibull shape parameter β (lifelines ``rho_``)."""
    if shape < 1.0 - tol:
        return "infant_mortality"
    if shape <= 1.0 + tol:
        return "random"
    return "wear_out"


@dataclass(frozen=True)
class WeibullResult:
    shape: float  # β (rho_)
    scale: float  # λ (lambda_)
    regime: str
    n: int
    n_events: int

    def survival(self, t: np.ndarray) -> np.ndarray:
        """Reliability R(t) = exp(-(t/λ)^β)."""
        t = np.asarray(t, dtype=float)
        return np.exp(-np.power(np.clip(t, 0, None) / self.scale, self.shape))

    def hazard(self, t: np.ndarray) -> np.ndarray:
        t = np.asarray(t, dtype=float)
        return (self.shape / self.scale) * np.power(np.clip(t, 1e-12, None) / self.scale, self.shape - 1)


def fit_weibull(tbl: pd.DataFrame) -> WeibullResult:
    wf = WeibullFitter()
    wf.fit(tbl["duration"].to_numpy(dtype=float), event_observed=tbl["event"].to_numpy())
    shape, scale = float(wf.rho_), float(wf.lambda_)
    return WeibullResult(shape=shape, scale=scale, regime=weibull_regime(shape), n=len(tbl), n_events=int(tbl["event"].sum()))


# --------------------------------------------------------------------------- covariates


def select_covariates(tbl: pd.DataFrame, k: int = 8) -> list[str]:
    """Pick the ``k`` covariates most (rank-)associated with duration among observed events.

    Uses |Spearman ρ| on event rows only (censored durations are lower bounds).
    Deterministic; ties broken by column name.
    """
    feats = feature_columns(tbl)
    ev = tbl[tbl["event"] == 1] if (tbl["event"] == 1).sum() >= 3 else tbl
    scores = []
    dur_rank = ev["duration"].rank()
    for f in feats:
        col = ev[f]
        if col.nunique() <= 1:
            continue
        rho = float(col.rank().corr(dur_rank))
        scores.append((-abs(rho) if np.isfinite(rho) else 0.0, f))
    scores.sort()
    return [f for _, f in scores[: max(1, min(k, len(scores)))]]


@dataclass
class _Scaler:
    mean: pd.Series
    std: pd.Series

    def transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        return (df[cols] - self.mean[cols]) / self.std[cols]


def _fit_scaler(tbl: pd.DataFrame, cols: list[str]) -> _Scaler:
    std = tbl[cols].std(ddof=0).replace(0.0, 1.0)
    return _Scaler(mean=tbl[cols].mean(), std=std)


# --------------------------------------------------------------------------- Cox


@dataclass
class CoxResult:
    covariates: list[str]
    coefficients: dict[str, float]
    train_concordance: float
    penalizer: float
    fitter: CoxPHFitter = field(repr=False)
    scaler: _Scaler = field(repr=False)
    kind: str = "cox"

    def _design(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.scaler.transform(df, self.covariates)

    def risk_score(self, df: pd.DataFrame) -> np.ndarray:
        """Partial hazard (higher ⇒ earlier expected failure)."""
        return self.fitter.predict_partial_hazard(self._design(df)).to_numpy(dtype=float).ravel()

    def survival(self, df: pd.DataFrame, times: np.ndarray) -> np.ndarray:
        """Survival matrix of shape ``(len(times), len(df))``."""
        sf = self.fitter.predict_survival_function(self._design(df), times=np.asarray(times, dtype=float))
        return sf.to_numpy(dtype=float)


def fit_cox(tbl: pd.DataFrame, covariates: list[str], penalizer: float = DEFAULT_PENALIZER) -> CoxResult:
    scaler = _fit_scaler(tbl, covariates)
    design = scaler.transform(tbl, covariates)
    design["duration"] = tbl["duration"].to_numpy(dtype=float)
    design["event"] = tbl["event"].to_numpy()
    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(design, duration_col="duration", event_col="event")
    return CoxResult(
        covariates=list(covariates),
        coefficients={c: float(v) for c, v in cph.params_.items()},
        train_concordance=float(cph.concordance_index_),
        penalizer=penalizer,
        fitter=cph,
        scaler=scaler,
    )


@dataclass(frozen=True)
class PHResult:
    p_values: dict[str, float]
    holds: bool
    alpha: float
    method: str


def check_ph(cox: CoxResult, tbl: pd.DataFrame, alpha: float = PH_ALPHA) -> PHResult:
    """Scaled Schoenfeld residual test (rank time transform). Verdict: all p > alpha."""
    design = cox._design(tbl)
    design["duration"] = tbl["duration"].to_numpy(dtype=float)
    design["event"] = tbl["event"].to_numpy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = proportional_hazard_test(cox.fitter, design, time_transform="rank")
    summary = res.summary  # index = covariate (possibly MultiIndex with transform)
    p = {}
    for idx, row in summary.iterrows():
        name = idx[0] if isinstance(idx, tuple) else idx
        p[str(name)] = float(row["p"])
    holds = all(v > alpha for v in p.values())
    return PHResult(p_values=p, holds=holds, alpha=alpha, method="schoenfeld_rank")


# --------------------------------------------------------------------------- Weibull AFT fallback


@dataclass
class WeibullAFTResult:
    covariates: list[str]
    coefficients: dict[str, float]
    fitter: WeibullAFTFitter = field(repr=False)
    scaler: _Scaler = field(repr=False)
    kind: str = "weibull_aft"

    def _design(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.scaler.transform(df, self.covariates)

    def risk_score(self, df: pd.DataFrame) -> np.ndarray:
        """Negative predicted median lifetime (higher ⇒ earlier expected failure)."""
        return -self.fitter.predict_median(self._design(df)).to_numpy(dtype=float).ravel()

    def survival(self, df: pd.DataFrame, times: np.ndarray) -> np.ndarray:
        sf = self.fitter.predict_survival_function(self._design(df), times=np.asarray(times, dtype=float))
        return sf.to_numpy(dtype=float)


def fit_weibull_aft(tbl: pd.DataFrame, covariates: list[str], penalizer: float = DEFAULT_PENALIZER) -> WeibullAFTResult:
    scaler = _fit_scaler(tbl, covariates)
    design = scaler.transform(tbl, covariates)
    design["duration"] = tbl["duration"].to_numpy(dtype=float)
    design["event"] = tbl["event"].to_numpy()
    aft = WeibullAFTFitter(penalizer=penalizer)
    aft.fit(design, duration_col="duration", event_col="event")
    coefs = {str(k[1]): float(v) for k, v in aft.params_.items() if k[0] == "lambda_" and k[1] != "Intercept"}
    return WeibullAFTResult(covariates=list(covariates), coefficients=coefs, fitter=aft, scaler=scaler)


# --------------------------------------------------------------------------- selection


@dataclass
class ModelSelection:
    kind: str
    reason: str
    model: CoxResult | WeibullAFTResult


def select_model(tbl: pd.DataFrame, covariates: list[str], ph: PHResult, penalizer: float = DEFAULT_PENALIZER) -> ModelSelection:
    """Apply the SPEC-001 §4.3 rule: Cox if PH holds, else Weibull AFT with recorded reason."""
    if ph.holds:
        return ModelSelection(
            kind="cox",
            reason=f"PH assumption holds (all Schoenfeld p > {ph.alpha}); Cox PH retained.",
            model=fit_cox(tbl, covariates, penalizer=penalizer),
        )
    failing = sorted(c for c, p in ph.p_values.items() if p <= ph.alpha)
    return ModelSelection(
        kind="weibull_aft",
        reason=f"PH assumption violated for {failing} (p <= {ph.alpha}); fell back to Weibull AFT.",
        model=fit_weibull_aft(tbl, covariates, penalizer=penalizer),
    )
