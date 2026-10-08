# Operating Model

## Every task
`Context -> State -> Authority -> Plan/Spec -> Execute -> Deterministic Verify -> Independent Verify when required -> Handoff -> Audit`.

## Every new agent
1. Read root `AGENTS.md`.
2. Run `repoctl preflight --path <target>`.
3. Load nearest local `AGENTS.md` contracts.
4. Do not infer requirements from an empty folder.
5. Respect the repository maturity and authority matrix.

## Circuit breaker
After three failed repair attempts for the same failure class, stop. Preserve evidence, emit an incident/blocker and escalate. Do not use destructive broad rollback commands as an automatic recovery mechanism.
