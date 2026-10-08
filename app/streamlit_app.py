"""Decision surface — ¿cuándo conviene el preventivo?

Run locally:
  streamlit run app/streamlit_app.py

Deploy: Streamlit Community Cloud / Docker (see README).
"""
from __future__ import annotations

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

st.set_page_config(page_title="Mantenimiento predictivo — decisión de costo", layout="wide")

st.title("¿Cuándo conviene el preventivo?")
st.caption(
    "Baseline gobernado sobre NASA C-MAPSS FD001 (supervivencia + costo). "
    "No es una recomendación de planta en producción."
)

default_raw = ROOT / "data" / "raw" / "cmapss"
raw_dir = st.sidebar.text_input("Carpeta de datos locales (C-MAPSS)", value=str(default_raw))
cp = st.sidebar.number_input("Costo del preventivo C_p (USD)", min_value=1.0, value=500.0, step=50.0)
cf = st.sidebar.number_input("Costo de la falla correctiva C_f (USD)", min_value=2.0, value=5000.0, step=100.0)
st.sidebar.markdown(f"**Relación C_f / C_p** = {cf / cp:.1f}")

if not Path(raw_dir).exists():
    st.error(
        "No encuentro los datos. Extrae el archivo NASA localmente, por ejemplo:\n\n"
        "`python -m pm_survival extract --archive <zip> --out data/raw/cmapss`"
    )
    st.stop()

if cf <= cp:
    st.warning("Para que el preventivo tenga sentido económico, C_f debe ser mayor que C_p.")
    st.stop()


@st.cache_resource(show_spinner="Ajustando el baseline (una vez por sesión)…")
def _bundle(path: str):
    return Dec.fit_decision_bundle(path, cost_ratio=10.0)


try:
    bundle = _bundle(raw_dir)
except Exception as exc:  # noqa: BLE001 — show operator-facing error
    st.exception(exc)
    st.stop()

cost = Db.recompute_cost(bundle.weibull, cp, cf)

col1, col2, col3 = st.columns(3)
col1.metric("Tiempo de intervención sugerido (t*)", f"{cost.t_star:.0f} ciclos")
col2.metric("Probabilidad de seguir operando en t*", f"{cost.reliability_at_t_star:.0%}")
col3.metric("Costo esperado por ciclo en t*", f"{cost.cost_rate_at_t_star:.4f} × C_p")

st.info(Db.intervention_message(cost))

curve = Db.reliability_curve(bundle.weibull)
st.subheader("Confiabilidad del activo (promedio de flota)")
st.line_chart(curve.set_index("ciclo"))
st.caption(
    f"Forma Weibull β = {bundle.weibull.shape:.2f} → régimen «{bundle.weibull.regime}». "
    f"Modelo por activo: {bundle.model.kind}."
)

st.subheader("Explicabilidad por activo (impulsores de riesgo)")
pool = pd.concat([bundle.train_table, bundle.censored_table], ignore_index=True)
unit = st.selectbox("Selecciona un activo (unit_id)", sorted(pool["unit_id"].unique().tolist()))
row = pool[pool["unit_id"] == unit].head(1)
exp = X.explain_asset(bundle.model, row, top_k=5)
st.write(exp.headline)
st.dataframe(X.explanation_frame(exp), use_container_width=True, hide_index=True)

with st.expander("Notas técnicas (para revisores)"):
    st.markdown(
        f"""
- Dataset: NASA C-MAPSS FD001 (público). Taxonomía L2: `docs/taxonomy.md`.
- Censura: trenes con falla observada; test truncado (`event = 0`).
- Pendientes solo en los primeros 20 ciclos (sin filtrar el futuro).
- Selección de modelo: {bundle.selection_reason}
- Evidencia offline: `reports/eval_FD001.md`, `models/MODEL_CARD_FD001.md`.
"""
    )
