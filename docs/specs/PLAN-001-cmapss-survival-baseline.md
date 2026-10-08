# PLAN-001 — Delivery plan for SPEC-001

Status: PROPOSED (non-promoted)  
Spec: `docs/specs/SPEC-001-cmapss-survival-baseline.md`  
Intent: `INTENT-446E2407EF97`

## Stage gates

```text
SPEC-001 approved (OWNER)
  → DEC-003/004/010 resolved (OWNER)
    → TASK-001..006 activated in order (OWNER activates; A4 implements; A2/A3 verify)
      → deterministic validation (repoctl verify + unittest)
        → independent review (deterministic-review skill)
          → promotion decision (OWNER)
```

## Task sequence

| Order | Task | Depends on | Scope | Role |
|-------|------|-----------|-------|------|
| 1 | TASK-001 data boundary + manifest + loader | DEC-003, DEC-004 | `data/raw`, `src`, `test/product` | A4 |
| 2 | TASK-002 survival table + censoring + grouped split | TASK-001 | `src`, `data/processed`, `test/product` | A4 |
| 3 | TASK-003 Weibull + Cox baselines + PH test | TASK-002, DEC-010 | `src`, `test/product` | A4 |
| 4 | TASK-004 metrics + deterministic report + model card | TASK-003, DEC-011/012 | `src`, `reports`, `models`, `test/product` | A4 |
| 5 | TASK-005 cost-policy function + tests | TASK-003, DEC-013 | `src`, `test/product` | A4 |
| 6 | TASK-006 end-to-end CLI run + evidence bundle + review | TASK-004, TASK-005 | `src`, `reports`, `.agents/handoffs` | A4 → A2/A3 |

## Context package per task (minimum)

- Root `AGENTS.md`, local `AGENTS.md` of touched scopes
- SPEC-001 sections referenced by the task
- Task JSON
- Qualified source excerpts only (C-MAPSS column layout; cost formula) — not full source files
- Validation commands listed in task

## Verification policy

- Each task: RED → GREEN → REFACTOR (tdd-workflow skill); tests offline on fixtures.
- After each task: `python .scripts/repoctl.py verify`, `python .scripts/repoctl.py security-scan`.
- Circuit breaker: 3 repair attempts per failure class, then incident report.

## Explicitly deferred (future specs)

- SPEC-002 interactive decision surface (Streamlit/Gradio) + container
- SPEC-003 FD002–FD004 multi-condition generalization
- SPEC-004 AI4I tabular contrast track (if owner reopens Candidate B)
