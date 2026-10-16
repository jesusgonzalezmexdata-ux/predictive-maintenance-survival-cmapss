"""Modo «Tu flota»: lista semanal de intervención a partir de las órdenes de trabajo del usuario."""
from __future__ import annotations

import streamlit as st

from . import fleet as fl
from . import fleet_intake as fi
from . import fleet_report as rp


def _md(text: str) -> str:
    return text.replace("$", "\\$")


@st.cache_data(show_spinner=False)
def _template():
    return fi.template_bytes()


@st.cache_data(show_spinner=False)
def _dirty_example():
    return fi.example_with_errors()


@st.cache_data(show_spinner="Reconstruyendo vidas y ajustando la confiabilidad…")
def _run(content: bytes, settings: fl.Settings):
    data, issues = fi.validate(fi.read_workbook(content))
    return data, issues, fl.analyse(data, settings)


def render():
    st.subheader("Lista semanal de intervención con tus órdenes de trabajo")
    st.markdown("Sube la exportación de tu sistema de mantenimiento (SAP PM, Maximo o Excel): equipo, fecha y tipo de orden. "
                "Obtienes el intervalo preventivo óptimo por familia, el ahorro anual y la lista de equipos a intervenir esta "
                "semana. **El archivo se procesa en tu navegador: no se envía a ningún servidor.**")
    st.download_button("Descargar plantilla de Excel (con una flota de ejemplo)", _template(), "plantilla_ordenes.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    up = st.file_uploader("Tu archivo .xlsx", type=["xlsx"])
    if st.button("O prueba con un archivo de ejemplo que trae errores de captura"):
        st.session_state["ejemplo_flota"] = True
    site = st.text_input("Nombre de la planta o flota (aparece en el reporte)", "Mi planta")
    a, b, c = st.columns(3)
    cp = a.number_input("Costo de un preventivo (MXN)", 1, 10_000_000, 2_500, 500)
    cf = b.number_input("Costo de una falla: reparación + paro (MXN)", 2, 50_000_000, 15_000, 1_000)
    cap = c.number_input("Preventivos que el taller puede hacer por semana", 1, 500, 5, 1)

    if up is not None:
        content = up.getvalue()
    elif st.session_state.get("ejemplo_flota"):
        content = _dirty_example()
        st.caption("Analizando el archivo de ejemplo: 40 montacargas y 25 compresores simulados, exportados con encabezados "
                   "distintos, tipos de orden abreviados, 3 filas con error y una orden duplicada.")
    else:
        st.info("Para probar, descarga la plantilla y súbela tal cual, o usa el archivo de ejemplo con errores.")
        return
    if cf <= cp:
        st.error("El costo de una falla debe ser mayor que el de un preventivo; si no, nunca conviene intervenir antes.")
        return
    try:
        data, issues, r = _run(content, fl.Settings(costo_preventivo=float(cp), costo_falla=float(cf), capacidad_semana=int(cap)))
    except fi.DataError as exc:
        st.error(str(exc))
        return

    errors = [i for i in issues if i.nivel == "error"]
    st.markdown(f"**{data['filas_validas']:,} de {data['filas_leidas']:,} órdenes válidas** · {len(errors)} excluidas · "
                f"{len(issues) - len(errors)} avisos · {len(r['vidas']):,} vidas reconstruidas · tiempo en {r['unidad']}")
    if issues:
        with st.expander("Ver errores y avisos de los datos", expanded=bool(errors)):
            st.dataframe(fi.issues_frame(issues), hide_index=True)
    st.success(_md(rp.headline(r)))

    pol = r["politica"]
    if not pol.empty:
        st.markdown("**Política por familia**")
        st.dataframe(pol[["familia", "equipos", "fallas", "beta", "beta_inf", "beta_sup", "intervalo_actual", "t_optimo",
                          "carga_semanal", "ahorro_anual", "ahorro_pct"]].rename(columns={
                     "familia": "Familia", "equipos": "Equipos", "fallas": "Fallas", "beta": "β", "beta_inf": "β mín (95 %)",
                     "beta_sup": "β máx (95 %)", "intervalo_actual": f"Intervalo actual ({r['unidad']})",
                     "t_optimo": f"Intervalo óptimo ({r['unidad']})", "carga_semanal": "Intervenciones/semana",
                     "ahorro_anual": "Ahorro anual (MXN)", "ahorro_pct": "Ahorro %"}).style.format({
                     "β": "{:.2f}", "β mín (95 %)": "{:.2f}", "β máx (95 %)": "{:.2f}", f"Intervalo actual ({r['unidad']})": "{:,.0f}",
                     f"Intervalo óptimo ({r['unidad']})": "{:,.0f}", "Intervenciones/semana": "{:.1f}",
                     "Ahorro anual (MXN)": "${:,.0f}", "Ahorro %": "{:.0%}"}, na_rep="—"), hide_index=True)
        for fam, txt in zip(pol["familia"], pol["recomendacion"], strict=True):
            st.markdown(f"- **{fam}:** {_md(txt)}")
    week = r["semana"]
    if not week.empty:
        st.markdown(f"**Lista de la semana** (capacidad: {cap} intervenciones)")
        st.dataframe(week[["equipo", "familia", "edad", "p_falla_semana", "estado"]].rename(columns={
                     "equipo": "Equipo", "familia": "Familia", "edad": f"Edad ({r['unidad']})",
                     "p_falla_semana": "P(falla en 7 días)", "estado": "Acción"}),
                     hide_index=True, column_config={
                         "P(falla en 7 días)": st.column_config.ProgressColumn(format="%.3f", min_value=0.0, max_value=float(week["p_falla_semana"].max())),
                         f"Edad ({r['unidad']})": st.column_config.NumberColumn(format="%.0f")})
    bt = r["retrospectiva"]
    if bt:
        msg = (f"Retrospectiva: en las últimas {bt['semanas']} semanas la lista habría anticipado {bt['anticipadas']} de "
               f"{bt['fallas']} fallas ({bt['captura']:.0%}), contra {bt['captura_al_azar']:.0%} eligiendo al azar.")
        (st.caption if bt["captura"] > bt["captura_al_azar"] else st.warning)(msg)
    page = rp.report_html(r, issues, site, (data["filas_leidas"], data["filas_validas"]))
    st.download_button("Descargar reporte de una página (HTML, imprimible a PDF)", page.encode("utf-8"),
                       "lista_semanal.html", "text/html", type="primary")
