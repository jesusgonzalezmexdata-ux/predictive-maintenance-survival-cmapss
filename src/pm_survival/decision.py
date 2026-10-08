"""Business-facing decision helpers (SPEC-002).

Keeps the Streamlit UI thin: load data, fit the governed baseline, answer
«¿cuándo conviene el preventivo?» and explain one asset.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import cost_policy as C
from . import data as D
from . import events as E
from . import explain as X
from . import models as M
from . import split as S


@dataclass
class DecisionBundle:
    weibull: M.WeibullResult
    model: M.CoxResult | M.WeibullAFTResult
    selection_reason: str
    train_table: pd.DataFrame
    censored_table: pd.DataFrame
    cost: C.CostPolicyResult


def fit_decision_bundle(
    raw_dir: str | Path,
    subset: str = "FD001",
    early_window: int = 20,
    n_covariates: int = 8,
    seed: int = 42,
    cost_ratio: float = 10.0,
    prefix: str = "",
) -> DecisionBundle:
    raw_dir = Path(raw_dir)
    train_raw = D.load_fd(raw_dir, subset, "train", prefix=prefix)
    test_raw = D.load_fd(raw_dir, subset, "test", prefix=prefix)
    tbl = E.build_survival_table(train_raw, censored=False, early_window=early_window)
    censored = E.build_survival_table(test_raw, censored=True, early_window=early_window)
    for col in E.feature_columns(tbl):
        if col not in censored.columns:
            censored[col] = 0.0
    tr, _ = S.grouped_unit_split(tbl, val_fraction=0.2, seed=seed)
    weib = M.fit_weibull(tr)
    covariates = M.select_covariates(tr, k=n_covariates)
    cox = M.fit_cox(tr, covariates)
    ph = M.check_ph(cox, tr)
    sel = M.select_model(tr, covariates, ph)
    horizon = float(max(600.0, 2.5 * weib.scale))
    cost = C.optimal_time(1.0, float(cost_ratio), weib.survival, horizon=horizon)
    return DecisionBundle(
        weibull=weib,
        model=sel.model,
        selection_reason=sel.reason,
        train_table=tbl,
        censored_table=censored,
        cost=cost,
    )


def recompute_cost(weib: M.WeibullResult, cp: float, cf: float) -> C.CostPolicyResult:
    if cp <= 0 or cf <= cp:
        raise ValueError("C_f must exceed C_p and both must be positive")
    horizon = float(max(600.0, 2.5 * weib.scale))
    return C.optimal_time(float(cp), float(cf), weib.survival, horizon=horizon)


def intervention_message(cost: C.CostPolicyResult) -> str:
    if cost.at_horizon:
        return (
            "Con esta relación de costos, el costo esperado no justifica adelantar el preventivo "
            "dentro del horizonte modelado: conviene operar y revisar más adelante."
        )
    return (
        f"Con C_f / C_p = {cost.cost_ratio:.1f}, el tiempo de intervención preventivo que "
        f"minimiza el costo esperado es t* ≈ {cost.t_star:.0f} ciclos "
        f"(confiabilidad residual R(t*) ≈ {cost.reliability_at_t_star:.0%})."
    )


def reliability_curve(weib: M.WeibullResult, t_max: float | None = None, n: int = 200) -> pd.DataFrame:
    t_max = float(t_max or max(400.0, 2.0 * weib.scale))
    t = np.linspace(1.0, t_max, n)
    return pd.DataFrame({"ciclo": t, "probabilidad_de_seguir_operando": weib.survival(t)})
