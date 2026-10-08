# Manufacturing Quality Analytics

MDA-Intent: true
Intent-Type: PROJECT
Project-Kind: DATA_SCIENCE
Target: .
Materialization: SCAFFOLD_ONLY

## Vision
Create a reproducible analytics repository that turns manufacturing data into traceable quality evidence.

## Objective
Establish the governed architecture required to ingest datasets, validate them, build analytical models and produce auditable reports without allowing exploratory work to become production authority automatically.

## Scope
- Data ingestion and validation.
- Feature engineering.
- Baseline and candidate models.
- Evaluation evidence and reports.

## Constraints
- No production credentials in the repository.
- Raw sensitive data must not be committed by default.
- Every promoted model must be reproducible from governed inputs.

## Deliverables
- Governed project topology.
- Bootstrap specification.
- Product scopes with local agent contracts.
- Initial work package for implementation planning.

## Acceptance Criteria
- The master repository remains governance-valid after scaffolding.
- Product scopes are declared but contain no invented product implementation.
- A new agent can resolve root and local contracts without extra prompting.

## Non-Goals
- Automatic deployment to production.
- Autonomous model selection with spending authority.
