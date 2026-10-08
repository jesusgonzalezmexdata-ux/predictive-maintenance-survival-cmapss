"""End-to-end evidence pipeline (TASK-006, SPEC-001).

    raw files ─► survival table ─► grouped split ─► Weibull + Cox ─► PH check
    ─► model selection ─► validation metrics ─► censored-unit scoring
    ─► cost policy ─► deterministic report + model card

Everything is deterministic for fixed inputs (``seed`` controls only the split).
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np

from . import __version__
from . import cost_policy as C
from . import data as D
from . import events as E
from . import metrics as X
from . import models as M
from . import report as R
from . import split as S

OPEN_DECISIONS = [
    "DEC-009 — kernel tests (test/test_intent.py) assume MASTER_TEMPLATE state; 4 cases fail in PROJECT mode; governance test change deferred",
    "DEC-007 — whether intake/sources/** should be excluded from repoctl discover(); optional governance change",
]

LIMITATIONS = [
    "Slope covariates use only the first early_window cycles (HG-003 = B / TASK-007). Cycles after that window, including the failure time, do not enter the feature. Early-life drift on FD001 is often weak, so concordance is expected to be lower than a full-trajectory slope; that lower number is the prognostic score.",
    "Per-unit summary covariates ignore within-trajectory dynamics; a time-varying (counting-process) Cox model is provided in events.build_long_format but not evaluated here.",
    "FD001 only (single operating condition, single fault mode). Generalisation to FD002–FD004 is out of scope (SPEC-001 §2).",
    "Cost parameters C_p, C_f are illustrative (DEC-013); t* is baseline evidence, not a production recommendation.",
    "Weibull parametric baseline is unconditional (no covariates); it informs the failure regime and the cost policy, not unit-level ranking.",
    "Censored-unit failure probabilities are reported from cycle 0; a decision surface must condition on the already-observed cycle (S(t+c)/S(c)). Concordance versus RUL truth is a separate evaluation and is reported in censored_scoring.",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_pipeline(
    raw_dir: str | Path,
    reports_dir: str | Path = "reports",
    models_dir: str | Path = "models",
    subset: str = "FD001",
    val_fraction: float = 0.2,
    seed: int = 42,
    n_covariates: int = 8,
    early_window: int = 20,
    horizons: list[int] | None = None,
    cost_ratio: float = 10.0,
    prefix: str = "",
) -> dict:
    raw_dir = Path(raw_dir)
    reports_dir, models_dir = Path(reports_dir), Path(models_dir)
    horizons = list(horizons) if horizons is not None else list(X.DEFAULT_HORIZONS)
    times = np.asarray(horizons, dtype=float)

    # 1. data boundary
    train_raw = D.load_fd(raw_dir, subset, "train", prefix=prefix)
    test_raw = D.load_fd(raw_dir, subset, "test", prefix=prefix)
    rul = D.load_rul(raw_dir, subset, prefix=prefix)
    schema_train = D.validate_schema(train_raw)
    schema_test = D.validate_schema(test_raw)

    # 2. events / censoring
    tbl = E.build_survival_table(train_raw, censored=False, early_window=early_window)
    censored = E.build_survival_table(test_raw, censored=True, early_window=early_window)
    # keep the same covariate columns for censored units (constant-dropping may differ)
    for col in E.feature_columns(tbl):
        if col not in censored.columns:
            censored[col] = 0.0
    tr, va = S.grouped_unit_split(tbl, val_fraction=val_fraction, seed=seed)

    # 3. models
    weib = M.fit_weibull(tr)
    covariates = M.select_covariates(tr, k=n_covariates)
    cox = M.fit_cox(tr, covariates)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ph = M.check_ph(cox, tr)
    sel = M.select_model(tr, covariates, ph)
    model = sel.model

    # 4. validation on held-out units
    risk_va = model.risk_score(va)
    surv_va = model.survival(va, times)
    cidx = X.concordance(va["duration"].to_numpy(), risk_va, va["event"].to_numpy())
    ib = X.integrated_brier(va["duration"].to_numpy(), va["event"].to_numpy(), surv_va, times)

    # 5. censored (test) units: score without RUL; compare ranking against RUL truth only for evaluation
    risk_te = model.risk_score(censored)
    truth = E.attach_rul_truth(censored, rul)["rul_true"].to_numpy(dtype=float)
    # Higher risk should pair with smaller remaining life ⇒ concordance of risk vs RUL (all "events" for ranking)
    c_rul = X.concordance(truth, risk_te, np.ones(len(truth), dtype=int))
    surv_te_at_h = model.survival(censored, times)
    exp_fail_within = {str(h): float(np.mean(1.0 - surv_te_at_h[i])) for i, h in enumerate(horizons)}

    # 6. cost policy on the Weibull reliability (unconditional baseline)
    horizon = float(max(600.0, 2.5 * weib.scale))
    cost = C.optimal_time(1.0, float(cost_ratio), weib.survival, horizon=horizon)

    payload = {
        "pm_survival_version": __version__,
        "subset": subset,
        "provenance": {
            "raw_dir": str(raw_dir).replace("\\", "/"),
            "files": {
                name: {"sha256": _sha256(raw_dir / f"{prefix}{name}")}
                for name in (f"train_{subset}.txt", f"test_{subset}.txt", f"RUL_{subset}.txt")
            },
            "schema_train": schema_train,
            "schema_test": schema_test,
            "early_window": early_window,
            "slope_window": early_window,
        },
        "split": {"val_fraction": val_fraction, "seed": seed, "n_train_units": int(len(tr)), "n_val_units": int(len(va))},
        "weibull": {"shape": weib.shape, "scale": weib.scale, "regime": weib.regime, "n": weib.n, "n_events": weib.n_events},
        "cox": {
            "covariates": cox.covariates,
            "coefficients": cox.coefficients,
            "train_concordance": cox.train_concordance,
            "penalizer": cox.penalizer,
        },
        "ph_test": {"holds": ph.holds, "alpha": ph.alpha, "p_values": ph.p_values, "method": ph.method},
        "selected_model": {"kind": sel.kind, "reason": sel.reason, "coefficients": getattr(model, "coefficients", {})},
        "validation": {
            "concordance": cidx,
            "ibs": ib["ibs"],
            "horizons": horizons,
            "brier": {str(int(t)): b for t, b in zip(ib["times"], ib["brier"])},
        },
        "censored_scoring": {
            "n_units": int(len(censored)),
            "concordance_vs_rul_truth": c_rul,
            "mean_unconditional_failure_probability_by_cycle": exp_fail_within,
            "note": "RUL truth used only to evaluate ranking; never a feature. Probabilities are from cycle 0 (unconditional), not conditioned on the observed censoring cycle.",
        },
        "cost_policy": {**cost.to_dict(), "reliability_source": "weibull_unconditional"},
    }

    R.write_eval_json(reports_dir / f"eval_{subset}.json", payload)
    R.write_text(reports_dir / f"eval_{subset}.md", R.render_eval_markdown(payload))
    R.write_text(models_dir / f"MODEL_CARD_{subset}.md", R.render_model_card(payload, OPEN_DECISIONS, LIMITATIONS))
    return json.loads(json.dumps(payload, default=float))
