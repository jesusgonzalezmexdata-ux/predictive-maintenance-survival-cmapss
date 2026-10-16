"""Lista semanal de intervención a partir de órdenes de trabajo (MVP 2, sin sensores).

1. Las órdenes se convierten en vidas: de una intervención a la siguiente. Termina en falla si la orden que la
   cierra es correctiva; si es preventiva, la vida queda censurada (el equipo no falló, se intervino antes).
2. Por familia se ajusta una Weibull con censura. β > 1 (con su intervalo) indica desgaste: solo entonces el
   preventivo por edad reduce costo.
3. Con los costos del usuario se calcula la edad óptima de intervención t* (reemplazo por edad) y el ahorro anual
   contra el intervalo preventivo actual.
4. Lista de la semana: probabilidad de falla de cada equipo en los próximos 7 días dada su edad, limitada por la
   capacidad del taller.
5. Retrospectiva: en las últimas semanas del histórico, ¿cuántas fallas habría anticipado la lista?
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from lifelines import WeibullFitter

from . import cost_policy as C
from .fleet_intake import MIN_FAILURES
from .models import WeibullResult, weibull_regime


@dataclass
class Settings:
    costo_preventivo: float = 2_500.0   # MXN por intervención preventiva
    costo_falla: float = 15_000.0       # MXN por falla: reparación + paro + urgencia
    capacidad_semana: int = 5           # intervenciones preventivas que el taller puede hacer por semana
    semanas_programar: int = 4


# ------------------------------------------------------------------ vidas
def _rates(orders, equipment, cutoff):
    """Uso por día de cada equipo (solo con horómetro)."""
    g = orders.dropna(subset=["horometro"]).groupby("equipo")
    span = (g["fecha"].max() - g["fecha"].min()).dt.days
    rate = (g["horometro"].max() - g["horometro"].min()) / span.where(span > 0)
    if not equipment.empty:
        e = equipment.set_index("equipo")
        alt = e["horometro_actual"] / (cutoff - e["fecha_alta"]).dt.days
        rate = rate.combine_first(alt.where(np.isfinite(alt) & (alt > 0)))
    return rate


def lives(data, cutoff=None):
    """Tabla de vidas: equipo, familia, inicio, fin, duracion, evento (1 = falla)."""
    o, e, hours = data["orders"], data["equipment"], data["unit"] == "horas"
    cutoff = pd.Timestamp(cutoff) if cutoff is not None else o["fecha"].max()
    o = o[o["fecha"] <= cutoff]
    rate = _rates(o, e, cutoff) if hours else None
    fam_rate = None
    if hours:
        fam_rate = rate.groupby(o.groupby("equipo")["familia"].first()).median()
    e_idx = e.set_index("equipo") if not e.empty else None
    rows = []
    units = set(o["equipo"]) | (set(e["equipo"]) if not e.empty else set())
    fam_of = o.groupby("equipo")["familia"].first()
    first_record = data["orders"]["fecha"].min()
    for unit in sorted(units):
        g = o[o["equipo"] == unit]
        fam = fam_of.get(unit) if unit in fam_of else e_idx.at[unit, "familia"]
        r = rate.get(unit, np.nan) if hours else 1.0
        if hours and not np.isfinite(r):
            r = fam_rate.get(fam, np.nan) if fam_rate is not None else np.nan
        prev_t, prev_x = None, None
        alta = e_idx.at[unit, "fecha_alta"] if e_idx is not None and unit in e_idx.index else pd.NaT
        # La fecha de alta solo abre una vida si el equipo entró en servicio dentro del periodo registrado;
        # si es anterior, pudo tener intervenciones que no están en el archivo.
        if pd.notna(alta) and first_record < alta <= cutoff:
            prev_t, prev_x = alta, 0.0 if hours else float(alta.toordinal())
        for row in g.itertuples():
            x = float(row.horometro) if hours else float(row.fecha.toordinal())
            if prev_t is not None and x - prev_x > 0:
                rows.append((unit, fam, prev_t, row.fecha, x - prev_x, int(row.tipo == "correctiva"), False))
            prev_t, prev_x = row.fecha, x
        if prev_t is None:
            continue
        if hours:
            current = e_idx.at[unit, "horometro_actual"] if e_idx is not None and unit in e_idx.index else np.nan
            if pd.isna(current) or data.get("_backtest"):
                current = prev_x + (r * (cutoff - prev_t).days if np.isfinite(r) else np.nan)
        else:
            current = float(cutoff.toordinal())
        if np.isfinite(current) and current - prev_x >= 0:
            rows.append((unit, fam, prev_t, cutoff, max(current - prev_x, 0.0), 0, True))
    out = pd.DataFrame(rows, columns=["equipo", "familia", "inicio", "fin", "duracion", "evento", "abierta"])
    out.attrs["rates"] = rate
    return out


# ------------------------------------------------------------------ modelo y política
@dataclass
class FamilyModel:
    familia: str
    weibull: WeibullResult
    beta_ci: tuple[float, float]
    n_vidas: int
    n_fallas: int
    mttf: float

    @property
    def desgaste_demostrado(self) -> bool:
        return self.beta_ci[0] > 1.0


def fit_families(life: pd.DataFrame) -> dict[str, FamilyModel]:
    models = {}
    for fam, g in life[life["duracion"] > 0].groupby("familia"):
        if g["evento"].sum() < MIN_FAILURES:
            continue
        wf = WeibullFitter().fit(g["duracion"].to_numpy(float), event_observed=g["evento"].to_numpy())
        beta, eta = float(wf.rho_), float(wf.lambda_)
        ci = wf.summary.loc["rho_"]
        lo, hi = float(ci["coef lower 95%"]), float(ci["coef upper 95%"])
        w = WeibullResult(shape=beta, scale=eta, regime=weibull_regime(beta), n=len(g), n_events=int(g["evento"].sum()))
        models[fam] = FamilyModel(fam, w, (lo, hi), len(g), int(g["evento"].sum()), eta * math.gamma(1 + 1 / beta))
    return models


def policy_table(models, life, data, settings: Settings) -> pd.DataFrame:
    cp, cf = settings.costo_preventivo, settings.costo_falla
    rate = life.attrs.get("rates")
    rows = []
    for fam, mdl in models.items():
        R = mdl.weibull.survival
        opt = C.optimal_time(cp, cf, R, horizon=4 * mdl.weibull.scale, n_points=4000)
        pm = life[(life["familia"] == fam) & ~life["abierta"] & (life["evento"] == 0)]["duracion"]
        current = float(pm.median()) if len(pm) >= 3 else None
        c_rtf = cf / mdl.mttf
        c_cur = C.expected_cost_rate(current, cp, cf, R) if current else c_rtf
        # Sin desgaste demostrado (IC de β incluye 1) no se propone edad de intervención: la referencia es dejar
        # de hacer preventivo por edad y vigilar condición.
        use_age = mdl.desgaste_demostrado and not opt.at_horizon
        c_opt = opt.cost_rate_at_t_star if use_age else c_rtf
        units = life.loc[life["familia"] == fam, "equipo"].unique()
        if data["unit"] == "horas":
            per_year = float(np.nanmedian([rate.get(u, np.nan) for u in units])) * 365
        else:
            per_year = 365.0
        rows.append({
            "familia": fam, "equipos": len(units), "vidas": mdl.n_vidas, "fallas": mdl.n_fallas,
            "beta": mdl.weibull.shape, "beta_inf": mdl.beta_ci[0], "beta_sup": mdl.beta_ci[1], "eta": mdl.weibull.scale,
            "desgaste_demostrado": mdl.desgaste_demostrado, "vida_media": mdl.mttf,
            "intervalo_actual": current, "t_optimo": opt.t_star if use_age else None,
            "confiabilidad_t_optimo": opt.reliability_at_t_star if use_age else None,
            "carga_semanal": len(units) * per_year / 52 / opt.t_star if use_age else None,
            "costo_unidad_actual": c_cur, "costo_unidad_optimo": c_opt, "costo_unidad_dejar_fallar": c_rtf,
            "uso_anual_por_equipo": per_year,
            "ahorro_anual": (c_cur - c_opt) * per_year * len(units),
            "ahorro_pct": 1 - c_opt / c_cur if c_cur > 0 else 0.0,
        })
    num = ["intervalo_actual", "t_optimo", "confiabilidad_t_optimo", "carga_semanal"]
    return pd.DataFrame(rows).astype({c: float for c in num}) if rows else pd.DataFrame(rows)


def recommendation(row) -> str:
    unit = row.get("unidad", "")
    if not row["desgaste_demostrado"]:
        return (f"β = {row['beta']:.2f} (IC 95 % {row['beta_inf']:.2f}–{row['beta_sup']:.2f}): no hay desgaste demostrado. "
                "El preventivo por edad no reduce fallas; conviene inspección por condición y bajar la frecuencia del preventivo"
                + (" actual" if row["intervalo_actual"] else "") + ".")
    if row["t_optimo"] is None:
        return "Hay desgaste, pero con estos costos dejar fallar sale más barato que intervenir por edad."
    txt = f"Intervenir cada {row['t_optimo']:,.0f} {unit}".rstrip()
    if row["intervalo_actual"]:
        txt += f" (hoy ≈ {row['intervalo_actual']:,.0f})"
    return txt + f": ahorro de {row['ahorro_pct']:.0%} sobre la práctica actual."


# ------------------------------------------------------------------ lista de la semana
def weekly_list(models, life, data, policy, settings: Settings, cutoff=None) -> pd.DataFrame:
    hours = data["unit"] == "horas"
    rate = life.attrs.get("rates")
    tstar = policy.set_index("familia")["t_optimo"].to_dict()
    open_ = life[life["abierta"]]
    rows = []
    for r in open_.itertuples():
        mdl = models.get(r.familia)
        if mdl is None:
            continue
        h = 7 * rate.get(r.equipo, np.nan) if hours else 7.0
        if not np.isfinite(h):
            continue
        a = r.duracion
        R = mdl.weibull.survival
        p = 1 - float(R(np.array([a + h]))[0] / max(float(R(np.array([a]))[0]), 1e-12))
        t = tstar.get(r.familia)
        if t is None or (isinstance(t, float) and math.isnan(t)):
            status = "Operar · vigilar condición"
        elif a >= t:
            status = "Vencido"
        elif a + settings.semanas_programar * h >= t:
            status = "Programar"
        else:
            status = "Operar"
        rows.append({"equipo": r.equipo, "familia": r.familia, "edad": a, "t_optimo": t, "p_falla_semana": p, "estado": status,
                     "semanas_para_t_optimo": None if status == "Operar · vigilar condición" else max(0.0, (t - a) / h)})
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.sort_values("p_falla_semana", ascending=False).reset_index(drop=True)
    due = out.index[out["estado"] == "Vencido"]
    out.loc[due[: settings.capacidad_semana], "estado"] = "Intervenir esta semana"
    out.loc[due[settings.capacidad_semana:], "estado"] = "Vencido · sin capacidad esta semana"
    return out


# ------------------------------------------------------------------ retrospectiva
def backtest(data, settings: Settings, frac: float = 0.25):
    """Ajusta con el histórico previo al corte y, semana a semana en el resto, compara la lista (top N por
    probabilidad de falla) con las fallas que ocurrieron."""
    o = data["orders"]
    t0, t1 = o["fecha"].min(), o["fecha"].max()
    start = t0 + (t1 - t0) * (1 - frac)
    weeks = pd.date_range(start, t1 - pd.Timedelta(days=7), freq="7D")
    if len(weeks) < 4:
        return None
    bt = dict(data, _backtest=True)
    base = lives(bt, cutoff=start)
    models = fit_families(base)
    if not models:
        return None
    hits = total = slots = fleet_size = 0
    for w in weeks:
        life = lives(bt, cutoff=w)
        rate = life.attrs.get("rates")
        open_ = life[life["abierta"] & life["familia"].isin(models)]
        if open_.empty:
            continue
        probs = []
        for r in open_.itertuples():
            h = 7 * rate.get(r.equipo, np.nan) if data["unit"] == "horas" else 7.0
            if not np.isfinite(h):
                continue
            R = models[r.familia].weibull.survival
            probs.append((r.equipo, 1 - float(R(np.array([r.duracion + h]))[0] / max(float(R(np.array([r.duracion]))[0]), 1e-12))))
        top = {u for u, _ in sorted(probs, key=lambda t: -t[1])[: settings.capacidad_semana]}
        failed = set(o[(o["fecha"] >= w) & (o["fecha"] < w + pd.Timedelta(days=7)) & (o["tipo"] == "correctiva")
                       & o["familia"].isin(models)]["equipo"])
        hits += len(failed & top)
        total += len(failed)
        slots += 1
        fleet_size += len(probs)
    if total == 0:
        return None
    random_rate = settings.capacidad_semana * slots / fleet_size
    return {"desde": start, "semanas": slots, "fallas": total, "anticipadas": hits, "captura": hits / total,
            "captura_al_azar": min(random_rate, 1.0), "veces_mejor_que_azar": (hits / total) / random_rate if random_rate else None}


# ------------------------------------------------------------------ orquestación
def analyse(data, settings: Settings | None = None):
    settings = settings or Settings()
    life = lives(data)
    models = fit_families(life)
    policy = policy_table(models, life, data, settings)
    if not policy.empty:
        policy["unidad"] = data["unit"]
        policy["recomendacion"] = policy.apply(recommendation, axis=1)
    week = weekly_list(models, life, data, policy, settings) if models else pd.DataFrame()
    return {"vidas": life, "modelos": models, "politica": policy, "semana": week, "retrospectiva": backtest(data, settings),
            "corte": data["orders"]["fecha"].max(), "unidad": data["unit"], "settings": settings,
            "familias_sin_modelo": sorted(set(life["familia"]) - set(models))}
