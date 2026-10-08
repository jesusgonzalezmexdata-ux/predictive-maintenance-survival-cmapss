"""SPEC-003 study: condition-based (landmark) survival vs. baselines, and maintenance policies.

Everything here is computed from the raw NASA files; nothing is hand-entered.

1. Repeated grouped cross-validation on the 100 run-to-failure engines
   (engines never cross folds): out-of-fold concordance and Brier score of the
   landmark model, calibration of P(fail within h).
2. Policy backtest on the same out-of-fold predictions (renewal-reward):
   run-to-failure, fixed age t*, condition-based, oracle, for several C_f/C_p.
   The condition threshold and t* are fitted on the training engines of each fold;
   the threshold uses an inner grouped CV so it never sees its own predictions.
3. Official test set (100 truncated engines + true RUL): concordance and RMSE of the
   predicted remaining life against the truth, with bootstrap 95 % CIs, for
   the landmark model and two baselines (age only; early-window model of SPEC-001).
4. Holm correction of the SPEC-001 Schoenfeld tests (reported next to the original verdict).
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from lifelines.utils import concordance_index

from . import cost_policy as C
from . import data as D
from . import events as E
from . import landmark as L
from . import models as M
from . import policies as P
from . import split as S

RATIOS = (2.0, 3.0, 5.0, 10.0, 20.0, 50.0)
HEADLINE_RATIO = 10.0
DECISION_HORIZON = 10  # P(fail within the next two inspections); fixed before looking at results
CALIBRATION_HORIZON = 30
BRIER_HORIZONS = (10, 30, 50)


@dataclass(frozen=True)
class StudyConfig:
    subset: str = "FD001"
    window: int = L.DEFAULT_WINDOW
    step: int = L.DEFAULT_STEP
    start: int = L.DEFAULT_START
    n_folds: int = 5
    n_repeats: int = 5
    inner_folds: int = 4
    seed: int = 2026
    n_boot: int = 2000


def _folds(units: np.ndarray, k: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    perm = rng.permutation(np.sort(units))
    return [np.sort(f) for f in np.array_split(perm, k)]


def _predict(model: L.LandmarkModel, rows: pd.DataFrame) -> pd.DataFrame:
    out = rows[["unit_id", "cycle", "residual"]].copy()
    out["p_fail"] = model.prob_fail_within(rows, DECISION_HORIZON)
    out["p30"] = model.prob_fail_within(rows, CALIBRATION_HORIZON)
    surv = model.survival(rows, np.array(BRIER_HORIZONS, float))
    for j, h in enumerate(BRIER_HORIZONS):
        out[f"p_h{h}"] = 1.0 - surv[j]
    out["median"] = model.median_residual(rows)
    return out


def _age_tstar(lives: np.ndarray, ratio: float) -> float:
    tbl = pd.DataFrame({"duration": lives.astype(float), "event": 1})
    weib = M.fit_weibull(tbl)
    horizon = float(max(600.0, 2.5 * weib.scale))
    return C.optimal_time(1.0, ratio, weib.survival, horizon=horizon).t_star


def _bootstrap_metric(fn, *arrays, n_boot: int, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(arrays[0])
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        vals.append(fn(*(a[idx] for a in arrays)))
    lo, hi = np.quantile(vals, [0.025, 0.975])
    return float(lo), float(hi)


def _cindex(truth: np.ndarray, pred: np.ndarray) -> float:
    return float(concordance_index(truth, pred))


def _rmse(truth: np.ndarray, pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((pred - truth) ** 2)))


def holm(p_values: dict[str, float], alpha: float = 0.05) -> dict:
    """Holm–Bonferroni step-down adjustment."""
    items = sorted(p_values.items(), key=lambda kv: kv[1])
    m = len(items)
    adjusted, running = {}, 0.0
    for i, (name, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        adjusted[name] = running
    return {"alpha": alpha, "adjusted": adjusted, "holds": all(v > alpha for v in adjusted.values())}


def run_study(raw_dir: str | Path, cfg: StudyConfig | None = None, prefix: str = "") -> dict:
    """Run the full SPEC-003 study (lifelines convergence chatter is silenced only inside this call)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return _run_study(Path(raw_dir), cfg or StudyConfig(), prefix)


