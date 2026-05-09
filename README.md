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

## Key Documents

- `architecture/vllm-hust-source-deconstruction.md` — a layered source walkthrough of the `vllm-hust` fork, including request flow, engine structure, execution path, and fork-specific extension surfaces.
- `architecture/vllm-hust-engine-execution-chain.md` — a deeper walkthrough of the request-to-engine-to-worker execution path.
- `architecture/vllm-hust-platform-plugin-chain.md` — a focused breakdown of platform detection, plugin activation, and fork-safe hardware extension points.
- `architecture/vllm-hust-multimodal-agi4s-capabilities.md` — a focused map of multimodal, reasoning, tool-calling, and AGI4S-facing capability modules.
- `architecture/vllm-hust-source-call-flow.md` — detailed source call-flow diagrams for CLI serve startup and OpenAI request handling.
