# INCIDENT-2026-10-07-SOURCE-AS-INTENT-DISCOVERY

Status: MITIGATED (DEC-006 = Q3 applied by OWNER 2026-10-07; bundles remain quarantined evidence; DEC-007 discover-path change still optional)  
Severity: MEDIUM (workflow contamination; no product scaffold; no implementation)  
Actor discovering: A1_ORCHESTRATOR  
Circuit breaker: not tripped (single occurrence; no retry loop)

## Trigger

Session continuation ran:

```bash
python .scripts/repoctl.py reconcile-intake --proposal-only
```

Kernel `discover()` recursively lists all `intake/**/*.md` except examples/templates. Two raw files under `intake/sources/` were therefore treated as intents and proposal-ingested:

- `INTENT-B8EFB6BFC67C` ← SRC-006 methodology notes
- `INTENT-A65ACF71731C` ← SRC-007 project brief notes

Both lack structured `objective_or_vision` → state `NEEDS_DECISION`. No product scopes materialized. Project remains GREENFIELD / MASTER_TEMPLATE.

## Affected scope

- `config/intake-registry.json`
- `docs/intents/INTENT-A65ACF71731C/**`
- `docs/intents/INTENT-B8EFB6BFC67C/**`
- Audit event `intent_reconcile` (kernel)

## Preserved evidence

- `.logs/reports/2026-10-07_SOURCE_INVENTORY_v2.json`
- Quarantine markers in both intent directories
- Prior CASE_D proposals under `docs/proposals/`
- `python .scripts/repoctl.py verify` → PASS after event

## Attempts made

1. Re-inspect / verify / preflight after ingest — confirmed no project init, no product scopes.
2. Quarantine labels added; inventory/qualification updated.
3. Did **not** delete registry entries or intent folders (destructive without owner authority).
4. Did **not** invent objective/vision to force scaffold.

## Current blocker

Owner must select canonical objective (HG-001) and disposition quarantined source-derived intents (DEC-006). Optional future governance change: exclude `intake/sources/**` from discover (DEC-007) — requires governance authority.

## Required human authority

OWNER for HG-001 + DEC-006. OWNER/governance for DEC-007 if discover path should be changed.