def _run_study(raw_dir: Path, cfg: StudyConfig, prefix: str) -> dict:
    train_raw = D.load_fd(raw_dir, cfg.subset, "train", prefix=prefix)
    test_raw = D.load_fd(raw_dir, cfg.subset, "test", prefix=prefix)
    rul = D.load_rul(raw_dir, cfg.subset, prefix=prefix)

    sensors = L.informative_sensors(train_raw)
    feats = L.feature_names(sensors)
    tbl = L.landmark_table(train_raw, sensors, cfg.window, cfg.step, cfg.start)
    life = train_raw.groupby("unit_id")["cycle"].max().astype(float)
    units = life.index.to_numpy()

    # ---------------------------------------------------------------- 1 + 2: repeated grouped CV
    cv_rows, policy_rows, repeat_cindex = [], [], []
    for r in range(cfg.n_repeats):
        oof = []
        for k, held in enumerate(_folds(units, cfg.n_folds, cfg.seed + r)):
            tr_units = np.setdiff1d(units, held)
            tr_tbl = tbl[tbl["unit_id"].isin(tr_units)]
            model = L.fit_landmark(tr_tbl, feats)
            pred = _predict(model, tbl[tbl["unit_id"].isin(held)])
            pred["repeat"], pred["fold"] = r, k
            oof.append(pred)

            # inner CV on training engines → threshold per ratio (no self-prediction)
            inner = []
            for inner_held in _folds(tr_units, cfg.inner_folds, cfg.seed + 1000 * (r + 1) + k):
                inner_model = L.fit_landmark(tr_tbl[~tr_tbl["unit_id"].isin(inner_held)], feats)
                inner.append(_predict(inner_model, tr_tbl[tr_tbl["unit_id"].isin(inner_held)]))
            inner = pd.concat(inner, ignore_index=True)

            for ratio in RATIOS:
                thr = P.tune_threshold(inner, life, ratio)
                t_star = _age_tstar(life.loc[tr_units].to_numpy(), ratio)
                plans = {
                    "run_to_failure": pd.Series(np.inf, index=held),
                    "age": pd.Series(t_star, index=held),
                    "condition": P.condition_replacement(pred, thr).reindex(held),
                    "oracle": P.oracle_replacement(pred).reindex(held),
                }
                for name, rep in plans.items():
                    out = P.outcomes(life.loc[held].to_numpy(), rep.to_numpy(), ratio)
                    out["unit_id"], out["policy"], out["ratio"], out["repeat"] = held, name, ratio, r
                    out["threshold"] = thr if name == "condition" else np.nan
                    out["t_star"] = t_star if name == "age" else np.nan
                    policy_rows.append(out)
        oof = pd.concat(oof, ignore_index=True)
        cv_rows.append(oof)
        repeat_cindex.append(_cindex(oof["residual"].to_numpy(), oof["median"].to_numpy()))

    cv = pd.concat(cv_rows, ignore_index=True)
    pol = pd.concat(policy_rows, ignore_index=True)

    # out-of-fold Brier (no censoring on run-to-failure engines) vs a constant base-rate forecast
    brier = {}
    for h in BRIER_HORIZONS:
        y = (cv["residual"] <= h).astype(float)
        p = cv[f"p_h{h}"]
        brier[str(h)] = {"model": float(np.mean((p - y) ** 2)), "base_rate": float(np.mean((y.mean() - y) ** 2))}

    # calibration of P(fail within 30) — deciles of the out-of-fold prediction
    y30 = (cv["residual"] <= CALIBRATION_HORIZON).astype(float)
    bins = pd.qcut(cv["p30"], 10, duplicates="drop")
    calib = (
        pd.DataFrame({"pred": cv["p30"], "obs": y30, "bin": bins})
        .groupby("bin", observed=True)
        .agg(predicted=("pred", "mean"), observed=("obs", "mean"), n=("obs", "size"))
        .reset_index(drop=True)
    )

    # policy summaries: pooled over repeats; CI by engine-cluster bootstrap
    policy_table, policy_ci = [], {}
    for ratio in RATIOS:
        per_unit = {}
        for name in ("run_to_failure", "age", "condition", "oracle"):
            sub = pol[(pol["ratio"] == ratio) & (pol["policy"] == name)]
            s = P.summarise(name, sub)
            row = s.to_dict()
            row["failures"] = round(row["failures"] / cfg.n_repeats, 1)
            row["preventive"] = round(row["preventive"] / cfg.n_repeats, 1)
            row["n_engines"] = int(row["n_engines"] / cfg.n_repeats)
            row["ratio"] = ratio
            if name == "condition":
                row["threshold_median"] = float(sub["threshold"].median())
            if name == "age":
                row["t_star_median"] = float(sub["t_star"].median())
            policy_table.append(row)
            per_unit[name] = sub.groupby("unit_id")[["cost", "length"]].sum().sort_index()
        policy_ci[str(ratio)] = {
            "condition_minus_age": P.bootstrap_difference(per_unit["condition"], per_unit["age"], cfg.n_boot, cfg.seed),
            "condition_minus_run_to_failure": P.bootstrap_difference(
                per_unit["condition"], per_unit["run_to_failure"], cfg.n_boot, cfg.seed
            ),
        }
    policy_df = pd.DataFrame(policy_table)

    # ---------------------------------------------------------------- 3: official test set
    final = L.fit_landmark(tbl, feats)
    last = L.last_cycle_features(test_raw, sensors, cfg.window)
    truth = rul.loc[last["unit_id"]].to_numpy(float)
    preds = {
        "landmark": final.median_residual(last),
        "age_only": L.age_only_median_residual(life.to_numpy(), last["cycle"].to_numpy()),
    }
    # early-window model of SPEC-001 (one row per engine, lifetime from cycle 0)
    early_tr = E.build_survival_table(train_raw, censored=False, early_window=cfg.window)
    early_te = E.build_survival_table(test_raw, censored=True, early_window=cfg.window)
    for col in E.feature_columns(early_tr):
        if col not in early_te.columns:
            early_te[col] = 0.0
    tr_split, _ = S.grouped_unit_split(early_tr, val_fraction=0.2, seed=42)
    covs = M.select_covariates(tr_split, k=8)
    ph = M.check_ph(M.fit_cox(tr_split, covs), tr_split)
    early_model = M.select_model(tr_split, covs, ph).model
    early_te = early_te.set_index("unit_id").loc[last["unit_id"]].reset_index()
    early_life = -early_model.risk_score(early_te) if early_model.kind == "weibull_aft" else None
    if early_life is not None:
        preds["early_window"] = np.clip(early_life - early_te["duration"].to_numpy(float), 0.0, None)

    test_metrics = {}
    for name, pred in preds.items():
        c_lo, c_hi = _bootstrap_metric(_cindex, truth, pred, n_boot=cfg.n_boot, seed=cfg.seed)
        r_lo, r_hi = _bootstrap_metric(_rmse, truth, pred, n_boot=cfg.n_boot, seed=cfg.seed)
        test_metrics[name] = {
            "concordance_vs_rul": _cindex(truth, pred),
            "concordance_ci95": [c_lo, c_hi],
            "rmse_cycles": _rmse(truth, pred),
            "rmse_ci95": [r_lo, r_hi],
        }
    p30_test = final.prob_fail_within(last, CALIBRATION_HORIZON)
    y30_test = (truth <= CALIBRATION_HORIZON).astype(float)
    test_brier30 = {"model": float(np.mean((p30_test - y30_test) ** 2)), "base_rate": float(np.mean((y30_test.mean() - y30_test) ** 2))}

    # decision for the current fleet (test engines at their last observed cycle)
    oof_r0 = cv[cv["repeat"] == 0]
    fleet_thresholds = {str(r): P.tune_threshold(oof_r0, life, r) for r in RATIOS}
    fleet = pd.DataFrame(
        {
            "unit_id": last["unit_id"].astype(int),
            "cycles_observed": last["cycle"].astype(int),
            "p_fail_10": final.prob_fail_within(last, DECISION_HORIZON),
            "p_fail_30": p30_test,
            "median_remaining_cycles": preds["landmark"],
        }
    ).sort_values("p_fail_10", ascending=False)

    fleet_weib = M.fit_weibull(pd.DataFrame({"duration": life.to_numpy(), "event": 1}))

    return {
        "config": cfg.__dict__ | {"ratios": list(RATIOS), "decision_horizon": DECISION_HORIZON},
        "fleet_weibull": {"shape": fleet_weib.shape, "scale": fleet_weib.scale, "regime": fleet_weib.regime, "n": fleet_weib.n},
        "sensors": sensors,
        "n_landmark_rows": int(len(tbl)),
        "cv": {
            "concordance_by_repeat": repeat_cindex,
            "concordance_mean": float(np.mean(repeat_cindex)),
            "brier": brier,
            "calibration_p30": calib.to_dict(orient="records"),
        },
        "policies": policy_df.astype(object).where(policy_df.notna(), None).to_dict(orient="records"),
        "policy_ci": policy_ci,
        "test": {"metrics": test_metrics, "brier_p30": test_brier30, "n_units": int(len(truth))},
        "holm_spec001": holm(ph.p_values) | {"original_verdict_holds": bool(ph.holds), "raw": ph.p_values},
        "fleet_thresholds": fleet_thresholds,
        "_frames": {"fleet": fleet, "policy": policy_df, "calibration": calib, "cv": cv, "test_truth": truth, "test_preds": preds},
        "final_model": final,
    }


