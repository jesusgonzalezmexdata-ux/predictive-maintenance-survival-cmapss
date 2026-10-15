# Condition-based maintenance with survival analysis (NASA C-MAPSS)

*English · [Español](README.es.md)*

[![product-ci](https://github.com/jesusgonzalezmexdata-ux/predictive-maintenance-survival-cmapss/actions/workflows/product-ci.yml/badge.svg)](https://github.com/jesusgonzalezmexdata-ux/predictive-maintenance-survival-cmapss/actions/workflows/product-ci.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Which engines should be serviced now, and how much does that save against replacing by age or running to failure?**

With a failure 10 times more expensive than a preventive job, deciding on each engine's **current condition** costs **40 % less** than replacing the whole fleet at a fixed age, with 1 in-service failure out of 100 engines and 91 % of useful life used (against 50 %).

> Portfolio evidence on data **simulated** by NASA. Not a production system and not an aeronautical certification. Costs are illustrative.

![Cost by policy with C_f/C_p = 10](reports/figures/policy_cost_ratio10.png)

## Results

### 1. The business number: cost by policy (100 engines, out of fold)

Cost in units of a preventive job (C_p = 1, C_f = 10). Each engine is evaluated by a model that did not see it.

| Policy | Cost / 1,000 cycles | In-service failures | Useful life used |
|---|---:|---:|---:|
| Run to failure | 48.47 | 100 | 100 % |
| Age replacement t* (whole fleet) | 9.64 | 0 | 50 % |
| **Condition-based (this model)** | **5.80** | **1** | **91 %** |
| Oracle (theoretical bound) | 4.92 | 0 | 98 % |

- Condition − age difference: **−3.84** per 1,000 cycles (95 % CI −4.49 to −2.77, bootstrap by engine).
- The advantage holds for every cost ratio tested (2 to 50): 28 % to 45 % saving against age replacement. See the [sensitivity](reports/figures/policy_sensitivity.png).

### 2. Does it rank which engine will fail first? (official test set, true RUL)

| Model | Concordance with true RUL | 95 % CI | RMSE (cycles) |
|---|---:|---|---:|
| **Condition-based (landmark)** | **0.85** | 0.80–0.89 | 26.9 |
| Age only (population) | 0.71 | 0.66–0.76 | 36.1 |
| Early window (SPEC-001) | 0.69 | 0.63–0.74 | 44.2 |

![Test concordance](reports/figures/test_concordance.png)

Signals from the first 20 cycles add nothing over age; recent condition does. Test Brier score of P(failure within 30 cycles): 0.034 against 0.188 for a constant prediction.

## What makes this analysis different

1. **No look-ahead.** At each inspection `c` the model uses only the last 20 cycles up to `c` (mean, slope and age) and predicts residual life `T − c`. An automated test rewrites the data after `c` and checks that the features do not change.
2. **It fixes its own earlier mistake.** SPEC-001 used slopes over the whole trajectory (C-index 0.78 and 0.82 against true RUL, with leakage). Removing the leakage dropped it to 0.46 against true RUL; this repository documents that step and solves it with the *landmark* approach instead of hiding it.
3. **Uncertainty everywhere.** Grouped 5 × 5 cross-validation (no engine crosses folds), bootstrap 95 % CIs, Brier against the base rate and [calibration](reports/figures/calibration_p30.png).
4. **It measures the decision, not only the model.** A *renewal-reward* backtest of four policies, with the intervention threshold tuned by inner CV on training engines and an oracle as the ceiling.
5. **It says what does not work.** The model overestimates risk when it predicts between ~5 % and ~20 % (conservative for the decision). With a Holm correction, the proportional-hazards assumption of SPEC-001 does hold; both readings are reported.

## How to run it

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows · macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
```

**Decision app (works without the NASA data, in demo mode):**

```bash
streamlit run app/streamlit_app.py
```

Four tabs: this week's decision (which engines to service), policy comparison, fleet reliability and single-engine explanation (the last one needs the local data). The C_f/C_p ratio is set in the sidebar.

**Regenerate all evidence from the raw data** (not in git; download it from NASA's official source):

```bash
python -m pm_survival extract --archive path/to/CMAPSSData.zip --out data/raw/cmapss
python -m pm_survival run   --raw-dir data/raw/cmapss   # SPEC-001 baseline
python -m pm_survival study --raw-dir data/raw/cmapss   # SPEC-003, ~2 min
python tools/make_figures.py
pytest test/product                                      # 71 tests, no NASA data needed
```

**Docker:** `docker build -t pm-survival . && docker run -p 8501:8501 pm-survival`, then open `http://localhost:8501`.

**Publish the demo (Streamlit Community Cloud):** New app → this repository → branch `main` → file `app/streamlit_app.py`. No data upload is needed: the app reads the derived artifacts in `reports/demo/`.

## Where everything is

| What | Where |
|---|---|
| Narrated analysis | [`notebooks/analisis_mantenimiento_por_condicion.ipynb`](notebooks/analisis_mantenimiento_por_condicion.ipynb) (Spanish) |
| Full evaluation with CIs | [`reports/landmark_FD001.md`](reports/landmark_FD001.md) |
| Model cards | [`models/MODEL_CARD_LANDMARK_FD001.md`](models/MODEL_CARD_LANDMARK_FD001.md), [`models/MODEL_CARD_FD001.md`](models/MODEL_CARD_FD001.md) |
| Model and policy code | [`src/pm_survival/landmark.py`](src/pm_survival/landmark.py), [`policies.py`](src/pm_survival/policies.py), [`study.py`](src/pm_survival/study.py) |
| App | [`app/streamlit_app.py`](app/streamlit_app.py) |
| Product tests | [`test/product/`](test/product) |
| Specifications | [`SPEC-001`](docs/specs/SPEC-001-cmapss-survival-baseline.md), [`SPEC-002`](docs/specs/SPEC-002-dod-closure.md), [`SPEC-003`](docs/specs/SPEC-003-condition-based-impact.md) |
| L2 taxonomy ↔ sensors | [`docs/taxonomy.md`](docs/taxonomy.md) |

## Monitoring

[`monitoring.py`](src/pm_survival/monitoring.py) compares a new batch of engine cycles with a reference batch: PSI per informative sensor (≥ 0.25 = alert), sensors that froze, and readings outside the reference range (> 5 % = alert). Compare engines in the same age range: young test engines drift against whole training trajectories without anything being wrong. Tests cover a shifted sensor, a frozen sensor and an unchanged batch.

## Reference baseline (SPEC-001)

Fleet Weibull with β ≈ 4.6 (wear-out), a Weibull AFT model on the first 20 cycles and an age-replacement policy: t* ≈ 105 cycles with C_f/C_p = 10. It is the baseline everything above is compared with ([evaluation](reports/eval_FD001.md)).

## Limits

- FD001 has a single operating regime and a single failure mode; FD002–FD004 require retraining and revalidation.
- Illustrative costs; inspection is assumed free, with the last 20 cycles of data available.
- Simulated data: a real plant has measurement noise, dropped sensors and imperfect maintenance.
- The model is not promoted to production.

## License

Code under [MIT](LICENSE). NASA C-MAPSS data are not redistributed; get them from the official source.

---

**Jesús R. L. González** · Data Analyst and Data Scientist · Manufacturing operations and quality · [LinkedIn](https://www.linkedin.com/in/jesus-r-l-gonzalez)
