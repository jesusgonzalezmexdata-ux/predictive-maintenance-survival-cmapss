# DECISION REQUIRED — Approve SPEC-001 and unblock first implementation tasks

Status: **OWNER_GATE**  
Created: 2026-10-07 (session GEC-003)  
Blocks: activation of TASK-001..006; any product code under `src/`, `data/`, `models/`, `reports/`, `test/product/`

## HUMAN_GATE_ID

`HG-002-APPROVE-SPEC-001-AND-STACK`

## DECISION_REQUIRED

1. Approve `docs/specs/SPEC-001-cmapss-survival-baseline.md` (or request edits).
2. Resolve the three decisions that TASK-001/003 cannot start without:
   - **DEC-003** canonical NASA archive (SRC-003 expanded vs SRC-004 nested)
   - **DEC-004** raw data policy (external path only + `.gitignore` vs commit)
   - **DEC-010** dependency stack (`numpy`, `pandas`, `lifelines`)
3. Optionally resolve DEC-008 (init git + hooks), DEC-011/012/013 (metric primacy, horizon grid, illustrative cost ratio). Defaults are listed in SPEC-001 §6 and will be used if you only say "defaults".

## WHY_IT_CANNOT_BE_DECIDED_AUTOMATICALLY

- Product scopes have write policy `APPROVED_TASK`; no task is active. Implementation authority is `TASK_SCOPED`, and activation belongs to OWNER.
- Dependency additions are supply-chain events (root contract).
- Committing ~25 MB of raw archives is a data-retention/redistribution decision.
- Spec contains semantic choices (event definition, censoring, metric primacy, cost defaults) that are owner meaning, not agent inference.

## OPTION_A — Approve SPEC-001 with defaults

`DEC-003 = SRC-003`, `DEC-004 = external path + .gitignore data/raw/*`, `DEC-010 = numpy+pandas+lifelines`, `DEC-008 = init git + hooks`, DEC-011/012/013 defaults.

### CONSEQUENCE_A
TASK-001 → TASK-006 can be activated sequentially; implementation proceeds under TDD with offline fixtures; evidence bundle produced; independent review; then promotion gate.

## OPTION_B — Approve with edits

State edits (e.g. include FD002–FD004, use `scikit-survival` instead of `lifelines`, commit data). Spec is revised, re-presented, then same path as A.

### CONSEQUENCE_B
One revision cycle before tasks activate.

## OPTION_C — Reject / defer

### CONSEQUENCE_C
Repository stays at ARCHITECTURE_MATERIALIZED with specs PROPOSED; no code.

## RECOMMENDED_OPTION

**OPTION_A**

## RECOMMENDATION_BASIS

Narrowest first milestone that still demonstrates the three senior signals (censoring, PH-assumption discipline, cost-optimal \( t^* \)); `lifelines` covers Weibull/Cox/PH tests in one dependency; external data path avoids redistributing NASA archives via git.

## WHAT_CONTINUES_AUTOMATICALLY_AFTER_DECISION

1. Record decisions in SPEC-001 §6 and task JSONs (status → ACTIVE one at a time).
2. If DEC-008 approved: `git init`, `.gitignore` for `data/raw/*`, `repoctl install-hooks`.
3. Dependency manifest written; TDD cycle per task; `repoctl verify` + `security-scan` after each.
4. TASK-006 independent review; handoff; stop at promotion gate (OWNER).

## Owner response format (minimal)

```text
DECISION HG-002 = A | B:<edits> | C
```
