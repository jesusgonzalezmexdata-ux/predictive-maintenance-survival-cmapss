"""Decision app — ¿qué motores intervengo y cuánto me ahorra?

Run locally:
  streamlit run app/streamlit_app.py

Two modes:
* demo (default when the NASA files are absent): reads the derived artifacts in
  ``reports/demo`` produced by ``python -m pm_survival study``; no raw data is shipped.
* local data (``PM_RAW_DIR`` or the sidebar path points at C-MAPSS FD001): also fits the
  SPEC-001 baseline to explain individual engines.

Portfolio evidence on NASA simulation data, not a plant recommendation.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pm_survival import decision as Dec  # noqa: E402
from pm_survival import explain as X  # noqa: E402
from pm_survival import models as M  # noqa: E402

DEMO = ROOT / "reports" / "demo"
POLICY_NAMES = {
    "condition": "Por condición (este modelo)",
    "age": "Por edad t* (toda la flota)",
    "run_to_failure": "Dejar fallar",
    "oracle": "Oráculo (cota teórica)",
}

st.set_page_config(page_title="Mantenimiento por condición — C-MAPSS", layout="wide")


@st.cache_data
def load_demo() -> dict:
    return {
        "policy": pd.read_csv(DEMO / "policy_by_ratio.csv"),
        "fleet": pd.read_csv(DEMO / "fleet_now.csv"),
        "thresholds": json.loads((DEMO / "thresholds.json").read_text(encoding="utf-8")),
        "weibull": json.loads((DEMO / "fleet_weibull.json").read_text(encoding="utf-8")),
    }


demo = load_demo()
ratios = sorted(demo["policy"]["ratio"].unique().tolist())

st.title("¿Qué motores intervengo esta semana y cuánto me ahorra?")
st.caption(
    "Análisis de supervivencia por condición sobre NASA C-MAPSS FD001 (datos simulados). "
    "Evidencia de portafolio, no una recomendación de planta en producción."
)

ratio = st.sidebar.select_slider(
    "Cuánto cuesta una falla frente a un preventivo (C_f / C_p)",
    options=ratios,
    value=10.0 if 10.0 in ratios else ratios[len(ratios) // 2],
    format_func=lambda r: f"{r:g}×",
)
st.sidebar.caption("Costos en unidades del preventivo (C_p = 1). Cambia la razón para ver cómo se mueve la decisión.")

tab_week, tab_policy, tab_fleet, tab_asset = st.tabs(
    ["Decisión de la semana", "Comparación de políticas", "Confiabilidad de la flota", "Explicar un motor"]
)

# ------------------------------------------------------------------ 1. this week's decision
with tab_week:
    thr = float(demo["thresholds"][str(float(ratio))])
    fleet = demo["fleet"].copy()
    fleet["acción"] = "Operar"
    fleet.loc[fleet["p_fail_30"] >= 0.5, "acción"] = "Vigilar (riesgo alto a 30 ciclos)"
    fleet.loc[fleet["p_fail_10"] >= thr, "acción"] = "Intervenir ahora"
    counts = fleet["acción"].value_counts()

    c1, c2, c3 = st.columns(3)
    c1.metric("Intervenir ahora", int(counts.get("Intervenir ahora", 0)))
    c2.metric("Vigilar", int(counts.get("Vigilar (riesgo alto a 30 ciclos)", 0)))
    c3.metric("Operar", int(counts.get("Operar", 0)))
    st.markdown(
        f"Regla: intervenir cuando la probabilidad de falla en los próximos 10 ciclos es ≥ **{thr:.1%}**. "
        "Ese umbral se eligió minimizando el costo en motores de entrenamiento con la razón seleccionada."
    )
    show = fleet.rename(
        columns={
            "unit_id": "motor",
            "cycles_observed": "ciclos operados",
            "p_fail_10": "P(falla ≤ 10 ciclos)",
            "p_fail_30": "P(falla ≤ 30 ciclos)",
            "median_remaining_cycles": "vida restante mediana (ciclos)",
        }
    )
    st.dataframe(
        show,
        hide_index=True,
        use_container_width=True,
        column_config={
            "P(falla ≤ 10 ciclos)": st.column_config.ProgressColumn(format="%.2f", min_value=0.0, max_value=1.0),
            "P(falla ≤ 30 ciclos)": st.column_config.ProgressColumn(format="%.2f", min_value=0.0, max_value=1.0),
            "vida restante mediana (ciclos)": st.column_config.NumberColumn(format="%.0f"),
        },
    )
    st.caption("Flota = los 100 motores del conjunto de prueba oficial, en su último ciclo observado.")

# ------------------------------------------------------------------ 2. policy comparison
with tab_policy:
    pol = demo["policy"]
    sub = pol[pol["ratio"] == ratio].set_index("policy")
    cond, age = sub.loc["condition"], sub.loc["age"]
    saving = 1.0 - cond["cost_per_1000_cycles"] / age["cost_per_1000_cycles"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Ahorro frente a reemplazo por edad", f"{saving:.0%}")
    c2.metric("Fallas en servicio (de 100 motores)", f"{cond['failures']:g}", delta=f"{cond['failures'] - age['failures']:+g} vs edad", delta_color="inverse")
    c3.metric("Vida útil aprovechada", f"{cond['utilisation']:.0%}", delta=f"{cond['utilisation'] - age['utilisation']:+.0%} vs edad")

    table = sub.loc[["run_to_failure", "age", "condition", "oracle"]].reset_index()
    table["política"] = table["policy"].map(POLICY_NAMES)
    st.dataframe(
        table[["política", "cost_per_1000_cycles", "failures", "preventive", "mean_wasted_cycles", "utilisation"]].rename(
            columns={
                "cost_per_1000_cycles": "costo / 1 000 ciclos",
                "failures": "fallas",
                "preventive": "preventivos",
                "mean_wasted_cycles": "ciclos de vida no usados (media)",
                "utilisation": "aprovechamiento",
            }
        ),
        hide_index=True,
        use_container_width=True,
        column_config={
            "costo / 1 000 ciclos": st.column_config.NumberColumn(format="%.2f"),
            "ciclos de vida no usados (media)": st.column_config.NumberColumn(format="%.1f"),
            "aprovechamiento": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.subheader("Sensibilidad a la razón de costos")
    wide = pol[pol["policy"].isin(["age", "condition", "oracle"])].pivot(
        index="ratio", columns="policy", values="cost_per_1000_cycles"
    )[["age", "condition", "oracle"]].rename(columns=POLICY_NAMES)
    # same colours as the README figures: age = orange, condition = blue, oracle = aqua
    st.line_chart(wide, color=["#eb6834", "#2a78d6", "#1baf7a"], x_label="C_f / C_p", y_label="costo / 1 000 ciclos")
    st.caption(
        "Backtest fuera de pliegue (5 × 5 CV agrupada) sobre 100 motores run-to-failure. "
        "Detalle e intervalos de confianza: `reports/landmark_FD001.md`."
    )

# ------------------------------------------------------------------ 3. fleet reliability (age policy)
with tab_fleet:
    w = demo["weibull"]
    weib = M.WeibullResult(shape=w["shape"], scale=w["scale"], regime=w["regime"], n=w["n"], n_events=w["n"])
    cost = Dec.recompute_cost(weib, 1.0, float(ratio))
    c1, c2 = st.columns(2)
    c1.metric("Edad de reemplazo para toda la flota (t*)", f"{cost.t_star:.0f} ciclos")
    c2.metric("Probabilidad de seguir operando en t*", f"{cost.reliability_at_t_star:.0%}")
    st.info(Dec.intervention_message(cost))
    st.line_chart(Dec.reliability_curve(weib).set_index("ciclo"))
    st.caption(
        f"Weibull de flota: β = {weib.shape:.2f} → desgaste («{weib.regime}»). "
        "Esta es la política de referencia: trata a todos los motores igual."
    )

# ------------------------------------------------------------------ 4. explain one engine (needs local data)
with tab_asset:
    default_raw = os.environ.get("PM_RAW_DIR", str(ROOT / "data" / "raw" / "cmapss"))
    raw_dir = st.text_input("Carpeta local con C-MAPSS FD001", value=default_raw)
    if not (Path(raw_dir) / "train_FD001.txt").exists():
        st.info(
            "Para explicar un motor se necesitan los archivos NASA en tu equipo (no se redistribuyen). "
            "Extrae el zip con `python -m pm_survival extract --archive <zip> --out data/raw/cmapss`."
        )
    else:

        @st.cache_resource(show_spinner="Ajustando el modelo SPEC-001 (una vez por sesión)…")
        def _bundle(path: str):
            return Dec.fit_decision_bundle(path, cost_ratio=10.0)

        bundle = _bundle(raw_dir)
        pool = pd.concat([bundle.train_table, bundle.censored_table], ignore_index=True)
        unit = st.selectbox("Motor (unit_id)", sorted(pool["unit_id"].unique().tolist()))
        exp = X.explain_asset(bundle.model, pool[pool["unit_id"] == unit].head(1), top_k=5)
        st.write(exp.headline)
        st.dataframe(X.explanation_frame(exp), use_container_width=True, hide_index=True)
        st.caption(f"Modelo explicado: {bundle.model.kind} de SPEC-001 (ventana temprana). {bundle.selection_reason}")
