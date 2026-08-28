# vllm-hust-docs

This repository contains vllm-hust documentation, sync notes, and fork-specific operation guides.

## Scope

- Upstream sync notes and decision logs.
- Fork-only deployment and hardware compatibility guides.
- Workspace-level developer playbooks.

## Principles

- Keep runtime code changes in `vllm-hust` minimal and upstream-merge-safe.
- Move process and documentation changes here whenever possible.
- Track compatibility matrices and migration notes explicitly.

## Suggested Layout

- `presentations/` — reusable introduction decks, overview slides, and externally reusable presentation assets.
- `meetings/` — internal meeting materials, decks, talk tracks, and action lists.
- `sync-notes/` — upstream sync notes and merge records.
- `operations/` — deployment, runtime, and hardware operation guides.
- `architecture/` — source code deconstruction, module maps, and internal design notes.
- `governance/` — organization-wide ownership, repository lifecycle, and graduation rules.
- `registry/` — machine-readable ecosystem classifications and their schemas.

## Key Documents

- `architecture/ecosystem-architecture.md` — normative organization-wide boundaries between the runtime core, platform profiles, runtime components, KV state systems, control planes, plugin bundles, and evidence tooling.
- `architecture/kv-systems-and-connector-materialization.md` — normative design gate separating KV systems, connector bridges, and bundle delivery while preserving factory-owned role, HMA, composition, and rollback behavior.
- `governance/repository-lifecycle.md` — ownership and lifecycle policy for core, incubating, certified external, deprecated, and archived repositories or integrations.
- `registry/ecosystem-components.json` — canonical machine-readable ecosystem catalog consumed by public documentation and the website.
- `registry/repository-portfolio.json` — organization-wide inventory that assigns every repository a lifecycle, role, runtime relationship, and canonical artifact scope without treating repositories as runtime components.
- `registry/repository-profile.schema.json` — contract for repository-local `.vllm-hust/repository-profile.json` declarations.
- `operations/extension-bundle-v1-migration.md` — normative static-admission contract, legacy compatibility policy, migration matrix, acceptance gates, and rollback sequence for Extension Bundle v1.

- `operations/optimization-repository-playbook.md` — a reusable playbook for optimization repositories that pin runtime dependencies with submodules, manage feature branches, preserve experiment provenance, and decide when upstream PRs are appropriate.
- `architecture/vllm-hust-source-deconstruction.md` — a layered source walkthrough of the `vllm-hust` fork, including request flow, engine structure, execution path, and fork-specific extension surfaces.
- `architecture/vllm-hust-engine-execution-chain.md` — a deeper walkthrough of the request-to-engine-to-worker execution path.
- `architecture/vllm-hust-platform-plugin-chain.md` — a focused breakdown of platform detection, plugin activation, and fork-safe hardware extension points.
- `architecture/vllm-hust-multimodal-agi4s-capabilities.md` — a focused map of multimodal, reasoning, tool-calling, and AGI4S-facing capability modules.
- `architecture/vllm-hust-source-call-flow.md` — detailed source call-flow diagrams for CLI serve startup and OpenAI request handling.
