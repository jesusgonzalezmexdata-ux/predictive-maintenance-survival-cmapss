# SPEC-001 — C-MAPSS Survival / RUL Baseline Evidence Pipeline

Status: APPROVED (HG-002 = A, OWNER, 2026-10-07) — implementation may proceed task by task; promotion still OWNER-gated  
Owner: OWNER  
Author: A6_PLANNER role (session GEC-003, 2026-10-07)  
Derived from: `INTENT-446E2407EF97` / `SPEC-446E2407EF97` (bootstrap)  
Applies decisions: HG-001 = A, DEC-002 = DATA_SCIENCE, DEC-006 = Q3  
Source evidence (qualified, non-normative): SRC-003 (C-MAPSS archive), SRC-001 (dataset notes), SRC-007 (survival/cost brief)

---

## 1. Objective

Produce the first governed, reproducible evidence pipeline that:

1. ingests NASA C-MAPSS FD001 run-to-failure trajectories under a declared raw-data boundary;
2. constructs a time-to-event representation with explicit right-censoring;
3. fits and evaluates baseline survival models (Weibull parametric, Cox proportional hazards) with deterministic metrics;
4. records evidence (metrics, manifests, model card) suitable for an independent verifier;
5. frames a cost-ratio maintenance decision (preventive vs corrective) as a computed artifact, not a UI.

## 2. Non-goals (this spec)

- Web application, hosting, containerization (SRC-007 proposes them; deferred to a later spec).
- FD002–FD004 multi-condition subsets (MAY be enabled later; FD001 first).
- Deep learning / sequence models.
- AI4I dataset work (Candidate C material; out of scope under HG-001 = A).
- Production deployment, monitoring, drift alerts.
- Any dependency on external network downloads at build/test time.

## 3. Scope (governed scopes touched)

| Scope | Allowed writes under this spec |
|-------|-------------------------------|
| `data/raw` | README + manifest (hashes, provenance) only. **No dataset copies by default** until DEC-004 resolved. |
| `data/processed` | Deterministic derived tables (small, regenerable) + schema docs |
| `src` | Package `pm_survival` (loader, event builder, models, metrics, cost policy, CLI) |
| `test/product` | Deterministic unit tests on synthetic mini-fixtures (no large data) |
| `models` | Model cards, metric manifests; binaries excluded by default |
| `reports` | Generated evaluation report (Markdown/JSON) |
| `notebooks` | Optional exploration; nothing promoted from here without spec/task |

## 4. Requirements

### 4.1 Data boundary and provenance

- **MUST** declare the raw source in `data/raw/MANIFEST.json` with SHA256 of the archive used (SRC-003 `7109344d…` or SRC-004 `c9c5dec1…` per DEC-003) and the per-file sizes.
- **MUST** load from a configurable local path (`PM_RAW_DIR` or CLI flag); **MUST NOT** download at runtime.
- **MUST NOT** commit multi-MB raw files unless DEC-004 explicitly authorizes.
- **SHOULD** validate FD001 schema: 26 whitespace-separated columns = `unit_id`, `cycle`, `op_setting_1..3`, `sensor_1..21`; train FD001 = 100 units, 20,631 rows (SUPPORTED by archive inspection).

### 4.2 Event / censoring construction

- **MUST** define the event as *engine reaches end of its recorded run-to-failure trajectory* (train set: last cycle = failure, `event = 1`).
- **MUST** represent test trajectories as **right-censored** at their last observed cycle (`event = 0`), with ground-truth remaining life taken from `RUL_FD00x.txt` only for evaluation, never as a feature.
- **MUST** emit a per-unit survival table: `unit_id, duration, event, covariates…`.
- **SHOULD** support a time-varying (counting-process) long format for Cox with covariates per cycle; **MAY** start with per-unit summary covariates (e.g. early-life sensor means) for the first baseline.
- **MUST** implement a time-based validation split by `unit_id` groups (no leakage of later cycles of the same unit into training).

### 4.3 Models

- **MUST** fit a Weibull parametric survival model (shape/scale) on training durations, reporting shape interpretation (infant / random / wear-out regime).
- **MUST** fit a Cox proportional hazards model on selected covariates.
- **MUST** test the proportional-hazards assumption (Schoenfeld residuals or equivalent) and record the outcome in the report.
- **SHOULD** fall back to Weibull AFT if PH assumption fails, with the decision recorded.
- **MAY** add Random Survival Forest as a third baseline if a dependency decision allows it.

### 4.4 Metrics and evidence

