"""Entrada de datos de mantenimiento real: plantilla de Excel con órdenes de trabajo y validación en español.

python -m pm_survival.fleet_intake plantilla_ordenes.xlsx   # escribe la plantilla con una flota de ejemplo

Cada orden correctiva cierra una vida con falla; cada preventiva la cierra sin falla (dato censurado).
"""
from __future__ import annotations

import io
import sys
import unicodedata
from dataclasses import dataclass

import numpy as np
import pandas as pd

REQUIRED = ["equipo", "fecha", "tipo"]
OPTIONAL = ["familia", "horometro"]
EQUIP_COLS = ["equipo", "familia", "fecha_alta", "horometro_actual"]
ALIASES = {"activo": "equipo", "maquina": "equipo", "id_equipo": "equipo", "fecha_orden": "fecha",
           "tipo_orden": "tipo", "tipo_de_orden": "tipo", "clase": "familia", "tipo_equipo": "familia",
           "horas": "horometro", "horas_uso": "horometro", "lectura_horometro": "horometro"}
CORRECTIVE = {"correctiva", "correctivo", "corr", "falla", "averia", "emergencia", "cm", "breakdown", "corrective"}
PREVENTIVE = {"preventiva", "preventivo", "prev", "pm", "programada", "programado", "preventive", "planned"}
MIN_FAILURES = 5

INSTRUCTIONS = [
    ("Hoja", "Columna", "Obligatoria", "Qué poner"),
    ("ordenes", "equipo", "Sí", "Código del equipo; siempre escrito igual"),
    ("ordenes", "fecha", "Sí", "Fecha de la orden (dd/mm/aaaa)"),
    ("ordenes", "tipo", "Sí", "Correctiva (falla) o Preventiva; se aceptan variantes como CORR, PM, Falla"),
    ("ordenes", "familia", "No", "Tipo de equipo (montacargas, compresor…); cada familia se analiza por separado"),
    ("ordenes", "horometro", "No", "Lectura del horómetro en la orden; si falta, el análisis usa días de calendario"),
    ("equipos", "equipo, familia", "No", "Lista de equipos activos; incluye los que nunca han tenido orden"),
    ("equipos", "fecha_alta", "No", "Fecha de puesta en servicio; permite usar la primera vida de cada equipo"),
    ("equipos", "horometro_actual", "No", "Lectura actual del horómetro, para la lista de esta semana"),
    ("", "", "", "Supuesto: cada orden, correctiva o preventiva, deja el equipo como nuevo. Mínimo 5 fallas por familia; "
                 "ideal 20 o más. Los datos se procesan en tu navegador y no se envían a ningún servidor."),
]


class DataError(ValueError):
    """El archivo no se puede analizar."""


@dataclass
class Issue:
    nivel: str
    hoja: str
    fila: int | None
    mensaje: str


def _key(text) -> str:
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return "_".join(text.strip().lower().replace("-", " ").split())


def _columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns=lambda c: ALIASES.get(_key(c), _key(c))).dropna(how="all")


def read_workbook(source) -> dict[str, pd.DataFrame]:
    if isinstance(source, (bytes, bytearray)):
        source = io.BytesIO(source)
    try:
        sheets = pd.read_excel(source, sheet_name=None)
    except Exception as exc:
        raise DataError(f"No se pudo leer el archivo como Excel (.xlsx): {exc}") from exc
    return {_key(name): _columns(df) for name, df in sheets.items()}


def _text(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)


def _kind(value) -> str | None:
    key = _key(value) if pd.notna(value) else ""
    if key in CORRECTIVE:
        return "correctiva"
    if key in PREVENTIVE:
        return "preventiva"
    return None


