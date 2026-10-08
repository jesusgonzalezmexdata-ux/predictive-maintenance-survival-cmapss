# Automation

Four automation classes remain deliberately separate.

- **Event-driven:** intent arrival, agent spawn, task start, pre-write, post-write, commit and completion.
- **Scheduled:** daily drift, weekly Agent QA, monthly governance review.
- **Condition-driven:** circuit breaker, budget threshold, policy violation and audit break.
- **Human-gated:** governance promotion, production release, federation publishing and economic spend.

## Intent arrival

`intent_arrival` is an event-driven architecture-scaffolding event. It may normalize owner intent, produce architecture/spec/work-package artifacts, declare product scopes, compile adapters and append evidence. It may not generate arbitrary product implementation.

The local watcher (`.scripts/watch_intake.py`) provides file-arrival behavior. `repoctl reconcile-intake` provides deterministic one-shot behavior suitable for shells, IDE tasks or external automation.

## Scheduled work

Scheduled jobs may append evidence/reports but may not mutate canonical or product state. This prevents a nightly model or scheduler from silently rewriting governance.