- **MUST** report Concordance Index (C-index) on the held-out split.
- **SHOULD** report time-dependent Brier score / IBS over a declared horizon grid.
- **MUST** write `reports/eval_FD001.json` and `reports/eval_FD001.md` deterministically (fixed seed, sorted keys).
- **MUST** write `models/MODEL_CARD_FD001.md` with data boundary, assumptions, metrics, limitations, and open decisions.
- **MUST** be independently reproducible from `python -m pm_survival run --raw-dir <path>` given the archive.

### 4.5 Cost-policy framing

- **MUST** implement the expected cost-per-unit-time function
  \( C(t) = \dfrac{C_p R(t) + C_f (1 - R(t))}{\int_0^t R(x)\,dx} \)
  and return \( t^* = \arg\min_t C(t) \) for given \( C_p, C_f \) using the fitted reliability \( R(t) \).
- **MUST** expose this as a pure function with unit tests (monotonic sanity checks, degenerate ratios).
- **MUST NOT** present \( t^* \) as a production recommendation; it is baseline evidence.

### 4.6 Engineering constraints

- **MUST** keep all tests runnable offline on a synthetic mini-fixture (≤ 200 rows) committed under `test/product/fixtures/`.
- **MUST NOT** introduce secrets, credentials, or `.env` changes.
- Dependency additions are **OPEN_DECISION** (see §6) because they are supply-chain events.
- **SHOULD** pin versions in a lock/requirements file once DEC-010 approves the stack.

## 5. Acceptance criteria (verifiable)

| ID | Criterion | Verification |
|----|-----------|--------------|
| AC-1 | `python .scripts/repoctl.py verify` → PASS after all tasks | repoctl |
| AC-2 | `python -m unittest discover -s test/product -p 'test_*.py'` → all pass offline | unittest |
| AC-3 | Survival table for FD001 has 100 rows, `event==1` for all train units, durations equal max cycle per unit | test on fixture + report assertion |
| AC-4 | Test units are censored (`event==0`) and RUL truth is never present in feature columns | unit test |
| AC-5 | Report contains C-index, PH-test p-values, Weibull shape/scale, chosen fallback (if any) | file inspection |
| AC-6 | `cost_policy.optimal_time(Cp, Cf, R)` returns finite \( t^* \) and `Cf/Cp → 1` pushes \( t^* \) later | unit test |
| AC-7 | No file > 1 MB added to `data/`, `models/`, `reports/` unless DEC-004 approves | size scan |
| AC-8 | Model card lists open decisions verbatim from §6 | file inspection |

## 6. Decisions (resolved by OWNER via HG-002 = A, defaults accepted)

| ID | Decision | Resolution | Status |
|----|----------|------------|--------|
| DEC-003 | Canonical NASA archive | **SRC-003** `intake/sources/Proyect_5_Nasa.zip` (sha256 `7109344d…`) | DECIDED |
| DEC-004 | Raw data in git vs external path | **External path only**; `data/raw/*` and `intake/sources/*.zip` gitignored; local extraction under `data/raw/cmapss/` | DECIDED |
| DEC-005 | Kaggle preprocessed variant | **Exclude** | DECIDED |
| DEC-008 | Initialize git + hooks | **Done** (`git init -b main`, `repoctl install-hooks` PASS) | DECIDED |
| DEC-009 | Kernel tests assume MASTER_TEMPLATE (4 `test_intent.py` failures in PROJECT mode) | Known; governance test change deferred; product tests live in `test/product` | OPEN (governance) |
| DEC-010 | Dependency stack | **numpy, pandas, lifelines** pinned in `requirements.txt`; `.venv` local | DECIDED |
| DEC-011 | Primary metric | **C-index primary; IBS reported** | DECIDED |
| DEC-012 | Horizon grid (cycles) | **[50,100,150,200,250]** | DECIDED |
| DEC-013 | Illustrative cost ratio \( C_f/C_p \) | **10** (illustrative only, from SRC-007 example) | DECIDED |
| DEC-007 | Exclude `intake/sources/**` from `discover()` | Optional governance change; not required for SPEC-001 | OPEN (governance) |

## 7. Risks

- PH assumption likely violated on degradation data → fallback path must be real, not nominal.
- Per-unit summary covariates may be weak; time-varying Cox adds complexity.
- Dependency approval delay blocks GREEN phase of TDD tasks.
- Without git, no hook enforcement or history; evidence lives only on disk.

## 8. Required authority

- Spec approval: OWNER (PROMOTE).
- Task activation: OWNER (write policy `APPROVED_TASK`).
- Implementation: A4_TDD_GUIDE (MATERIALIZE) within active task scope.
- Verification: A2_DETERMINISTIC_AUDITOR / A3_CODE_REVIEWER (executor ≠ verifier).