def validate(book: dict[str, pd.DataFrame]):
    """Devuelve (datos, avisos). Filas con error se excluyen y se reportan con su fila de Excel."""
    issues: list[Issue] = []
    if "ordenes" not in book:
        raise DataError("Falta la hoja «ordenes». Usa la plantilla descargable.")
    o = book["ordenes"].copy()
    missing = [c for c in REQUIRED if c not in o.columns]
    if missing:
        raise DataError("A la hoja «ordenes» le faltan columnas obligatorias: " + ", ".join(missing))
    rows = pd.Series(o.index + 2, index=o.index)
    bad = pd.Series(False, index=o.index)

    o["equipo"] = _text(o["equipo"])
    empty = o["equipo"].isna() | (o["equipo"] == "")
    for r in o.index[empty]:
        issues.append(Issue("error", "ordenes", int(rows[r]), "«equipo» está vacío"))
    bad |= empty

    fecha = pd.to_datetime(o["fecha"], errors="coerce", dayfirst=True)
    for r in o.index[fecha.isna() & ~bad]:
        issues.append(Issue("error", "ordenes", int(rows[r]), f"Fecha no reconocida: {o.at[r, 'fecha']!r}"))
    bad |= fecha.isna()
    o["fecha"] = fecha.dt.normalize()

    kind = o["tipo"].map(_kind)
    for r in o.index[kind.isna() & ~bad]:
        issues.append(Issue("error", "ordenes", int(rows[r]),
                            f"Tipo de orden no reconocido: {o.at[r, 'tipo']!r} (usa Correctiva o Preventiva)"))
    bad |= kind.isna()
    variants = int((o["tipo"].astype(str).str.strip().str.lower() != kind).sum())
    if variants:
        issues.append(Issue("aviso", "ordenes", None, f"{variants} tipos de orden escritos de otra forma se unificaron"))
    o["tipo"] = kind

    if "familia" in o.columns:
        o["familia"] = _text(o["familia"]).fillna("Sin familia").astype(object)
    else:
        o["familia"] = "Todos"
        issues.append(Issue("aviso", "ordenes", None, "Sin columna «familia»: todos los equipos se analizan juntos"))

    use_hours = "horometro" in o.columns and pd.to_numeric(o["horometro"], errors="coerce").notna().mean() >= 0.8
    if "horometro" in o.columns:
        h = pd.to_numeric(o["horometro"], errors="coerce")
        neg = h < 0
        for r in o.index[neg & ~bad]:
            issues.append(Issue("error", "ordenes", int(rows[r]), f"Horómetro negativo: {o.at[r, 'horometro']!r}"))
        bad |= neg
        o["horometro"] = h
        if not use_hours:
            issues.append(Issue("aviso", "ordenes", None,
                                "Menos de 80 % de órdenes con horómetro: el análisis usa días de calendario"))
    else:
        issues.append(Issue("aviso", "ordenes", None, "Sin columna «horometro»: el análisis usa días de calendario"))

    dups = o.duplicated(["equipo", "fecha", "tipo"], keep="first") & ~bad
    if dups.any():
        issues.append(Issue("aviso", "ordenes", None, f"{int(dups.sum())} órdenes duplicadas (mismo equipo, fecha y tipo) "
                            f"eliminadas: filas {', '.join(map(str, rows[dups].head(10)))}"))
    bad |= dups

    clean = o[~bad].copy()
    if clean.empty:
        raise DataError("Ninguna orden es válida. Revisa los errores por fila.")
    clean["fila"] = rows[~bad]
    clean = clean.sort_values(["equipo", "fecha", "fila"])

    if use_hours:
        clean["horometro"] = clean.groupby("equipo")["horometro"].transform(lambda s: s.interpolate(limit_area="inside"))
        back = clean.groupby("equipo")["horometro"].diff() < 0
        for r in clean.index[back]:
            issues.append(Issue("error", "ordenes", int(clean.at[r, "fila"]),
                                f"El horómetro de {clean.at[r, 'equipo']} retrocede ({clean.at[r, 'horometro']:.0f})"))
        clean = clean[~back]

    fam = clean.groupby("equipo")["familia"].agg(lambda s: s.mode().iat[0])
    if (clean.groupby("equipo")["familia"].nunique() > 1).any():
        issues.append(Issue("aviso", "ordenes", None, "Algunos equipos aparecen en más de una familia; se usa la más frecuente"))
    clean["familia"] = clean["equipo"].map(fam)

    equipos = pd.DataFrame(columns=EQUIP_COLS)
    if "equipos" in book and not book["equipos"].empty and "equipo" in book["equipos"].columns:
        e = book["equipos"].copy()
        e["equipo"] = _text(e["equipo"]).astype(object)
        e = e.dropna(subset=["equipo"]).drop_duplicates("equipo")
        if "familia" in e.columns:
            e["familia"] = _text(e["familia"]).astype(object)
        else:
            e["familia"] = e["equipo"].map(fam)
        e["familia"] = e["familia"].fillna(e["equipo"].map(fam)).fillna("Todos" if "familia" not in o.columns else "Sin familia")
        e["fecha_alta"] = pd.to_datetime(e["fecha_alta"], errors="coerce", dayfirst=True) if "fecha_alta" in e.columns else pd.NaT
        e["horometro_actual"] = pd.to_numeric(e["horometro_actual"], errors="coerce") if "horometro_actual" in e.columns else np.nan
        equipos = e[EQUIP_COLS].reset_index(drop=True)

    for f, g in clean.groupby("familia"):
        n_fail = int((g["tipo"] == "correctiva").sum())
        if n_fail < MIN_FAILURES:
            issues.append(Issue("aviso", "ordenes", None,
                                f"La familia «{f}» tiene {n_fail} fallas; con menos de {MIN_FAILURES} no se estima su confiabilidad"))

    clean["equipo"] = clean["equipo"].astype(object)
    data = {"orders": clean.reset_index(drop=True), "equipment": equipos, "unit": "horas" if use_hours else "días",
            "filas_leidas": len(o), "filas_validas": len(clean)}
    return data, issues


