# ADR-0006 — Intent is canonical input, not product authority

Status: ACCEPTED

## Decision

Owner-authored Markdown intent may be normalized and may trigger deterministic architecture scaffolding. It does not by itself authorize arbitrary product implementation.

The intake compiler emits a normalized contract, architecture proposal, bootstrap spec, decisions report, work package and local scope contracts. Product implementation still requires governed task authority and deterministic verification.

## Rationale

The repository's purpose is to minimize repeated prompting while preventing a model from turning vague intent into undocumented requirements. Treating intent as a first-class source solves the first problem; separating scaffolding from implementation solves the second.

## Consequences

- A folder can remain semantically rich while containing no product implementation.
- New agents can discover the objective through generated local contracts and intent references.
- Missing acceptance criteria remain visible instead of being hallucinated.
- Updating an already-ingested intent requires explicit re-ingestion rather than silent architectural drift.
