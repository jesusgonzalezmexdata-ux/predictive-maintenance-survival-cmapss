# MDA — Canonical Governance Source

This directory is the source of truth for agent behavior. `repoctl compile` translates MDA into tool-native files. MDA here is an internal repository specification, not a claim of an external industry standard.

Never hand-edit generated root/tool adapters when the intended change belongs in `.mda/source/`. Change canonical source, verify, then compile.

## Intent compiler sources (v2)

- `source/intake.mda.json` defines accepted intent inputs, semantic states and safety invariants.
- `source/scaffold-profiles.mda.json` defines deterministic language-agnostic product topologies.
- `schemas/intent.schema.json` defines the normalized intent contract.

These sources extend the existing 19-point architecture; they do not introduce a Point 20.