def issues_frame(issues: list[Issue]) -> pd.DataFrame:
    return pd.DataFrame([vars(i) for i in issues], columns=["nivel", "hoja", "fila", "mensaje"]).astype({"fila": "Int64"})


# ------------------------------------------------------------------ flota de ejemplo
def example_tables(seed: int = 11, end: str = "2026-09-30"):
    """Flota simulada: 40 montacargas que se desgastan (Weibull β = 2.5, η = 1,500 h) con preventivo cada
    2,000 h, y 25 compresores con fallas aleatorias (β = 1.0, η = 3,000 h) con preventivo cada 1,500 h."""
    rng = np.random.default_rng(seed)
    start, stop = pd.Timestamp("2023-10-01"), pd.Timestamp(end)
    fleets = [("Montacargas", "MC", 40, 2.5, 1500.0, 2000.0, (9, 15)), ("Compresor", "CP", 25, 1.0, 3000.0, 1500.0, (14, 20))]
    orders, equip = [], []
    for fam, code, n, beta, eta, pm, use in fleets:
        for i in range(1, n + 1):
            unit = f"{code}-{i:02d}"
            daily = rng.uniform(*use)
            alta = start - pd.Timedelta(days=int(rng.integers(0, 400)))
            hours = (start - alta).days * daily
            since = hours % pm * rng.uniform(0.2, 1.0)        # edad desde la última intervención al iniciar el registro
            t, clock = start, hours
            while True:
                life = eta * rng.weibull(beta)
                remaining_life = max(life - since, 1.0)
                to_pm = max(pm - since, 1.0)
                step = max(min(remaining_life, to_pm), 2 * daily)   # al menos dos días entre órdenes
                t = t + pd.Timedelta(days=step / daily)
                clock += step
                if t > stop:
                    break
                kind = "Correctiva" if remaining_life < to_pm else "Preventiva"
                orders.append((unit, fam, t.normalize(), kind, round(clock)))
                since = 0.0
            equip.append((unit, fam, alta.normalize(), round(hours + (stop - start).days * daily)))
    o = pd.DataFrame(orders, columns=["equipo", "familia", "fecha", "tipo", "horometro"]).sort_values(["fecha", "equipo"])
    e = pd.DataFrame(equip, columns=EQUIP_COLS)
    return o.reset_index(drop=True), e


def template_bytes(tables=None) -> bytes:
    orders, equip = tables or example_tables()
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl", date_format="DD/MM/YYYY", datetime_format="DD/MM/YYYY") as xw:
        pd.DataFrame(INSTRUCTIONS[1:], columns=INSTRUCTIONS[0]).to_excel(xw, sheet_name="instrucciones", index=False)
        orders.to_excel(xw, sheet_name="ordenes", index=False)
        equip.to_excel(xw, sheet_name="equipos", index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = "A2"
            for col in ws.columns:
                width = max(len(str(c.value or "")) for c in list(col)[:50])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 70)
    return buf.getvalue()


def example_with_errors() -> bytes:
    """La flota de ejemplo «como sale del CMMS»: encabezados distintos, tipos de orden con variantes
    y errores típicos de captura."""
    orders, equip = (df.copy() for df in example_tables())
    orders = orders.rename(columns={"equipo": "Activo", "fecha": "Fecha orden", "tipo": "Tipo de orden",
                                    "horometro": "Lectura horómetro"})
    orders["Fecha orden"] = orders["Fecha orden"].dt.strftime("%d/%m/%Y")
    orders["Tipo de orden"] = orders["Tipo de orden"].replace({"Correctiva": "CORR", "Preventiva": "PM"})
    orders.loc[[2, 30], "Tipo de orden"] = ["Falla", "preventivo"]
    orders.loc[4, "Fecha orden"] = "30/02/2025"
    orders.loc[6, "Tipo de orden"] = "Inspección"
    orders.loc[8, "Activo"] = None
    orders = pd.concat([orders, orders.iloc[[12]]], ignore_index=True)
    return template_bytes((orders, equip))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "plantilla_ordenes.xlsx"
    with open(out, "wb") as fh:
        fh.write(template_bytes())
    print(f"Plantilla escrita en {out}")
