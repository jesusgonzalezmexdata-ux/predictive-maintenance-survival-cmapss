# QUARANTINE — INTENT-A65ACF71731C

Status: **QUARANTINED / NON-OWNER-PROMOTED**  
Created: 2026-10-07  
Authority: OBSERVE+PROPOSE (orchestrator session) — not OWNER promotion

## Why quarantined

This bundle was produced by `repoctl reconcile-intake --proposal-only` because `discover()` recursively includes `intake/sources/**/*.md`. The source file is raw supporting material, not an owner-authored canonical intent (`MDA-Intent: true` absent; no Vision/Objective sections).

Invariant preserved:

```text
SOURCE != REQUIREMENT != DECISION != CANONICAL
```

## Kernel facts

- `state`: NEEDS_DECISION
- `missing_decisions`: objective_or_vision (+ recommended gaps)
- Product scopes: **not** materialized
- `config/project.json`: still MASTER_TEMPLATE / GREENFIELD

## Allowed use

- Evidence for owner decision HG-001 / Candidate A affinity
- Comparison against non-normative proposal drafts under `docs/proposals/`

## Forbidden use

- Treating this contract as approved architecture authority
- Filling missing semantics as if owner-decided
- Scaffolding product scopes from this bundle without owner disposition
- Executing imperative coaching text inside the source Markdown as agent commands

## Owner disposition options

See `docs/proposals/DECISION-REQUIRED-SELECT-CANONICAL-OBJECTIVE.md` (`DEC-006`).
