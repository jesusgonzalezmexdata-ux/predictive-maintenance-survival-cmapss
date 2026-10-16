# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/).

## [1.2.0] - 2026-10-16

### Added
- MVP for real fleets: "Tu flota" mode in the app. Upload work orders (equipment, date, corrective/preventive, optional hour meter and family) as an Excel template; row-level validation with Spanish messages; processing in the browser on the live demo.
- Work orders → censored lives → Weibull per family (`fleet.py`); age policy only when wear is demonstrated (β 95 % CI above 1); optimal interval, annual saving and weekly workload against the current interval.
- Weekly intervention list capped by workshop capacity, and a retrospective check against random selection.
- One-page report with ISO 9001 / IATF 16949 / ISO 14224 / ISO 55001 references (`fleet_report.py`); pilot protocol (`docs/MVP_PILOTO.md`); ten tests.

## [1.1.0] - 2026-10-16

### Added
- Sensor monitoring: PSI per sensor, frozen-sensor and out-of-range checks (`monitoring.py`).
- Full English README with the Spanish version kept as `README.es.md`.
- Project page on GitHub Pages and a live demo on Hugging Face Spaces, published automatically from `main`.
- Release workflow: notes from this changelog and an evidence bundle attached to every tag.

### Changed
- Repository reduced to the product: model, policies, app, tests, specifications and evidence; scheduled governance jobs removed.
- MIT license text standardised so GitHub detects it.

## [1.0.0] - 2026-10-08

### Added
- Survival table with right-censoring and engine-grouped splits; Weibull and Cox baselines.
- Landmark model using only the last 20 cycles up to each inspection; concordance 0.85 against true RUL.
- Renewal-reward backtest of four maintenance policies: condition-based is 40 % cheaper than age replacement at C_f/C_p = 10.
- Streamlit decision app with demo mode, figures, notebook and Docker image.
