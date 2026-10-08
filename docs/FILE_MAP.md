# File Map

## Human intent entry
- `intake/` — owner-controlled Markdown inbox, template and examples.
- `config/intake.json` — discovery/materialization policy.
- `config/intake-registry.json` — content-addressed source registry.
- `docs/intents/` — normalized contracts, architecture proposals, specs, decisions and work packages.

## Canonical governance
- `.mda/source/` — behavior, 19 capabilities, maturity, authority, events, folder contracts, intake contract and scaffold profiles.
- `.mda/schemas/` — machine-readable contracts including `intent.schema.json`.
- `.agents/` — canonical roles, skills and handoff semantics.
- `config/` — runtime policy parameters, routing, budgets, schedules, security and intake policy.
- `.scripts/repoctl/` — provider-agnostic enforcement + intent compiler kernel.

## Generated adapters/contracts
- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `CONVENTIONS.md`.
- `.cursor/rules/`, `.github/copilot-instructions.md`, `.windsurf/rules/`, `.gemini/settings.json`, `.aider.conf.yml`.
- Local `AGENTS.md` + `SCOPE_STATE.json` inside governed product scopes.

## External enforcement
- `.hooks/` — Git and wrapper gates.
- `.sandbox/` — isolation policy/container profile.
- `.github/workflows/` — deterministic CI plus daily/weekly/monthly governance schedules.

## Evidence and frontier
- `.logs/` — audit/metrics/reports/incidents.
- `.federated/` — P17 quarantined federation surface.
- `test/` — kernel tests and Agent QA fixtures.