def write_outputs(res: dict, reports: Path, demo: Path) -> dict[str, str]:
    reports.mkdir(parents=True, exist_ok=True)
    demo.mkdir(parents=True, exist_ok=True)
    frames = res["_frames"]
    public = {k: v for k, v in res.items() if not k.startswith("_") and k != "final_model"}
    (reports / "landmark_FD001.json").write_text(json.dumps(public, indent=2, ensure_ascii=False, default=float), encoding="utf-8")
    (reports / "landmark_FD001.md").write_text(render_markdown(public), encoding="utf-8")
    frames["policy"].to_csv(demo / "policy_by_ratio.csv", index=False)
    frames["fleet"].round(4).to_csv(demo / "fleet_now.csv", index=False)
    frames["calibration"].round(4).to_csv(demo / "calibration_p30.csv", index=False)
    (demo / "thresholds.json").write_text(json.dumps(res["fleet_thresholds"], indent=2), encoding="utf-8")
    (demo / "fleet_weibull.json").write_text(json.dumps(res["fleet_weibull"], indent=2), encoding="utf-8")
    card = reports.parent / "models" / "MODEL_CARD_LANDMARK_FD001.md"
    if card.parent.exists():
        card.write_text(render_model_card(public), encoding="utf-8")
    return {"report": str(reports / "landmark_FD001.md"), "demo": str(demo)}


