"""MVP 2 «Tu flota»: órdenes de trabajo → vidas censuradas → política por familia, lista semanal y retrospectiva."""

from __future__ import annotations

import io

import _support  # noqa: F401  (puts src/ on sys.path)
import pandas as pd
import pytest

from pm_survival import fleet as fl
from pm_survival import fleet_intake as fi
from pm_survival import fleet_report as rp


def to_xlsx(sheets: dict) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name, index=False)
    return buf.getvalue()


@pytest.fixture(scope="module")
def example():
    return fi.example_tables()


@pytest.fixture(scope="module")
def result(example):
    data, issues = fi.validate(fi.read_workbook(fi.template_bytes(example)))
    return data, issues, fl.analyse(data)


def test_template_roundtrip(result, example):
    data, issues, _ = result
    assert issues == []
    assert data["unit"] == "horas" and data["filas_validas"] == len(example[0])


def test_weibull_recovers_simulated_regimes(result):
    pol = result[2]["politica"].set_index("familia")
    mc, cp = pol.loc["Montacargas"], pol.loc["Compresor"]
    assert mc["beta_inf"] < 2.5 < mc["beta_sup"] and mc["desgaste_demostrado"]
    assert cp["beta_inf"] < 1.0 < cp["beta_sup"] and not cp["desgaste_demostrado"]
    assert pd.isna(cp["t_optimo"]) and "no hay desgaste demostrado" in cp["recomendacion"]
    assert 1900 <= mc["intervalo_actual"] <= 2100 and mc["t_optimo"] < mc["intervalo_actual"]
    assert mc["ahorro_anual"] > 0 and 0 < mc["ahorro_pct"] < 1


def test_weekly_list_respects_capacity(result):
    r = result[2]
    week, cap = r["semana"], r["settings"].capacidad_semana
    assert (week["estado"] == "Intervenir esta semana").sum() <= cap
    assert week["p_falla_semana"].is_monotonic_decreasing
    assert set(week.loc[week["familia"] == "Compresor", "estado"]) == {"Operar · vigilar condición"}
    due = week[week["estado"].str.startswith(("Intervenir", "Vencido"))]
    assert (due["edad"] >= due["t_optimo"]).all()


def test_backtest_beats_random(result):
    bt = result[2]["retrospectiva"]
    assert bt["fallas"] > 20 and bt["captura"] > 2 * bt["captura_al_azar"]


def test_dirty_export_is_reported_by_row():
    data, issues = fi.validate(fi.read_workbook(fi.example_with_errors()))
    errors = {i.fila: i.mensaje for i in issues if i.nivel == "error"}
    assert set(errors) == {6, 8, 10}
    assert "Fecha no reconocida" in errors[6] and "Inspección" in errors[8] and "vacío" in errors[10]
    notes = " ".join(i.mensaje for i in issues if i.nivel == "aviso")
    assert "duplicadas" in notes and "otra forma" in notes
    assert data["filas_leidas"] - data["filas_validas"] == 4
    assert set(data["orders"]["tipo"]) == {"correctiva", "preventiva"}


def test_calendar_days_when_no_hour_meter(example):
    orders, _ = example
    data, issues = fi.validate(fi.read_workbook(to_xlsx({"ordenes": orders.drop(columns="horometro")})))
    assert data["unit"] == "días" and any("días de calendario" in i.mensaje for i in issues)
    r = fl.analyse(data)
    life = r["vidas"]
    assert not r["politica"].empty and (life.loc[~life["abierta"], "duracion"] > 0).all() and (life["duracion"] >= 0).all()


def test_commissioning_inside_record_opens_first_life():
    orders = pd.DataFrame({"equipo": ["A"] * 3, "fecha": pd.to_datetime(["2025-01-10", "2025-03-01", "2025-05-01"]),
                           "tipo": ["preventiva", "correctiva", "preventiva"], "familia": "F", "horometro": [100, 500, 900]})
    other = pd.DataFrame({"equipo": ["B"], "fecha": pd.to_datetime(["2024-12-01"]), "tipo": ["preventiva"], "familia": "F",
                          "horometro": [50]})
    equip = pd.DataFrame({"equipo": ["A", "B"], "familia": "F", "fecha_alta": pd.to_datetime(["2025-01-02", "2020-01-01"]),
                          "horometro_actual": [1000, 400]})
    data, _ = fi.validate(fi.read_workbook(to_xlsx({"ordenes": pd.concat([orders, other]), "equipos": equip})))
    life = fl.lives(data)
    a, b = life[life["equipo"] == "A"], life[life["equipo"] == "B"]
    assert a["duracion"].tolist() == [100, 400, 400, 100] and a["evento"].tolist() == [0, 1, 0, 0]
    assert b["duracion"].tolist() == [350] and b["abierta"].all()


def test_fatal_problems_raise(example):
    orders, _ = example
    with pytest.raises(fi.DataError, match="tipo"):
        fi.validate(fi.read_workbook(to_xlsx({"ordenes": orders.drop(columns="tipo")})))
    with pytest.raises(fi.DataError, match="ordenes"):
        fi.validate(fi.read_workbook(to_xlsx({"otra": orders})))


def test_report_is_escaped_and_complete(result):
    data, issues, r = result
    page = rp.report_html(r, issues, "<b>x</b>", (data["filas_leidas"], data["filas_validas"]))
    assert "<b>x</b>" not in page and "&lt;b&gt;x&lt;/b&gt;" in page
    for text in ("Política por familia", "Lista de la semana", "Retrospectiva", "ISO 14224"):
        assert text in page
    assert "http" not in page
