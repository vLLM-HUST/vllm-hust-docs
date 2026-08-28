# Extension Bundle v1 Migration and Acceptance

Status: **normative implementation record**

## 1. Purpose and non-goals

Extension Bundle v1 standardizes delivery, static admission, and process-local
startup snapshots. It does not make every ecosystem artifact a plugin and does
not replace domain behavior with a universal callback API.

The following remain distinct:

- a bundle is a versioned delivery and governance unit;
- a component implements one or more typed runtime contracts;
- a KV connector adapts scheduler and worker processes to an external KV system;
- a platform profile is a coordinated hardware integration distribution;
- an external control plane is a separate application; only its bridge is a
  runtime component;
- Mooncake, LMCache, and PegaFlow retain their external-system identities.

## 2. Current implementation boundary

The implementation lives under `vllm/plugins/` in `vllm-hust`:

| Concern | Source | Current behavior |
|---|---|---|
| domain identities | `contracts.py` | immutable bundle/component descriptors, contracts, execution planes, isolation, permissions |
| wire schema | `manifest.schema.json` | packaged Draft 2020-12 schema with closed fields and enum vocabulary |
| parser | `manifest.py` | rejects unknown/missing fields, unknown enum values, symlinks, malformed JSON, and invalid identities before implementation import |
| admission | `startup.py` | validates host API range, bundle allowlist, duplicate paths/IDs, permissions, and isolation support |
| process snapshot | `snapshot.py` | immutable ordered bundles/components with contract and execution-plane selection |
| startup integration | `plugins/__init__.py` | builds the typed snapshot before loading legacy general entry points |

The host extension API version is `1.0`. A bundle range uses a deliberately
narrow numeric grammar, for example `>=1,<2`. Supported operators are `>=`,
`<=`, `==`, `!=`, `>`, and `<`; versions have one to three numeric parts.
Whitespace, wildcards, epochs, prerelease syntax, and arbitrary PEP 440 forms
are rejected. This API version is independent of the vLLM product version.

## 3. Manifest v1

The required top-level fields are:

```json
{
  "schema_version": "1.0",
  "bundle_id": "org.example.kv-adapter",
  "bundle_version": "1.0.0",
  "host_api_range": ">=1,<2",
  "components": []
}
```

Each component declares:

- `component_id`;
- one or more `contracts`;
- one or more `execution_planes`;
- `isolation`;
- `implementation_ref`;
- optional `permissions`, defaulting to an empty list.

The schema is the wire-format authority. Python enums are the runtime
authority. Tests MUST prove that both vocabularies remain identical.

Bundle versions use semantic `major.minor.patch` form with optional prerelease
or build suffix. Bundle IDs are case-sensitive lowercase identifiers. A startup
configuration may not contain duplicate paths or duplicate bundle IDs.

## 4. Explicit discovery and enablement

There is no implicit filesystem scan, installed-package scan, network lookup,
or implementation import.

`VLLM_EXTENSION_MANIFESTS` is an OS-path-separator-delimited ordered list of
manifest files. `VLLM_EXTENSION_BUNDLES` is an optional comma-delimited bundle
ID allowlist:

- manifests unset: build an empty snapshot;
- allowlist unset: admit all explicitly configured compatible manifests;
- allowlist empty: validate the configured manifests but enable none;
- unknown allowlist ID: fail startup;
- malformed, incompatible, or duplicated disabled manifest: fail startup rather
  than leave invalid deployment configuration hidden.

Configuration order defines deterministic snapshot order. Domain materializers
MUST NOT use discovery order as an implicit conflict-resolution policy.

## 5. Permissions and isolation

Permissions are auditable capability requests, not claims that a sandbox exists.
The known vocabulary is `device_access`, `filesystem_read`, `filesystem_write`,
`ipc`, `network_egress`, `shared_memory`, and `subprocess`.

The configured startup path currently grants no non-empty permission by
default. A non-empty request fails admission unless a host call supplies an
explicit permission policy. `trusted_in_process` still has the ambient authority
of the host process; its declaration is not enforcement.

Only `trusted_in_process` is currently admitted by the configured startup path.
`process_isolated` and `sandboxed_process` are schema identities reserved for a
materializer that actually implements their lifecycle and enforcement. Merely
starting an ordinary subprocess MUST NOT be described as sandboxing.

## 6. Lifecycle and state ownership

The generic loader owns these states only:

```text
configured -> parsed -> admitted | disabled | rejected -> snapshotted
```

`rejected` is fail-closed and raises a path- and bundle-specific admission
error. `disabled` means a valid compatible manifest was excluded by the explicit
bundle allowlist. The startup snapshot is immutable for the process lifetime.

