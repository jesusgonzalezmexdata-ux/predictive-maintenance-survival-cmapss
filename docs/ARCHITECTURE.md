# Architecture

## Layers
1. **Canonical behavior layer** — `.mda/source`, authority and capability states.
2. **Enforcement kernel** — `.scripts/repoctl` plus Git/CI/sandbox gates.
3. **Agent layer** — roles, skills and structured handoffs.
4. **Adapter layer** — generated files for Codex, Claude, Cursor, Copilot, Gemini, Windsurf, Aider and future tools.
5. **Evidence layer** — hash-chained audit, reports, metrics and incidents.
6. **Frontier layer** — shadow simulation, federation and economic agency behind maturity/authority gates.

## Replacement rule
A provider-native feature may optimize ergonomics but may never become the sole enforcement point for a canonical guarantee.

## State rule
`GREENFIELD` describes absence of product implementation, not absence of governance. Requirements must be declared before materialization.

## v2 Intent compiler

The v2 kernel adds an intent-compilation layer ahead of normal SDD work. Markdown supplied by the owner is normalized into a content-addressed contract. A deterministic scaffold profile then declares product scopes and compiles local contracts. This layer is intentionally incapable of generating arbitrary product implementation; it terminates at architecture/spec/work-package readiness.

Canonical sources: `.mda/source/intake.mda.json` and `.mda/source/scaffold-profiles.mda.json`. Runtime/derived artifacts: `docs/intents/` and generated local scope contracts.
