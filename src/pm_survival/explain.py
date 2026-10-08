"""Local explicability for a single asset (SPEC-002 / DoD-B2).

Uses the fitted model's standardized covariate contributions (coefficient ×
scaled value). This is intentional XAI without the ``shap`` dependency: for Cox
it is the linear predictor contribution; for Weibull AFT it is the contribution
to log-scale (sign flipped so that a positive contribution means *higher risk /
earlier failure*).

Business copy helpers map feature names through the L2 taxonomy labels.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import models as M

# Feature → short business label (aligned with docs/taxonomy.md)
FEATURE_LABELS: dict[str, str] = {
    "op_setting_1_early": "Régimen: altitud (nivel temprano)",
    "op_setting_1_slope": "Régimen: altitud (tendencia temprana)",
    "op_setting_2_early": "Régimen: Mach (nivel temprano)",
    "op_setting_2_slope": "Régimen: Mach (tendencia temprana)",
    "op_setting_3_early": "Régimen: throttle (nivel temprano)",
    "op_setting_3_slope": "Régimen: throttle (tendencia temprana)",
    "sensor_2_early": "Temperatura LPC (nivel) — desgaste térmico L2-T",
    "sensor_2_slope": "Temperatura LPC (tendencia) — desgaste térmico L2-T",
    "sensor_3_early": "Temperatura HPC (nivel) — desgaste térmico L2-T",
    "sensor_3_slope": "Temperatura HPC (tendencia) — desgaste térmico L2-T",
    "sensor_4_early": "Temperatura LPT (nivel) — desgaste térmico L2-T",
    "sensor_4_slope": "Temperatura LPT (tendencia) — desgaste térmico L2-T",
    "sensor_6_early": "Presión bypass (nivel) — eficiencia L2-P",
    "sensor_6_slope": "Presión bypass (tendencia) — eficiencia L2-P",
    "sensor_7_early": "Presión HPC (nivel) — eficiencia L2-P",
    "sensor_7_slope": "Presión HPC (tendencia) — eficiencia L2-P",
    "sensor_11_early": "Presión estática HPC (nivel) — L2-P",
    "sensor_11_slope": "Presión estática HPC (tendencia) — L2-P",
    "sensor_15_early": "Bypass ratio (nivel) — flujo L2-F",
    "sensor_15_slope": "Bypass ratio (tendencia) — flujo L2-F",
    "sensor_17_early": "Bleed enthalpy (nivel) — L2-T/F",
    "sensor_17_slope": "Bleed enthalpy (tendencia) — L2-T/F",
    "sensor_20_early": "Coolant bleed W31 (nivel) — L2-F",
    "sensor_20_slope": "Coolant bleed W31 (tendencia) — L2-F",
    "sensor_21_early": "Coolant bleed W32 (nivel) — L2-F",
    "sensor_21_slope": "Coolant bleed W32 (tendencia) — L2-F",
}


def business_label(feature: str) -> str:
    if feature in FEATURE_LABELS:
        return FEATURE_LABELS[feature]
    base = feature.replace("_early", "").replace("_slope", "")
    kind = "tendencia temprana" if feature.endswith("_slope") else "nivel temprano"
    return f"{base} ({kind}) — ver taxonomía L2"


@dataclass(frozen=True)
class Driver:
    feature: str
    label: str
    contribution: float
    pct_of_abs: float
    direction: str  # "aumenta_riesgo" | "reduce_riesgo"


@dataclass(frozen=True)
class AssetExplanation:
    unit_id: int
    model_kind: str
    drivers: list[Driver]
    headline: str


def _signed_contributions(model: M.CoxResult | M.WeibullAFTResult, row: pd.DataFrame) -> dict[str, float]:
    """Per-covariate contribution to the risk-oriented score."""
    z = model.scaler.transform(row, model.covariates).iloc[0]
    out: dict[str, float] = {}
    for c in model.covariates:
        coef = float(model.coefficients.get(c, 0.0))
        val = float(z[c])
        # Cox: positive coef * positive z → higher hazard.
        # AFT: positive coef on lambda increases scale (longer life) → flip for risk.
        if model.kind == "weibull_aft":
            out[c] = -coef * val
        else:
            out[c] = coef * val
    return out


def explain_asset(model: M.CoxResult | M.WeibullAFTResult, row: pd.DataFrame, top_k: int = 5) -> AssetExplanation:
    """Explain one asset row from the survival table (must include unit_id + covariates)."""
    if len(row) != 1:
        raise ValueError("explain_asset expects a single-row DataFrame")
    unit_id = int(row["unit_id"].iloc[0])
    contrib = _signed_contributions(model, row)
    total_abs = sum(abs(v) for v in contrib.values()) or 1.0
    drivers = []
    for feat, value in sorted(contrib.items(), key=lambda kv: -abs(kv[1])):
        drivers.append(
            Driver(
                feature=feat,
                label=business_label(feat),
                contribution=float(value),
                pct_of_abs=100.0 * abs(value) / total_abs,
                direction="aumenta_riesgo" if value > 0 else "reduce_riesgo",
            )
        )
    top = drivers[: max(1, top_k)]
    if top:
        lead = top[0]
        verb = "aumentó" if lead.direction == "aumenta_riesgo" else "redujo"
        headline = (
            f"En el activo {unit_id}, el principal impulsor es «{lead.label}»: "
            f"{verb} el riesgo relativo (~{lead.pct_of_abs:.0f}% del peso explicativo local)."
        )
    else:
        headline = f"Activo {unit_id}: sin covariables para explicar."
    return AssetExplanation(unit_id=unit_id, model_kind=model.kind, drivers=top, headline=headline)


def explanation_frame(exp: AssetExplanation) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "factor": d.label,
                "impacto": "Aumenta riesgo" if d.direction == "aumenta_riesgo" else "Reduce riesgo",
                "peso_%": round(d.pct_of_abs, 1),
            }
            for d in exp.drivers
        ]
    )
