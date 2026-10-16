"""Reporte de una página (HTML imprimible) con la política por familia y la lista de la semana."""
from __future__ import annotations

import datetime as dt
import html

import pandas as pd

REFS = [
    ("ISO 9001 · 7.1.3", "Infraestructura: mantenimiento planificado del equipo"),
    ("IATF 16949 · 8.5.1.5", "Mantenimiento productivo total: frecuencia del preventivo basada en datos"),
    ("ISO 14224", "Registro de fallas y mantenimiento: cada orden distingue falla de preventivo"),
    ("ISO 55001 · 6.2", "Objetivos de gestión de activos y decisión por costo de ciclo de vida"),
]


def mxn(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"${v / 1e6:,.2f} M" if abs(v) >= 1e6 else f"${v:,.0f}"


def _e(x) -> str:
    return html.escape(str(x))


def _table(df: pd.DataFrame) -> str:
    head = "".join(f"<th>{_e(c)}</th>" for c in df.columns)
    body = "".join("<tr>" + "".join(f"<td>{_e(v)}</td>" for v in row) + "</tr>" for row in df.itertuples(index=False))
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def headline(r) -> str:
    pol, week = r["politica"], r["semana"]
    if pol.empty:
        return "Ninguna familia tiene fallas suficientes para estimar su confiabilidad."
    total = pol["ahorro_anual"].clip(lower=0).sum()
    top = pol.sort_values("ahorro_anual", ascending=False).iloc[0]
    text = (f"Ajustar la política de mantenimiento ahorraría ≈ {mxn(total)} al año. La mayor parte está en «{top['familia']}»: "
            f"{top['recomendacion']}")
    if not week.empty:
        n = int((week["estado"] == "Intervenir esta semana").sum())
        late = int((week["estado"] == "Vencido · sin capacidad esta semana").sum())
        text += f" Esta semana: {n} equipos a intervenir" + (f" y {late} vencidos más sin capacidad." if late else ".")
    return text


def report_html(r, issues=None, site: str = "Planta", data_rows=None) -> str:
    pol, week, bt, unit = r["politica"], r["semana"], r["retrospectiva"], r["unidad"]
    issues = issues or []
    parts = [f"<h1>Lista semanal de intervención · {_e(site)}</h1>",
             f"<p class='meta'>Corte {r['corte']:%d/%m/%Y} · tiempo en {unit} · generado el {dt.date.today():%d/%m/%Y} · "
             "Jesús R. L. González</p>", f"<p class='lead'>{_e(headline(r))}</p>"]
    if data_rows:
        err = sum(i.nivel == "error" for i in issues)
        parts.append(f"<h2>1 · Datos</h2><p>{data_rows[1]:,} de {data_rows[0]:,} órdenes válidas · {err} excluidas por error · "
                     f"{len(r['vidas']):,} vidas reconstruidas. Los datos se procesaron en el equipo del usuario.</p>")
    if not pol.empty:
        t = pd.DataFrame({
            "Familia": pol["familia"], "Equipos": pol["equipos"], "Fallas": pol["fallas"],
            "β (IC 95 %)": [f"{b:.2f} ({lo:.2f}–{hi:.2f})" for b, lo, hi in zip(pol["beta"], pol["beta_inf"], pol["beta_sup"], strict=True)],
            f"Intervalo actual ({unit})": pol["intervalo_actual"].map(lambda v: "—" if pd.isna(v) else f"{v:,.0f}"),
            f"Intervalo óptimo ({unit})": pol["t_optimo"].map(lambda v: "no aplica" if pd.isna(v) else f"{v:,.0f}"),
            "Intervenciones/semana": pol["carga_semanal"].map(lambda v: "—" if pd.isna(v) else f"{v:.1f}"),
            "Ahorro anual": pol["ahorro_anual"].map(mxn), "Ahorro %": pol["ahorro_pct"].map("{:.0%}".format)})
        parts.append("<h2>2 · Política por familia</h2>" + _table(t) + "<ul>"
                     + "".join(f"<li><b>{_e(f)}:</b> {_e(txt)}</li>" for f, txt in zip(pol["familia"], pol["recomendacion"], strict=True))
                     + "</ul><p class='note'>β &gt; 1 con su intervalo completo por encima de 1 = desgaste demostrado: solo entonces "
                       "el preventivo por edad reduce costo. Con β ≈ 1 las fallas son aleatorias y conviene inspección por condición.</p>")
    if r["familias_sin_modelo"]:
        parts.append(f"<p class='note'>Sin fallas suficientes para modelar: {_e(', '.join(r['familias_sin_modelo']))}.</p>")
    if not week.empty:
        w = week.head(20)
        parts.append("<h2>3 · Lista de la semana</h2>" + _table(pd.DataFrame({
            "Equipo": w["equipo"], "Familia": w["familia"], f"Edad ({unit})": w["edad"].map("{:,.0f}".format),
            "P(falla en 7 días)": w["p_falla_semana"].map("{:.1%}".format), "Acción": w["estado"]}))
            + f"<p class='note'>Primeros 20 de {len(week)} equipos, ordenados por probabilidad de falla en los próximos 7 días. "
              f"Capacidad del taller: {r['settings'].capacidad_semana} intervenciones por semana.</p>")
    parts.append("<h2>4 · ¿Qué tan confiable es?</h2><ul>")
    if bt:
        verdict = "mejor" if bt["captura"] > bt["captura_al_azar"] else "<b>no mejor</b>"
        parts.append(f"<li>Retrospectiva desde el {bt['desde']:%d/%m/%Y} ({bt['semanas']} semanas, modelo ajustado solo con el "
                     f"histórico previo): la lista habría anticipado {bt['anticipadas']} de {bt['fallas']} fallas "
                     f"({bt['captura']:.0%}), {verdict} que elegir {r['settings'].capacidad_semana} equipos al azar "
                     f"({bt['captura_al_azar']:.0%}).</li>")
    else:
        parts.append("<li>Histórico corto o sin fallas recientes: no hay retrospectiva.</li>")
    parts.append("<li>Supuesto: cada orden deja el equipo como nuevo. Si las reparaciones son parciales, la edad real es mayor "
                 "y el intervalo óptimo, más corto.</li><li>La edad usa el horómetro cuando existe; si no, días de calendario.</li>"
                 "<li>Modelo por edad, sin sensores: la versión con lecturas de condición ordena mejor dentro de cada familia.</li></ul>")
    if bt and bt["captura"] <= bt["captura_al_azar"]:
        parts.append("<p class='warn'>Criterio de abandono: la lista no supera al azar en la retrospectiva. No pasar a modo sombra.</p>")
    parts.append("<h2>Referencias</h2>" + _table(pd.DataFrame(REFS, columns=["Requisito", "Cómo se atiende"])))
    css = """body{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;color:#1b1b1b;max-width:900px;margin:24px auto;
padding:0 16px;font-size:14px;line-height:1.5}h1{font-size:22px;margin-bottom:2px}h2{font-size:16px;margin:22px 0 6px;
border-bottom:2px solid #2a78d6;padding-bottom:2px}.meta{color:#666;margin-top:0}.lead{font-size:15px;background:#f3f6fb;
padding:10px 12px;border-left:4px solid #2a78d6}table{border-collapse:collapse;margin:6px 0;font-size:13px}th,td{border:1px solid #ddd;
padding:4px 8px;text-align:left}th{background:#f5f5f2}.note{color:#555;font-size:12.5px}.warn{background:#fdecea;padding:8px 10px;
border-left:4px solid #d03b3b}@media print{body{margin:0}h2{break-after:avoid}}"""
    return ("<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Lista semanal · "
            f"{_e(site)}</title><style>{css}</style></head><body>" + "".join(parts) + "</body></html>")
