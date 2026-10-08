# SPEC-002 — Cierre Definition of Done (portafolio)

Status: ACTIVE (OWNER, chat 2026-10-08 — “si continua”)  
Derived from: INTENT-446E2407EF97 + cuestionario DoD MECE  
Depends on: SPEC-001 (baseline evidence), TASK-007 (early-window slopes)

## Objective

Close the portfolio Definition of Done gaps that SPEC-001 left out on purpose: L2 taxonomy mapping, business-language decision surface, local explicability, professional README, container recipe, and a deployable Streamlit app. **Not** a production plant integration.

## Non-goals

- Live Streamlit Cloud / HF URL without owner account credentials (repo ships deploy recipe; owner publishes URL).
- MES/SCADA integration.
- SHAP library if a coefficient-based local explanation meets the DoD “XAI” intent without a new heavy dependency — use `shap` only if needed; default is contribution of standardized covariates to the linear predictor / AFT scale.
- Promoting the model as production authority.

## Deliverables (MUST)

1. `docs/taxonomy.md` — L2 wear modes ↔ C-MAPSS sensor/setting proxies (explicit: C-MAPSS has no native L2 label).
2. `src/pm_survival/explain.py` — per-asset contribution table in business language (% of risk drivers).
3. Streamlit app: inputs \(C_p\), \(C_f\); outputs recommended intervention age \(t^*\), risk framing, top drivers.
4. Root `README.md` rewritten as portfolio entry (problem, method, metrics, how to run, deploy).
5. `Dockerfile` + updated `requirements.txt` (`streamlit`, `plotly`).
6. Unit tests for taxonomy presence and explain contributions; product tests still green.

## Acceptance

| ID | Criterion |
|----|-----------|
| DoD-A1 | Taxonomy documents C-MAPSS + L2 mapping |
| DoD-B1 | App answers “¿cuándo conviene el preventivo?” with \(t^*\) |
| DoD-B2 | Per-asset driver list with % contribution (XAI) |
| DoD-B3 | App UI copy uses riesgo / costo / intervención |
| DoD-C1 | README portfolio-grade (live URL section: placeholder until owner deploys) |
| DoD-C2 | Dockerfile builds a runnable image |
| DoD-C3 | `requirements.txt` lists all runtime deps |

## Authority

Owner continuation of DoD authorizes MATERIALIZE in `src`, `docs`, `app`, `test/product`, root README/Dockerfile/requirements. Promotion and cloud publish remain OWNER.
