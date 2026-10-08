"""Render README figures from the study outputs (no model fitting here).

Usage: python tools/make_figures.py   (after `python -m pm_survival study`)
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUT = REPORTS / "figures"

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0"
SERIES = {"condition": "#2a78d6", "age": "#eb6834", "oracle": "#1baf7a", "run_to_failure": "#8f8e88"}
LABEL = {"condition": "Por condición (este repo)", "age": "Por edad t* (flota)", "oracle": "Oráculo (cota)", "run_to_failure": "Dejar fallar"}

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.labelcolor": INK2,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "text.color": INK,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
    }
)


def policy_at_headline(pol: pd.DataFrame, ratio: float = 10.0) -> None:
    sub = pol[pol["ratio"] == ratio].set_index("policy").loc[["run_to_failure", "age", "condition", "oracle"]]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    y = range(len(sub))[::-1]
    for yi, (name, row) in zip(y, sub.iterrows(), strict=True):
        ax.barh(yi, row["cost_per_1000_cycles"], color=SERIES[name], height=0.55)
        ax.text(row["cost_per_1000_cycles"] + 1.0, yi, f"{row['cost_per_1000_cycles']:.1f}  ·  {row['failures']:g} {'falla' if row['failures'] == 1 else 'fallas'} de 100",
                va="center", color=INK, fontsize=10)
    ax.set_yticks(list(y), [LABEL[n] for n in sub.index])
    ax.set_xlabel("Costo por cada 1 000 ciclos (unidades de C_p)")
    ax.set_xlim(0, sub["cost_per_1000_cycles"].max() * 1.45)
    ax.grid(axis="y", visible=False)
    ax.set_title(f"Costo por política con C_f/C_p = {ratio:g}")
    fig.tight_layout()
    fig.savefig(OUT / "policy_cost_ratio10.png", dpi=160)
    plt.close(fig)


def policy_sensitivity(pol: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    for name in ("age", "condition", "oracle"):
        s = pol[pol["policy"] == name].sort_values("ratio")
        ax.plot(s["ratio"], s["cost_per_1000_cycles"], color=SERIES[name], lw=2, marker="o", ms=6, label=LABEL[name])
    ax.set_xscale("log")
    ax.set_xticks([2, 3, 5, 10, 20, 50], ["2", "3", "5", "10", "20", "50"])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("Razón de costos C_f / C_p (escala log)")
    ax.set_ylabel("Costo por 1 000 ciclos")
    ax.set_ylim(0, None)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Sensibilidad: la ventaja crece cuando la falla es más cara")
    fig.text(0.01, 0.01, "Dejar fallar queda fuera de escala (9.7 a 242 por 1 000 ciclos).", color=INK2, fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "policy_sensitivity.png", dpi=160)
    plt.close(fig)


def test_concordance(study: dict) -> None:
    m = study["test"]["metrics"]
    order = [("early_window", "Ventana temprana (SPEC-001)"), ("age_only", "Solo edad (población)"), ("landmark", "Por condición (landmark)")]
    fig, ax = plt.subplots(figsize=(8, 3))
    for i, (k, _lab) in enumerate(order):
        v = m[k]
        lo, hi = v["concordance_ci95"]
        color = SERIES["condition"] if k == "landmark" else SERIES["run_to_failure"]
        ax.plot([lo, hi], [i, i], color=color, lw=2)
        ax.plot(v["concordance_vs_rul"], i, "o", color=color, ms=9, mec=SURFACE, mew=2)
        ax.text(hi + 0.01, i, f"{v['concordance_vs_rul']:.2f}  (IC 95 % {lo:.2f}–{hi:.2f})", va="center", fontsize=10)
    ax.axvline(0.5, color=INK2, lw=1, ls="--")
    ax.text(0.505, -0.6, "azar", color=INK2, fontsize=9)
    ax.set_yticks(range(len(order)), [lab for _, lab in order])
    ax.set_xlim(0.45, 1.2)
    ax.set_ylim(-0.8, len(order) - 0.4)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Concordancia con la vida restante real (100 motores de prueba)")
    ax.set_title("¿Ordena bien qué motor fallará primero?")
    fig.tight_layout()
    fig.savefig(OUT / "test_concordance.png", dpi=160)
    plt.close(fig)


def calibration(cal: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(4.8, 4.4))
    ax.plot([0, 1], [0, 1], color=INK2, lw=1, ls="--", label="Calibración perfecta")
    ax.plot(cal["predicted"], cal["observed"], color=SERIES["condition"], lw=2, marker="o", ms=6, label="Modelo (deciles)")
    ax.set_xlabel("P(falla en ≤ 30 ciclos) predicha")
    ax.set_ylabel("Frecuencia observada")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Calibración fuera de pliegue")
    fig.tight_layout()
    fig.savefig(OUT / "calibration_p30.png", dpi=160)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    study = json.loads((REPORTS / "landmark_FD001.json").read_text(encoding="utf-8"))
    pol = pd.DataFrame(study["policies"])
    policy_at_headline(pol)
    policy_sensitivity(pol)
    test_concordance(study)
    calibration(pd.read_csv(REPORTS / "demo" / "calibration_p30.csv"))
    print(sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