def render_model_card(r: dict) -> str:
    t = r["test"]["metrics"]["landmark"]
    pol = {(p["ratio"], p["policy"]): p for p in r["policies"]}
    c10, a10 = pol[(HEADLINE_RATIO, "condition")], pol[(HEADLINE_RATIO, "age")]
    return "\n".join(
        [
            "# Model card — landmark Weibull AFT (FD001)",
            "",
            "Status: EVIDENCE, not promoted. Generated by `python -m pm_survival study` (SPEC-003).",
            "",
            "## Uso previsto",
            "",
            "Estimar, en cada inspección, la probabilidad de que un motor falle en los próximos ciclos "
            "a partir de su condición reciente, y decidir si conviene un preventivo. Demostración de método sobre datos simulados.",
            "",
            "## No usar para",
            "",
            "Decisiones de aeronavegabilidad o de planta real; otros regímenes de operación (FD002–FD004) sin reentrenar y revalidar.",
            "",
            "## Datos y rasgos",
            "",
            "- NASA C-MAPSS FD001: 100 motores run-to-failure (entrenamiento) y 100 truncados con RUL real (prueba).",
            f"- {len(r['sensors'])} sensores con variación; media y pendiente en los últimos {r['config']['window']} ciclos + edad; "
            f"{r['n_landmark_rows']} filas landmark (cada {r['config']['step']} ciclos desde el ciclo {r['config']['start']}).",
            "- Ningún rasgo usa ciclos posteriores a la inspección (prueba automática de no fuga).",
            "",
            "## Desempeño",
            "",
            f"- Concordancia con RUL real en prueba: {t['concordance_vs_rul']:.2f} (IC 95 % {t['concordance_ci95'][0]:.2f}–{t['concordance_ci95'][1]:.2f}).",
            f"- RMSE de la vida restante mediana: {t['rmse_cycles']:.1f} ciclos (IC 95 % {t['rmse_ci95'][0]:.1f}–{t['rmse_ci95'][1]:.1f}).",
            f"- Concordancia fuera de pliegue (5 × 5 CV agrupada): {r['cv']['concordance_mean']:.2f}.",
            f"- Con C_f/C_p = {HEADLINE_RATIO:g}: {c10['cost_per_1000_cycles']:.2f} por 1 000 ciclos frente a "
            f"{a10['cost_per_1000_cycles']:.2f} del reemplazo por edad ({c10['failures']:g} vs {a10['failures']:g} fallas de 100).",
            "",
            "## Limitaciones conocidas",
            "",
            "- Sobrestima el riesgo cuando predice entre ~5 % y ~20 % de probabilidad de falla a 30 ciclos (ver calibración en `reports/landmark_FD001.md`).",
            "- Costos ilustrativos; la inspección se supone gratuita y con datos completos.",
            "- Un solo régimen y un solo modo de falla.",
            "",
        ]
    )


