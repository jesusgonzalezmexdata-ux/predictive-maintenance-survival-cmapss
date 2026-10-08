# Bootstrap Specification — Predictive Maintenance Survival MLOps

Spec ID: `SPEC-446E2407EF97`
Derived from: `INTENT-446E2407EF97`

## Problem / objective

Establish the governed architecture and first bootstrap specification required to ingest NASA C-MAPSS-style run-to-failure data, represent right-censored trajectories, train and evaluate baseline Weibull/Cox (or justified AFT/RSF alternatives) survival/RUL models, and produce auditable evidence suitable for later task-scoped implementation of a cost-optimized maintenance recommendation surface.

## Required repository outcome

- Declare governed scope `src`.
- Declare governed scope `data/raw`.
- Declare governed scope `data/processed`.
- Declare governed scope `notebooks`.
- Declare governed scope `models`.
- Declare governed scope `reports`.
- Declare governed scope `test/product`.
- Generate tool adapters from canonical MDA.
- Preserve `CORE_CONTRACT != TOOL_ADAPTER`.
- Keep product implementation absent until governed tasks exist.

## Deliverables

- Normalized intent contract and architecture proposal.
- DATA_SCIENCE scaffold scopes with local AGENTS.md / SCOPE_STATE.json.
- Bootstrap specification and initial work package for planning.
- Explicit decisions file for unresolved semantics.

## Acceptance criteria

- `repoctl verify` remains PASS after SCAFFOLD_ONLY materialization.
- Product scopes exist but contain no invented product implementation.
- A new agent can resolve root and local contracts without conversational memory.
- Bootstrap spec records open decisions for primary metrics, hosting, and NASA packaging.

## Non-goals

- Selecting a production model family without a governed task/spec.
- Committing sensitive or redistributed datasets by default.
- Implementing full MLOps cloud infrastructure or public hosting in the first scaffold.
- Promoting SRC-006 portfolio methodology as this repository's product objective.
