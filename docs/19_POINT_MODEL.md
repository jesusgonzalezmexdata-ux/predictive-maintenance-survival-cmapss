# 19-Point Capability Model

1. **Universal File Architecture / MDA** — minimum `M0_SEED`, default `ENFORCED`. Single canonical source compiled to tool-native adapters.
2. **Base Behavior Contract / AGENTS.md** — minimum `M0_SEED`, default `ENFORCED`. Define non-negotiable behavior and authority boundaries.
3. **Routing Matrix: Frontier vs Local** — minimum `M1_GUARDED`, default `ENABLED`. Route tasks by risk, complexity, privacy and cost.
4. **Deterministic Guardrails and Sandboxing** — minimum `M1_GUARDED`, default `ENFORCED`. Enforce filesystem, command and execution boundaries outside model discretion.
5. **Agnostic Execution Contract and Reproducibility** — minimum `M0_SEED`, default `ENFORCED`. Expose stable verification commands independent of language/framework.
6. **Daily Work Protocol** — minimum `M0_SEED`, default `ENFORCED`. Require Context -> Plan -> Execute -> Verify -> Handoff.
7. **Multi-Environment Synchronization** — minimum `M0_SEED`, default `ENFORCED`. Generate every adapter from canonical MDA and detect drift.
8. **Structured Memory and Decay** — minimum `M1_GUARDED`, default `ENABLED`. Separate ephemeral session memory from governed long-term decisions.
9. **Traceability, Telemetry and Forensic Log** — minimum `M1_GUARDED`, default `ENFORCED`. Maintain append-only hash-chained evidence of governed actions.
10. **Circuit Breakers and Recovery** — minimum `M1_GUARDED`, default `ENFORCED`. Stop autonomous loops and escalate after bounded retries.
11. **Evolutionary Governance and Meta-Learning** — minimum `M2_GOVERNED`, default `CONFIGURED`. Convert incidents into proposed governance changes; never auto-promote them.
12. **Continuous Agent QA and Benchmarking** — minimum `M2_GOVERNED`, default `CONFIGURED`. Evaluate agent behavior before governance changes are promoted.
13. **Resource and Token Economy Governance** — minimum `M2_GOVERNED`, default `CONFIGURED`. Bound model, token, CPU/GPU and monetary consumption per task.
14. **Human-Agent Onboarding and Context Transfer** — minimum `M0_SEED`, default `ENFORCED`. Make repository entry deterministic for humans and agents.
15. **Data Security, Prompt Privacy and Supply Chain** — minimum `M1_GUARDED`, default `ENABLED`. Prevent secret leakage and unsafe dependency introduction.
16. **Repository Digital Twin / Shadow Simulation** — minimum `M3_SHADOW`, default `DECLARED`. Simulate candidate plans in isolated worktrees before real mutation.
17. **Federated Cross-Repository Swarm Intelligence** — minimum `M4_FEDERATED`, default `DECLARED`. Share abstract patterns without source code or identifying context.
18. **Autonomous Economic Agency** — minimum `M5_ECONOMIC`, default `DECLARED`. Optimize compute/model spend inside explicit signing limits.
19. **Orchestration, Subagents and Event Fabric** — minimum `M0_SEED`, default `ENFORCED`. Define who acts, when events fire and how handoffs are recorded.

## v2 intent layer mapping (not a Point 20)

Intent-driven bootstrap is a cross-cutting compiler over the existing model, not an additional capability point:

- **P01** — MDA stores the normalized architecture rules and scaffold profiles.
- **P02** — generated root/local `AGENTS.md` files bind agents to the resulting scopes.
- **P05** — `repoctl ingest/reconcile-intake` provide the deterministic execution contract.
- **P06** — intent is normalized before plan/spec/execution.
- **P09** — ingestion, reconciliation and changes are audit events.
- **P10** — changed/conflicting intent stops automatic reconciliation.
- **P14** — a new human/agent can start from the Markdown objective and generated contracts.
- **P19** — `intent_arrival` is an event in the orchestration fabric.

The 19-point architecture therefore remains closed and intact.
