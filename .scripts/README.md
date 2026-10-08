# repoctl — Governance Kernel

`repoctl` is the stable, provider-agnostic enforcement and bootstrap interface. Agents call it instead of guessing framework-specific commands. The kernel uses only the Python standard library.

## Intent-driven commands

- `discover-intents` — read-only discovery of new intent sources.
- `ingest <file.md>` — explicitly normalize and scaffold from one Markdown intent.
- `reconcile-intake` — process new files in `intake/` plus marked/recognized intent files in future product folders.
- `python .scripts/watch_intake.py` — event-style local watcher around reconciliation.

## Governance commands

- `inspect`, `preflight`, `context` — repository/target state and effective contract.
- `compile`, `verify`, `security-scan`, `audit-verify` — deterministic validation.
- `init-project`, `declare-scope`, `propose-scope` — explicit state transitions.
- `scheduled ...` — evidence-only recurring governance jobs.

Intent ingestion can scaffold architecture/contracts/specs. It cannot authorize arbitrary product implementation.