Initialize, ready, degraded, failed, restart, drain, and shutdown semantics are
domain- or isolation-materializer responsibilities. They MUST NOT be added to a
generic lifecycle enum until a real executor implements and tests them. The
generic loader does not import `implementation_ref` and does not launch sidecars.

## 7. Process and frontend/backend boundary

API, scheduler, worker, native, device, and bridge are execution planes, not
frontend page categories. A component is materialized only in a process that:

1. owns the declared domain contract;
2. matches the declared execution plane;
3. supports the declared isolation and permissions;
4. has an explicit domain composition policy.

A KV integration normally uses distinct scheduler and worker components in one
bundle. An external control plane exposes no in-engine plugin object; a local
bridge may implement `vllm.control.action.v1` and
`vllm.control.receipt.v1`.

## 8. Legacy compatibility profile

`VLLM_PLUGINS` and the existing Python entry-point groups remain unchanged
during migration. They are separate from `VLLM_EXTENSION_MANIFESTS` and
`VLLM_EXTENSION_BUNDLES`.

| Existing surface | Migration classification | Bundle v1 status |
|---|---|---|
| `vllm.general_plugins` | legacy import-time mutation compatibility | retained; not bundle-conformant |
| `vllm.platform_plugins` | platform profile/component materialization | contract identity exists; materializer pending |
| `vllm.io_processor_plugins` | API-plane IO processor | contract identity exists; behavior adapter pending |
| `vllm.stat_logger_plugins` | telemetry/stat logger | contract identities exist; behavior adapter pending |
| model registry / out-of-tree model | model descriptor plus implementation registration | dedicated contract missing |
| reasoning and tool parsers | explicit API-plane parser selection | dedicated contract missing |
| LoRA resolvers | artifact/model resolution | dedicated contract missing |
| KV connectors | scheduler/worker integration with an external state system | descriptor contracts implemented; materializers pending |
| weight-transfer connectors | data-path integration | dedicated contract missing |
| scheduler/victim selector | scheduler-local policy | descriptor contract implemented; materializer pending |
| platform/operator/model runner | coordinated platform/runtime components | descriptor contracts implemented; materializers pending |
| control plane | external decision system | only action/receipt bridge contracts belong in vLLM |

“Contract identity exists” is not behavior compatibility. A legacy surface is
called migrated only after its component is materialized through the typed
contract and equivalent behavior, failure, and rollback tests pass.

## 9. Non-breaking migration sequence

1. Land descriptor, schema, admission, and empty-snapshot behavior with legacy
   entry points unchanged.
2. Add read-only diagnostics for admitted and disabled bundle IDs.
3. Implement one domain materializer at a time, starting with API-plane or
   descriptor-only components rather than hardware hot paths.
4. Dual-run behavior tests comparing legacy and typed paths; never enable both
   implementations for the same component in production.
5. Mark the typed path experimental in the ecosystem registry.
6. Publish exact core/platform/component compatibility and rollback records.
7. Change a component's recommended path only after behavior and failure tests
   pass.
8. Deprecate a legacy group only through a release notice, successor mapping,
   disablement test, and rollback window. No organization-wide removal date is
   currently approved.

## 10. Acceptance gates

The current static-admission phase is accepted only when all of these hold:

- default configuration performs no manifest scan and imports no implementation;
- explicit manifests are parsed before legacy entry-point imports;
- schema and runtime enums agree;
- incompatible API ranges, duplicate paths/IDs, unknown allowlist IDs, unknown
  permissions, denied permissions, and unsupported isolation fail closed;
- scheduler and worker components remain independently selectable;
- snapshot order is deterministic and snapshot data is immutable;
- legacy entry-point tests remain unchanged and passing;
- schema is included in wheel and sdist package data;
- documentation does not claim runtime behavior from manifest validation alone.

Later phases require separate gates for configuration schema, artifact digest
and path integrity, dependency ordering, domain materialization, health,
shutdown, recovery, and real hardware behavior. None is implied by completion
of static admission.

## 11. Validation and rollback

CPU validation targets:

```text
tests/plugins_tests/test_extension_contracts.py
tests/plugins_tests/test_extension_manifest.py
tests/plugins_tests/test_extension_startup.py
tests/test_envs.py
```

Rollback is immediate: unset `VLLM_EXTENSION_MANIFESTS` and keep the existing
`VLLM_PLUGINS` configuration. Because v1 does not materialize implementations
yet, this removes only typed admission and snapshot construction. A future
domain materializer MUST define its own disablement and rollback behavior before
graduating beyond experimental status.
