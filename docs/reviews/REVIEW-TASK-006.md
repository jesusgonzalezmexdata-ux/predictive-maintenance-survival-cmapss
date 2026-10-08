# Independent review — TASK-006 / SPEC-001 evidence pipeline

Status: **PARTIAL**  
Reviewer role: A2_DETERMINISTIC_AUDITOR (same session as implementer — `executor != verifier` is therefore incomplete)  
Date: 2026-10-07  
Spec: `docs/specs/SPEC-001-cmapss-survival-baseline.md`  
Commits reviewed: `b5d7a73` … `ef37372` (plus uncommitted governance state update)

## Claims evaluated

| Claim | Verdict | Evidence |
|-------|---------|----------|
| AC-1 `repoctl verify` PASS | SUPPORTED | verify PASS; audit head `86b2d838…` |
| AC-2 product unittest PASS offline | SUPPORTED | 48 tests OK, 4.57s, no network |
| AC-3 FD001 train: 100 units, event=1, duration=max cycle | PARTIALLY_SUPPORTED | Fixture analogue in `test_events.py`; real-data `provenance.schema_train.n_units=100` in `reports/eval_FD001.json`. No dedicated unittest against live `data/raw/cmapss`. |
| AC-4 test units censored; RUL not a feature | SUPPORTED | `test_test_units_are_right_censored`, `test_rul_truth_never_in_features` |
| AC-5 report has C-index, PH p-values, Weibull, fallback | SUPPORTED | `reports/eval_FD001.json` / `.md` |
| AC-6 cost `t*` finite; ratio→1 later; higher ratio earlier | SUPPORTED | `test_cost_policy.py` |
| AC-7 no tracked file > 1 MB in data/models/reports | SUPPORTED | `git ls-files` size scan empty; `data/raw/cmapss` and `intake/sources/*.zip` gitignored |
| AC-8 model card lists remaining open decisions | SUPPORTED | DEC-009, DEC-007 listed |
| No runtime download | SUPPORTED | loader tests + grep |
| DEC-003 archive SRC-003 | SUPPORTED | `data/raw/MANIFEST.json` sha256 `7109344d…` |
| CLI `python -m pm_survival run --raw-dir` | SUPPORTED | `cli.py`, `test_pipeline.py` |

## Defects / limitations (not silent)

1. **Slope–duration confounding** (documented in model card): `_slope` uses the full observed trajectory. On run-to-failure train/val units this correlates with duration. Validation C-index **0.778** is therefore optimistic as a remaining-life score. Ranking vs RUL on *censored* test units (0.816) is a more relevant check and is reported separately.
2. **PH borderline**: `sensor_17_slope` p = 0.0506; verdict “holds” at α=0.05. Fragile.
3. **Verifier identity**: this review was produced in the same agent session as implementation. Treat as **PARTIAL**, not a substitute for a second reviewer.

## Out of scope (correctly not claimed)

- Production recommendation / hosting / FD002–FD004 / AI4I
- Promotion

## Verdict

**PARTIAL** — SPEC-001 baseline pipeline is present, tested, and evidence-producing. Do not promote. Owner must decide HG-003.
