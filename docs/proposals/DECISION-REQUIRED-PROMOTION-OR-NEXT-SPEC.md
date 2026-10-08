# DECISION REQUIRED — Promotion vs next specification

Status: **DECIDED — HG-003 = B (OWNER, chat 2026-10-08)**  
Applied: TASK-007 early-window slopes; FD001 evidence regenerated; not promoted  
Created: 2026-10-07 (session GEC-004)  
Closed: 2026-10-08  
Blocks remaining: promotion; SPEC-002; production release

## HUMAN_GATE_ID

`HG-003-PROMOTION-OR-NEXT-SPEC`

## DECISION_REQUIRED

Choose what happens after SPEC-001 baseline evidence is implemented and independently reviewed as PARTIAL (same-session reviewer; documented covariate limitation).

## WHY_IT_CANNOT_BE_DECIDED_AUTOMATICALLY

- `IMPLEMENTED != VERIFIED != PROMOTED`. Promotion and production release are owner-only (`config/authority.json`).
- The model card records a real limitation: full-trajectory slope covariates are partly confounded with duration on run-to-failure units. Whether that is acceptable for a portfolio baseline, or must be fixed before any public claim, is owner meaning.
- The next product jump (Streamlit/Gradio hosting) is a new spec (SPEC-001 §2 non-goal).
- Independent review in this session cannot fully satisfy `executor != verifier`.

## OPTION_A — Accept as portfolio baseline evidence (no production)

Keep status **IMPLEMENTED / not PROMOTED**. Allow a later SPEC-002 for an interactive cost calculator only after you say so. Do not publish hosting or claim production.

### CONSEQUENCE_A
Work stops on product code until a new spec is approved. Evidence (`reports/eval_FD001.*`, `models/MODEL_CARD_FD001.md`) remains in-repo.

## OPTION_B — Require a covariate fix before any public claim

Authorize a new task under SPEC-001: early-window-only slopes (or counting-process Cox) and re-run evidence. Then re-review.

### CONSEQUENCE_B
C-index will likely drop; the claim becomes more honest as a prognostic model. Extra implementation cycle.

## OPTION_C — Approve SPEC-002 (interactive decision surface) now

Web app / container / public URL as originally sketched in SRC-007. Requires a new spec (scope, non-goals, hosting, no-spend constraint).

### CONSEQUENCE_C
New architecture/spec cycle; still no production release unless you also authorize RELEASE.

## RECOMMENDED_OPTION

**OPTION_A**, with optional later B if you want the ranking metric to be a true remaining-life score rather than a degradation-rate correlate.

## RECOMMENDATION_BASIS

SPEC-001 acceptance criteria for a governed baseline are met on fixtures and the FD001 evidence bundle. The remaining issues are claim-strength and promotion, not missing CLI/tests.

## Owner response format (minimal)

```text
DECISION HG-003 = A | B | C
```
