# Incubating component registrations

This directory records individually reviewed component registrations. It is
currently a partial catalog containing Quality-Bounded Inference only, not a
complete organization inventory. The historical inventory remains in
[repo-inventory.md](../repo-inventory.md).

The component and repository records are paired by `component_ids`:

- [ecosystem-components.json](ecosystem-components.json) describes the component.
- [repository-portfolio.json](repository-portfolio.json) describes its repository.
- Each file has a corresponding `*.schema.json` using JSON Schema Draft 2020-12.

The record separates the artifact's role (`system_role`) from its delivery
(`delivery_model`), process topology (`deployment_topology`) and execution planes.
`integration_contracts` contains versioned typed contracts; existing, unversioned
hooks belong in `integration_surfaces`. QBI claims no typed domain contract.
`maintainers`, `maintainer_profiles` and `advisors` are display metadata; they do
not establish compatibility, lifecycle state or admission.

## Quality-Bounded Inference

QBI is an incubating, in-process, request-level control-plane component delivered
as an extension bundle. Its canonical organization repository is private, so the
portfolio record uses `public_surface: false`. Registration does not publish the
repository or establish a website display contract.

`integration_tested` records the historical vLLM 0.19.1 / Extension Bundle
`0.2-experimental` integration described in [PR #12](https://github.com/vLLM-HUST/vllm-hust-docs/pull/12):
manager acceptance, loading in the API/engine/worker processes, and a request-bound
pre-action read. It does not establish compatibility with the current Manifest
`0.3-experimental` described in the [extension author guide](../operations/extension-author-guide.md).
No throughput, latency or complete-task quality claim is made. Compatibility
with a new host or manifest requires separate validation; absent the required
request-entry reading point, the extension must fail closed.

The original registration reported Extension Manager `0.2.0.dev0` at
`00c9b336` and a vLLM `0.19.1+empty` carrier on Ascend 910B2. Its reported
checks covered list/inspect/validate/enable/plan/render, loading in four processes
(API server, EngineCore and two workers), pre-admission rejection of an
unsupported mechanism or missing source receipt, and a matching receipt for a
valid request binding. No model completion was consumed. These are historical
reports retained for provenance, not checks rerun by this registration's CI.

## Validation

Install the validation dependency and run:

```sh
python -m pip install jsonschema==4.25.1
python scripts/validate_ecosystem_registry.py
python scripts/check_markdown_links.py
```

The validator checks both schemas, unique identities, contract/surface separation
and component-to-repository references. CI runs the same validation.
