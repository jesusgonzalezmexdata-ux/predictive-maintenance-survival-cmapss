"""Command-line entry points (TASK-006).

    python -m pm_survival extract --archive <zip> --out data/raw/cmapss
    python -m pm_survival run --raw-dir data/raw/cmapss [--reports reports] [--models models]
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

from . import data as D
from . import metrics as X
from .pipeline import run_pipeline


def _extract(archive: Path, out: Path) -> list[str]:
    """Extract only ``*.txt`` members (flat) — never binaries — into ``out``."""
    out.mkdir(parents=True, exist_ok=True)
    names = []
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = Path(info.filename).name
            if not name.lower().endswith(".txt"):
                continue
            (out / name).write_bytes(zf.read(info))
            names.append(name)
    return sorted(names)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pm_survival", description="Governed C-MAPSS survival / RUL baseline (SPEC-001)")
    sub = p.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extract", help="extract .txt members of a local C-MAPSS archive")
    e.add_argument("--archive", required=True, type=Path)
    e.add_argument("--out", required=True, type=Path)

    r = sub.add_parser("run", help="run the evidence pipeline on local raw files")
    r.add_argument("--raw-dir", type=Path, default=None, help=f"defaults to ${D.ENV_RAW_DIR}")
    r.add_argument("--reports", type=Path, default=Path("reports"))
    r.add_argument("--models", type=Path, default=Path("models"))
    r.add_argument("--subset", default="FD001", choices=list(D.SUBSETS))
    r.add_argument("--val-fraction", type=float, default=0.2)
    r.add_argument("--seed", type=int, default=42)
    r.add_argument("--n-covariates", type=int, default=8)
    r.add_argument("--early-window", type=int, default=20)
    r.add_argument("--horizons", type=int, nargs="+", default=X.DEFAULT_HORIZONS)
    r.add_argument("--cost-ratio", type=float, default=10.0, help="C_f / C_p (DEC-013 default 10)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "extract":
        names = _extract(args.archive, args.out)
        print(json.dumps({"status": "PASS", "extracted": names, "out": str(args.out)}, indent=2))
        return 0
    if args.cmd == "run":
        try:
            raw_dir = D.resolve_raw_dir(args.raw_dir)
        except FileNotFoundError as exc:
            print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, indent=2), file=sys.stderr)
            return 2
        payload = run_pipeline(
            raw_dir,
            reports_dir=args.reports,
            models_dir=args.models,
            subset=args.subset,
            val_fraction=args.val_fraction,
            seed=args.seed,
            n_covariates=args.n_covariates,
            early_window=args.early_window,
            horizons=args.horizons,
            cost_ratio=args.cost_ratio,
        )
        summary = {
            "status": "PASS",
            "subset": args.subset,
            "selected_model": payload["selected_model"]["kind"],
            "validation_concordance": payload["validation"]["concordance"],
            "ibs": payload["validation"]["ibs"],
            "weibull_shape": payload["weibull"]["shape"],
            "t_star": payload["cost_policy"]["t_star"],
            "reports": str(args.reports),
            "models": str(args.models),
        }
        print(json.dumps(summary, indent=2))
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
