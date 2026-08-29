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

The configured startup path grants no non-empty permission by default. Operators
may supply the strict `VLLM_EXTENSION_ALLOWED_PERMISSIONS` allowlist; blank,
duplicate, aliased, or unknown values fail startup, and every admitted component
request must be a subset of that allowlist. This is admission policy only:
`trusted_in_process` still has the ambient authority of the host process, so its
permission declaration is auditable intent rather than OS enforcement.

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

The first domain materializer is now the scheduler-local victim selector. It
imports exactly one admitted `vllm.scheduler.policy.v1` component in the
`scheduler` plane. This does not add generic lifecycle states: construction and
protocol validation belong to the scheduler domain, while an empty typed
provider set continues to the legacy compatibility path.

## 7. Process and frontend/backend boundary

API, scheduler, worker, native, device, and bridge are execution planes, not
frontend page categories. A component is materialized only in a process that:

1. owns the declared domain contract;
2. matches the declared execution plane;
3. supports the declared isolation and permissions;
4. has an explicit domain composition policy.

A KV integration names scheduler, worker, and API-plane telemetry components
in one bundle. They may share one implementation only when its descriptor is
admitted for all three contracts and planes; split-role bundles prevent the
API/logger process from importing worker/device code merely to decode stats.
An external control plane exposes no in-engine plugin object; a local bridge
may implement `vllm.control.action.v1` and
`vllm.control.receipt.v1`.

## 8. Legacy compatibility profile

`VLLM_PLUGINS` and the existing Python entry-point groups remain unchanged
during migration. They are separate from `VLLM_EXTENSION_MANIFESTS` and
`VLLM_EXTENSION_BUNDLES`.

| Existing surface | Migration classification | Bundle v1 status |
|---|---|---|
| `vllm.general_plugins` | legacy import-time mutation compatibility | retained; not bundle-conformant |
| `vllm.platform_plugins` | platform probe plus coordinated profile materialization | descriptor identity exists; materializer blocked on the [platform/operator/model-runner design gate](../architecture/platform-operator-model-runner-boundaries.md) |
| `vllm.io_processor_plugins` | API-plane IO processor | explicit qualified typed materializer implemented; unqualified legacy names retained |
| `vllm.stat_logger_plugins` | telemetry/stat logger | typed API-plane fan-out implemented; distinct legacy providers retained and dual-published classes deduplicated |
| model registry / out-of-tree model | model descriptor plus implementation registration | dedicated contract missing |
| reasoning and tool parsers | explicit API-plane parser selection | dedicated contract missing |
| LoRA resolvers | artifact/model resolution | dedicated contract missing |
| KV connectors | scheduler/worker integration with an external state system | scheduler, worker, and API-plane telemetry contracts; closed ordered selection topology; HMA, piecewise, and cache-layout declarations; `KVTransferConfig` mapping; and fail-closed typed `single`/`ordered_multi` factory materialization implemented; the four built-in Mooncake/LMCache names pass class, role, telemetry-codec, next-start rollback-name, and missing-optional-dependency equivalence, while matched real-system behavior, failure, shutdown, accelerator, and performance equivalence remain blocked on the [KV domain design gate](../architecture/kv-systems-and-connector-materialization.md) |
| weight-transfer connectors | data-path integration | dedicated contract missing |
| scheduler/victim selector | scheduler-local policy | typed materializer, exact legacy selection, and installed dual-path contract replay implemented; experimental while broader release gates remain open |
| platform/operator/model runner | coordinated platform/runtime components | descriptor identities implemented; materializers blocked on the [domain design gate](../architecture/platform-operator-model-runner-boundaries.md) |
| control plane | external decision system | external system stays outside vLLM; bridge materialization blocked on the [control-plane design gate](../architecture/control-plane-and-runtime-bridge.md) |

“Contract identity exists” is not behavior compatibility. A legacy surface is
called migrated only after its component is materialized through the typed
contract and equivalent behavior, failure, and rollback tests pass.

### 8.1 Scheduler-policy materialization profile

The scheduler materializer applies this exclusive-provider policy:

- zero admitted typed providers: use the existing
  `vllm.victim_selector` entry-point path;
- one admitted typed provider: import its `module:attribute` reference only
  after admission and construct it through `from_vllm_config`;
- multiple providers: fail startup unless `additional_config` contains the
  fully qualified `victim_selector_component` value
  `<bundle_id>/<component_id>`;
- a selected ID that is not admitted, an invalid import, a factory failure, or
  an object that does not satisfy `VictimSelector`: fail closed without trying
  another typed or legacy provider;
- `victim_selector_plugin_disabled=true`: retain the existing emergency path
  to `NoOpVictimSelector`.

Typed selection and legacy discovery MUST NOT both instantiate a victim
selector in one scheduler process. BidKV now publishes a conforming experimental
manifest, but its existing entry point remains the recommended path until the
equivalence and rollback gates below pass.

### 8.2 API-plane materialization profiles

IO processors remain an exclusive model/API choice. An unqualified
`io_processor_plugin` value keeps the existing `vllm.io_processor_plugins`
entry-point behavior. A fully qualified `<bundle_id>/<component_id>` value
instead selects exactly one admitted `vllm.io_processor.v1` component on the
API execution plane. The host imports its `module:attribute` only after
admission, requires an `IOProcessor` subclass, and constructs it through the
existing `(vllm_config, renderer)` boundary. Missing selection, import, type,
or constructor failures are terminal and never fall back to a legacy provider.