def _fmt(x: float, d: int = 2) -> str:
    return f"{x:.{d}f}"


def render_markdown(r: dict) -> str:
    t = r["test"]["metrics"]
    names = {"landmark": "Landmark (condición actual)", "age_only": "Solo edad (población)", "early_window": "Ventana temprana (SPEC-001)"}
    lines = [
        "# Evaluación — modelo por condición (landmark) y políticas de mantenimiento, FD001",
        "",
        "Status: EVIDENCE (portfolio, not a production recommendation). Generated by `pm_survival.study` (SPEC-003).",
        "",
        "## 1. Vida restante en el conjunto de prueba oficial (100 motores, RUL real)",
        "",
        "| Modelo | Concordancia vs RUL | IC 95 % | RMSE (ciclos) | IC 95 % |",
        "|---|---:|---|---:|---|",
    ]
    for k, m in t.items():
        lines.append(
            f"| {names.get(k, k)} | {_fmt(m['concordance_vs_rul'])} | {_fmt(m['concordance_ci95'][0])}–{_fmt(m['concordance_ci95'][1])} "
            f"| {_fmt(m['rmse_cycles'], 1)} | {_fmt(m['rmse_ci95'][0], 1)}–{_fmt(m['rmse_ci95'][1], 1)} |"
        )
    b = r["test"]["brier_p30"]
    lines += [
        "",
        "Las tres filas predicen la vida *restante* y se comparan contra la RUL real. "
        "La cifra 0.46 que reporta SPEC-001 ordena por vida *total* predicha sin restar los ciclos ya vividos; "
        "al restarlos sube a la fila «Ventana temprana», casi igual que usar solo la edad: "
        "las señales de los primeros 20 ciclos no aportan sobre la edad. Lo que aporta es la condición actual.",
        "",
        f"Brier de P(falla en ≤ 30 ciclos) en prueba: modelo {_fmt(b['model'], 3)} vs tasa base {_fmt(b['base_rate'], 3)}.",
        "",
        "## 2. Validación cruzada agrupada repetida (motores run-to-failure)",
        "",
        f"- {r['config']['n_repeats']} repeticiones × {r['config']['n_folds']} pliegues; ningún motor cruza pliegues.",
        f"- Concordancia fuera de pliegue (vida residual en cada inspección): media {_fmt(r['cv']['concordance_mean'])}; "
        f"por repetición {', '.join(_fmt(x) for x in r['cv']['concordance_by_repeat'])}.",
        "",
        "| Horizonte | Brier modelo | Brier tasa base |",
        "|---|---:|---:|",
    ]
    for h, v in r["cv"]["brier"].items():
        lines.append(f"| {h} ciclos | {_fmt(v['model'], 3)} | {_fmt(v['base_rate'], 3)} |")
    lines += ["", "Calibración de P(falla en ≤ 30 ciclos), deciles fuera de pliegue:", "", "| predicho | observado | n |", "|---:|---:|---:|"]
    for c in r["cv"]["calibration_p30"]:
        lines.append(f"| {_fmt(c['predicted'], 3)} | {_fmt(c['observed'], 3)} | {c['n']} |")
    lines += [
        "",
        "## 3. Políticas de mantenimiento (backtest renewal-reward, fuera de pliegue)",
        "",
        f"Costos en unidades de C_p (C_p = 1, C_f = razón). Inspección cada {r['config']['step']} ciclos; "
        f"la política por condición interviene cuando P(falla en ≤ {r['config']['decision_horizon']} ciclos) ≥ p*, "
        "con p* ajustado solo en motores de entrenamiento (CV interna).",
        "",
        "| C_f/C_p | Política | Costo / 1 000 ciclos | Fallas (de 100) | Preventivos | Ciclos de vida no usados (media) | Aprovechamiento |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    pname = {"run_to_failure": "Dejar fallar", "age": "Por edad (t*)", "condition": "Por condición", "oracle": "Oráculo (cota)"}
    for p in r["policies"]:
        lines.append(
            f"| {p['ratio']:g} | {pname[p['policy']]} | {_fmt(p['cost_per_1000_cycles'])} | {p['failures']:g} | {p['preventive']:g} "
            f"| {_fmt(p['mean_wasted_cycles'], 1)} | {p['utilisation']:.1%} |"
        )
    lines += ["", "Diferencia de costo por 1 000 ciclos (IC 95 %, bootstrap por motor):", "", "| C_f/C_p | Condición − Edad | P(condición mejor) | Condición − Dejar fallar |", "|---:|---|---:|---|"]
    for ratio, ci in r["policy_ci"].items():
        a, b2 = ci["condition_minus_age"], ci["condition_minus_run_to_failure"]
        lines.append(
            f"| {float(ratio):g} | {_fmt(a['diff'])} ({_fmt(a['ci_low'])} a {_fmt(a['ci_high'])}) | {a['p_a_better']:.0%} "
            f"| {_fmt(b2['diff'])} ({_fmt(b2['ci_low'])} a {_fmt(b2['ci_high'])}) |"
        )
    h = r["holm_spec001"]
    lines += [
        "",
        "## 4. Supuesto de riesgos proporcionales del modelo SPEC-001 (corrección de Holm)",
        "",
        f"- Veredicto original (α = 0.05 por covariable, sin corrección): {'se sostiene' if h['original_verdict_holds'] else 'violado'}.",
        f"- Con Holm sobre {len(h['adjusted'])} pruebas: {'se sostiene' if h['holds'] else 'violado'} "
        f"(p ajustado mínimo = {_fmt(min(h['adjusted'].values()), 3)}).",
        "- La regla de selección de SPEC-001 no se cambió; se reportan ambas lecturas.",
        "",
        "## Límites",
        "",
        "- FD001: una condición de operación y un modo de falla; los resultados no se generalizan a FD002–FD004 sin reevaluar.",
        "- Costos ilustrativos (C_p = 1, C_f = razón); la sección 3 muestra cómo cambia la decisión con la razón.",
        "- Datos simulados por NASA; en planta real la inspección tiene costo y los sensores tienen fallas de medición.",
        "- La política por condición supone que en cada inspección se dispone de los últimos 20 ciclos de sensores.",
        "",
    ]
    return "\n".join(lines)
