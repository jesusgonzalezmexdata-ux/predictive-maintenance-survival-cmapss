# DECISION REQUIRED — Select Canonical Objective

Status: **DECIDED — HG-001 = A; DEC-006 = Q3; PROJECT_KIND = DATA_SCIENCE**  
Decided by: OWNER (chat instruction "desarrolla A", 2026-10-07, session GEC-003)  
Applied: `intake/OBJECTIVE.md` ingested → `INTENT-446E2407EF97` (state SCAFFOLDED); quarantined bundles kept as evidence only  
Decision ID: `DEC-001-SELECT-CANONICAL-OBJECTIVE`  
Updated: 2026-10-07 (session GEC-002; sources SRC-006/SRC-007 qualified; quarantined auto-ingest)  
Report class: historical record; remaining open decisions moved to `docs/specs/SPEC-001-cmapss-survival-baseline.md` §6  
Blocks (historical): intent normalization that owner trusts, architecture scaffolding, specification, tasks, implementation

---

## HUMAN_GATE_ID

`HG-001-SELECT-CANONICAL-OBJECTIVE`

## DECISION_REQUIRED

Select the first canonical product/project objective to place in `intake/` (recommended: `intake/OBJECTIVE.md` with `MDA-Intent: true`) and normalize via `repoctl reconcile-intake` — **after** disposing quarantined source-derived intents (DEC-006).

## WHY_IT_CANNOT_BE_DECIDED_AUTOMATICALLY

Raw sources under `intake/sources/` support more than one materially different product direction (tabular AI4I failure analytics vs NASA C-MAPSS RUL/survival vs dual-track study). SRC-007 strengthens a survival/cost-policy framing but still allows AI4I **or** NASA as the public anchor. SRC-006 is portfolio meta-guidance, not a product objective. Repository policy forbids converting sources into requirements or silently resolving semantic ambiguity. `DESARROLLO_GITHUB_PROYECTO_5.txt` is empty.

Additionally, kernel discovery currently treats `intake/sources/*.md` as ingestible intents. Two `NEEDS_DECISION` bundles exist and are **quarantined** — they are not owner-promoted canonical meaning.

## OPTION_A

Adopt **Candidate A** — Survival / RUL MLOps focused on NASA C-MAPSS, with Weibull/Cox + cost-optimized maintenance policy themes from SRC-007 as **proposed** acceptance language (draft in `docs/proposals/INTENT-PROPOSAL-predictive-maintenance-survival.md`).

### CONSEQUENCE_A

- Project-Kind likely `DATA_SCIENCE` (or `RESEARCH` if owner prefers DEC-002).
- First scaffold centers turbofan degradation / censored trajectories / survival evaluation.
- AI4I becomes non-goal or later expansion unless explicitly added.
- SRC-006 themes may appear as documentation quality constraints, not as the product objective.
- After owner copies draft to `intake/OBJECTIVE.md` and reconciles, architecture materialization can proceed under SCAFFOLD_ONLY.

## OPTION_B

Adopt **Candidate B** — Dual-dataset study (AI4I + C-MAPSS) under one governed MLOps evidence frame, optionally including cost-policy survival track from SRC-007.

### CONSEQUENCE_B

- Broader first topology and work package.
- Requires explicit metric/protocol separation between datasets.
- Higher planning complexity before first implementation task.

## OPTION_C

Adopt **Candidate C** — AI4I-first tabular predictive maintenance; defer C-MAPSS/survival.

### CONSEQUENCE_C

- Faster narrow first milestone on `ai4i2020.csv`.
- Conflicts with repository name emphasis on survival unless owner accepts rename/scope reframing later.
- Weakens alignment with SRC-007’s survival/cost-policy thesis unless reframed as secondary.

## RECOMMENDED_OPTION

**OPTION_A**

## RECOMMENDATION_BASIS

- Repository directory name emphasizes survival + predictive maintenance + MLOps.
- Strongest local scientific archive is NASA C-MAPSS with explicit RUL / pre-failure truncation semantics.
- SRC-007 independently supports survival (Weibull/Cox), right-censoring, and cost-optimized replacement as excellence criteria.
- AI4I remains available later; choosing A does not destroy that evidence.
- Recommendation is advisory only (`PROPOSAL != DECISION`).

## Secondary decisions

| ID | Decision | Why | Blocks scaffold? |
|----|----------|-----|------------------|
| DEC-006 | Disposition of quarantined `INTENT-A65ACF71731C` and `INTENT-B8EFB6BFC67C` | Source-derived; must not be mistaken for owner intent | **Yes** (clarity before next reconcile) |
| DEC-002 | `DATA_SCIENCE` vs `RESEARCH` project kind | Changes scaffold profile scopes | After HG-001 |
| DEC-003 | Canonical NASA packaging: `Proyect_5_Nasa.zip` vs nested turbofan zip | Avoid duplicate raw boundaries | After HG-001 |
| DEC-004 | Whether multi‑MB dataset zips stay in git / intake or move to external artifact storage | Supply-chain and repo size policy | After HG-001 |
| DEC-005 | Include or exclude Kaggle preprocessed survival dataset | Listed in notes; not present locally | After HG-001 |
| DEC-007 | Whether `intake/sources/**` should be excluded from `discover()` | Prevents future source-as-intent contamination | Governance change; optional |

### DEC-006 options (required with HG-001)

| Option | Meaning |
|--------|---------|
| **Q1 REJECT** | Owner rejects both quarantined bundles as non-canonical; keep files only as evidence; do not scaffold from them |
| **Q2 ADOPT-A65-AFTER-REWRITE** | Owner rewrites SRC-007 themes into a proper `intake/OBJECTIVE.md`, then explicit `ingest`; leave B8EF rejected |
| **Q3 KEEP-AS-EVIDENCE-ONLY** | Leave quarantined bundles on disk marked QUARANTINED; never use as promotion authority |

**Recommended:** **Q1** or **Q3** (equivalent effect for promotion), plus write a fresh owner `intake/OBJECTIVE.md` from Candidate A/B/C.

## WHAT_CONTINUES_AUTOMATICALLY_AFTER_DECISION

Once owner places a chosen `MDA-Intent: true` Markdown in `intake/` **outside** `sources/` (or explicitly `repoctl ingest <path>` on that file) and clears DEC-006:

1. Agent/owner runs `python .scripts/repoctl.py reconcile-intake` (agent may run if authorized).
2. Kernel emits `docs/intents/INTENT-*/` contract, architecture proposal, bootstrap spec, decisions, work package.
3. If no blocking missing decisions: SCAFFOLD_ONLY scope materialization + adapter compile.
4. Then governed specification/planning can continue until the next true owner gate.

**Do not** re-run reconcile expecting SRC-006/SRC-007 alone to become ready — they lack structured objective/vision and are quarantined.

## Owner response format (minimal)

```text
DECISION HG-001 = A | B | C
DECISION DEC-006 = Q1 | Q2 | Q3
OPTIONAL_EDITS = <none | describe changes to draft>
PROJECT_KIND = DATA_SCIENCE | RESEARCH | OTHER:<value>
```