Stat loggers have fan-out semantics rather than exclusive selection. Every
admitted `vllm.stat_logger.v1` API-plane component is imported and required to
resolve to a `StatLoggerBase` subclass. Distinct legacy entry-point loggers
continue to run alongside typed providers. When one distribution publishes the
same logger class through both mechanisms during migration, the host
deduplicates that class to prevent double metrics and logs. Any admitted typed
provider that fails import or type validation fails the domain closed instead
of being silently omitted.

Both profiles roll back on the next fresh process start by removing their
Bundle manifest from `VLLM_EXTENSION_MANIFESTS` and restoring the existing
unqualified legacy entry-point configuration. Neither profile changes worker,
device, platform-detection, or native hot paths.

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

Implementation status: steps 1 and 2 are complete. Step 3 is active. The
scheduler/victim-selector materializer is implemented, and the KV domain now
has a closed three-role selection-topology parser/resolver, cache-layout
compatibility checks, mutually exclusive `KVTransferConfig` mapping, and a
typed `single` and `ordered_multi` factory adapters. Configuration-time checks
read declarations without implementation imports; scheduler, worker, and
API/logger processes import only their selected role and verify declarations
locally. Ordered child configuration and telemetry use logical connector IDs,
not class names or legacy registry lookup. The built-in Mooncake direct/store
and LMCache v1/multiprocess paths now have factory-level legacy/typed tests for
exact class and role resolution, telemetry codec shape, rollback configuration,
and equivalent optional-dependency failure. This completes a bounded part of
step 4, not the matched service, lifecycle, failure-recovery, accelerator, or
performance runs. Steps 4 through 8 otherwise remain required;
implementing a
materializer does not by itself make the typed path recommended or deprecate
its legacy surface.

## 10. Acceptance gates

The current static-admission phase is accepted only when all of these hold:

- default configuration performs no manifest scan and imports no implementation;
- explicit manifests are parsed before legacy entry-point imports;
- schema and runtime enums agree;
- incompatible API ranges, duplicate paths/IDs, unknown allowlist IDs, unknown
  permissions, denied permissions, and unsupported isolation fail closed;
- scheduler and worker components remain independently selectable;
- API-plane telemetry is selected independently and cannot resolve to a
  worker-only component;
- ordered KV connectors with conflicting non-null cache-layout declarations
  fail before implementation import;
- snapshot order is deterministic and snapshot data is immutable;
- legacy entry-point tests remain unchanged and passing;
- schema is included in wheel and sdist package data;
- documentation does not claim runtime behavior from manifest validation alone.

Later phases require separate gates for configuration schema, artifact digest
and path integrity, dependency ordering, domain materialization, health,
shutdown, recovery, and real hardware behavior. None is implied by completion
of static admission.

The experimental scheduler-policy materializer additionally requires:

- zero typed providers preserves the legacy entry-point behavior;
- an explicit `victim_selector_plugin` must select exactly one legacy entry
  point, while omitting it preserves historical auto-discovery during the
  compatibility window;
- discovery, load, factory, and protocol failures for an explicitly selected
  legacy provider fail closed instead of silently choosing another provider;
- one typed provider is imported only after the immutable snapshot exists;
- ambiguity requires an exact `<bundle_id>/<component_id>` selection;
- missing selection, import failure, factory failure, and protocol mismatch
  fail closed and never fall through to another implementation;
- the emergency disable flag returns the upstream-compatible no-op selector;
- BidKV legacy and typed paths produce equivalent victim choices, metrics, and
  failure behavior under the same scheduler traces before recommendation;
- a release record names the tested core and BidKV revisions and the exact
  rollback command/configuration.

Core `b819e5a3e2c2c4322e3aa72cd028f82fc25605b1` and BidKV
`703108492cf3f1681fd0b5b8ccb116cfc778f1e8` satisfy the software-equivalence
gate with the installed distribution metadata, the packaged Bundle manifest,
and a versioned four-step scheduler contract trace. Victim choices, exported
metrics, decision snapshots, invalid-configuration root causes, next-start
rollback, and emergency disable behavior match. This evidence does not claim a
real online serving run, accelerator behavior, or performance equivalence.

## 11. Validation and rollback

CPU validation targets:

```text
tests/plugins_tests/test_extension_contracts.py
tests/plugins_tests/test_extension_manifest.py
tests/plugins_tests/test_extension_startup.py
tests/test_envs.py
tests/v1/core/test_victim_selector_extensions.py
```

These extension gates are distinct from platform support gates. A failure in an
unchanged upstream kernel does not justify changing unrelated extension code or
silently relaxing that kernel's tolerance. It MUST remain visible in the exact
release record, MUST block any affected support claim, and MAY be classified as
baseline-equivalent only after an exact branch-versus-upstream audit and a
reproducible rerun. That classification does not turn a failed kernel gate into
a pass; it only prevents an unrelated baseline defect from being misreported as
an Extension Bundle regression.

For scheduler-policy rollback, unset `VLLM_EXTENSION_MANIFESTS` (and
`VLLM_EXTENSION_BUNDLES`), keep the existing BidKV package and
`vllm.victim_selector` entry point installed, and retain
`additional_config.victim_selector_plugin=bidkv`. The next process start then
has no typed provider and resolves that exact legacy entry point. Omitting the
name retains historical auto-discovery only for compatibility and is not the
recommended deterministic deployment form. For an emergency rollback to
upstream-compatible selection, set
`additional_config.victim_selector_plugin_disabled=true`; this bypasses both
typed and legacy victim-selector providers and constructs `NoOpVictimSelector`.
Other future domain materializers MUST define their own disablement and rollback
behavior before graduating beyond experimental status.
