# Architecture Proposal — Proyecto 5 Mantenimiento predictivo con análisis de supervivencia (Weibull y Cox)

Status: **NEEDS_DECISION**

Intent: `INTENT-A65ACF71731C`
Source: `intake/sources/Proyecto_5_Mantenimiento predictivo con análisis de supervivencia (Weibull y Cox).md`
Class: `PROJECT`
Project kind: `GENERIC`

## Objective

_Missing: objective or vision must be supplied._

## Architecture profile

Minimal language-agnostic product topology.

## Proposed governed scopes

- `src` — Product implementation source.
- `test/product` — Product-level deterministic tests.

## Governance behavior

- Every materialized scope receives a local `AGENTS.md` and `SCOPE_STATE.json`.
- The intent layer may scaffold topology/specification but does not generate product implementation.
- Missing decisions remain explicit and block claims of implementation readiness.
- Any agent entering a scope resolves root + nearest local contract before effectful work.

## Constraints

- No additional constraints were declared; do not invent them.

## Acceptance criteria

- Acceptance criteria are not yet declared; implementation readiness remains incomplete.
