# Intent-Driven Bootstrap Architecture

## Purpose

The intent layer allows a human to describe **what should exist and why** without having to manually instruct each AI agent how to structure the repository.

The canonical flow is:

```text
Markdown Intent
      ↓
Discovery
      ↓
Normalization
      ↓
Semantic Gap Detection
      ↓
Architecture Profile Selection
      ↓
Architecture Proposal + Bootstrap Spec
      ↓
Governed Scope Materialization
      ↓
Adapter Compilation
      ↓
Ready for Spec/Task-Driven Implementation
```

## Accepted sources

1. Any Markdown file explicitly passed to `repoctl ingest`.
2. Markdown files placed in the owner-controlled `intake/` directory.
3. Markdown files elsewhere that contain the exact marker `MDA-Intent: true`.

## What is derived

The normalizer derives or preserves:

- intent ID and content hash;
- intent class (`PROJECT`, `DOMAIN`, `FEATURE`, `RESEARCH`);
- project kind / scaffold profile;
- title, vision, objective and target;
- scope, constraints, deliverables, acceptance criteria and non-goals;
- missing/recommended decisions;
- deterministic architecture topology;
- a bootstrap specification and initial work package.

Explicit metadata wins over inference. Inference never creates domain requirements; it only selects a generic scaffold profile.

## What is never derived silently

The kernel must not invent:

- business requirements;
- success metrics;
- production authority;
- secrets/credentials;
- external integrations;
- spending authority;
- safety/compliance obligations that were never declared;
- product implementation merely because a directory is empty.

Unknowns are emitted into `DECISIONS_REQUIRED.md`.

## Materialization boundary

Intent ingestion may create directories, local agent contracts, state files, specs, proposals and work-package metadata. This is **architecture scaffolding**, not product implementation.

Product code requires a governed task/spec and the authority envelope defined by the root/local contracts.

## Changed intent

An intent already processed is content-addressed. If the source changes, automatic reconciliation returns `CHANGED_REQUIRES_EXPLICIT_REINGEST` rather than silently rewriting an active architecture. The owner must explicitly ingest the changed file again.

## Why this boundary matters

Without this separation, an AI model can transform a vague sentence into hundreds of implementation assumptions. With this separation, the system can automate repository construction while preserving the distinction between human intent, architectural derivation and implementation authority.
