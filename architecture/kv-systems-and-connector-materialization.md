# KV Systems and Connector Materialization

Status: **normative design gate**

Scope: Mooncake, LMCache, PegaFlow, LMCache-Ascend, and vLLM KV connector
materialization

## 1. Decision

A KV system, a vLLM connector bridge, and a bundle that delivers that bridge
are three different objects.

- Mooncake, LMCache, and PegaFlow are KV systems with service or subsystem
  lifecycles outside vLLM.
- `MooncakeConnector`, `MooncakeStoreConnector`, `LMCacheConnectorV1`,
  `LMCacheMPConnector`, and the PegaFlow scheduler/worker connector are bridge
  implementations inside vLLM processes.
- A Python distribution or Extension Bundle may deliver a connector, but the
  delivery unit is neither the external system nor the connector contract.

The ecosystem registry therefore publishes separate entries for each external
system and its vLLM connector bridge. A system entry has no vLLM connector
contract merely because the same repository also contains an adapter.

Canonical ownership follows implementation delivery, not the external system's
brand. The Mooncake system entry remains canonical to `kvcache-ai/Mooncake`, and
the LMCache system entry remains canonical to `LMCache/LMCache`. The HUST core
fork is canonical for the bridge entries it actually ships: Mooncake direct and
distributed-store connectors, plus the LMCache v1 facade and multiprocess
connector/fallback. Their registry entries retain upstream links to the systems
they integrate.

## 2. Runtime ownership that MUST remain intact

The runtime core owns the connector domain in
`vllm/distributed/kv_transfer/kv_connector/factory.py` and
`vllm/distributed/kv_transfer/kv_connector/v1/base.py`.

`KVConnectorFactory` currently owns behavior that a generic bundle loader MUST
NOT duplicate:

1. construct scheduler and worker roles separately;
2. preserve `KVTransferConfig` as the domain configuration boundary;
3. lazy-load built-in and external connector classes;
4. validate the external constructor signature;
5. enforce hybrid KV cache manager capability checks;
6. preserve `MultiConnector` composition and child capability checks.

Existing `kv_connector` and `kv_connector_module_path` configurations remain
the compatibility path. Static bundle admission MUST NOT mutate either field or
register an implementation as an import-time side effect.

## 3. Why scheduler-policy materialization cannot be copied

The victim selector is an exclusive scheduler-local policy. KV integration is
role-split and may be composed. Applying the victim-selector rule would create
several failures:

- one provider could be incorrectly instantiated in both scheduler and worker;
- two legitimate `MultiConnector` children could be rejected as ambiguous;
- a bundle could bypass HMA and constructor checks owned by the factory;
- the external Mooncake, LMCache, or PegaFlow service could be mistaken for an
  in-process plugin object;
- legacy module-path deployments could change behavior without an explicit
  migration choice.

No KV materializer may ship by reusing a generic “select one component and
import it” helper.

## 4. Required materialization profile

A future KV bundle profile MUST define, before implementation:

- a scheduler component implementing `vllm.kv_connector.scheduler.v1`;
- a worker component implementing `vllm.kv_connector.worker.v1`;
- an API-plane telemetry component implementing
  `vllm.kv_connector.telemetry.v1`, which owns the stats codec and logger-side
  class behavior without importing a worker implementation;
- whether both contracts are implemented by one class or separate classes;
- exact qualified component selection for each execution plane;
- worker declarations for HMA, piecewise CUDA Graph mode, and an optional
  required KV cache layout (`NHD` or `HND`);
- how `MultiConnector` expresses ordered child composition without relying on
  manifest discovery order;
- how the admitted implementation is passed into `KVConnectorFactory` without
  bypassing `KVTransferConfig`, HMA checks, or constructor validation;
- domain configuration schema ownership and secret handling;
- the external system endpoint/version handshake and fallback behavior;
- per-role initialization, ready, drain, failure, and shutdown semantics;
- rollback to the current built-in name or external module-path configuration.

The generic Bundle v1 manifest does not yet encode all of these domain choices.
Adding a free-form configuration object to the generic manifest is not an
acceptable shortcut; the KV domain must own and version its configuration.

### 4.1 Implemented typed KV materialization boundary

The core now contains a closed `kv-connector-selection-v1` schema and a
dependency-light parser/resolver in
`vllm/plugins/kv_connector_selection.py`. This boundary implements only the
domain decisions that are safe before implementation import:

- `single` requires exactly one logical connector;
- `ordered_multi` requires at least two connectors and preserves declared
  order rather than manifest discovery order;
- every logical connector names exact qualified scheduler, worker, and
  API-plane telemetry components;
- a component may implement both roles, or the roles may be separate;
- each role declares HMA support, while the worker also declares whether it
  requires piecewise CUDA Graph mode and an optional required cache layout, so
  configuration checks do not import a worker implementation in the wrong
  process;
- an ordered composition with conflicting non-null `NHD`/`HND` requirements is
  rejected before any implementation import;
- resolution rejects role crossing, missing admission, wrong execution plane,
  duplicate logical connectors, duplicate component pairs, and unknown fields;
- resolution reads the immutable startup snapshot and never imports a connector
  implementation.

This is a topology descriptor, not a runtime configuration shortcut. It does
not accept endpoint credentials or connector-specific free-form configuration.
`KVTransferConfig` now owns an optional `kv_connector_selection` field and
normalizes CLI dictionaries into the immutable profile; typed selection is
mutually exclusive with legacy connector names and module paths. Configuration
does not register anything with `KVConnectorFactory`. The factory now
materializes typed `single` and `ordered_multi` selections after the immutable
startup snapshot exists: scheduler, worker, and API/logger processes import
only their selected components. Ordered child configuration is keyed by logical
`connector_id` under `kv_connector_extra_config.typed_connectors`; its closed
host envelope has a packaged Draft 2020-12 schema, while each provider owns its
inner fields. External-system handshake, secret-source integration, lifecycle,
and rollback execution remain required.

Capability declarations are admission inputs, not trusted implementation
facts. The factory adapters verify `SupportsHMA`, piecewise-mode, and
cache-layout requirements against the imported role implementation inside its
owning process and fails closed on any declaration mismatch. Scheduler code may
import only the scheduler component, worker code only the worker component,
and API/logger code only the telemetry component. A combined class remains
valid only when its descriptor explicitly implements all three contracts and
is admitted in all three planes.

The existing `MultiConnector` compatibility path has also been hardened to
delegate KV-recovery requeue observations, worker first-compute observations,
and reclaimable block collection to every ordered child. Reclaimable block IDs
are unioned because a completed durable copy from any configured child makes
that device block reclaimable; asynchronous save completion continues to use
the existing all-child accounting. This fixes legacy lifecycle parity but does
not by itself materialize the typed topology.

The core release now packages two explicit bridge bundles. The Mooncake bundle
separates direct-transfer and distributed-store triples; the LMCache bundle
separates v1 and multiprocess triples. Each triple contains scheduler, worker,
and API telemetry components. Dedicated telemetry providers avoid importing the
connector worker modules in the API process, and the descriptors request the
filesystem, IPC, network, shared-memory, subprocess, and device permissions
used by their respective trusted in-process paths. These descriptors describe
core-delivered bridges only; they do not transfer ownership of Mooncake or
LMCache services into vLLM.

The four built-in bridge names now also have a factory-level materialization
equivalence gate. For `MooncakeConnector`, `MooncakeStoreConnector`,
`LMCacheConnectorV1`, and `LMCacheMPConnector`, the typed scheduler and worker
roles resolve to the same implementation class as the legacy name, the
next-start rollback name resolves back to that class, and each loadable typed
telemetry role produces the same stats type and payload as the legacy codec.
When the optional `lmcache` package is absent, the typed multiprocess path fails
closed while preserving the same `ModuleNotFoundError` root cause as the legacy
path. This is class, role, codec, rollback-configuration, and dependency-failure
equivalence only; it is not service, accelerator, lifecycle, or performance
equivalence.

The Mooncake disaggregated example no longer uses name-based `pkill` or kills
the caller's whole process group. Every prefiller, decoder, and proxy is started
in its own retained process group; cleanup sends `TERM` only to those groups,
waits for a bounded grace period, and escalates only those still alive. Static
safety tests and shell syntax validation cover this invariant. The example is
now the process-ownership basis for a topology-aware preflight/real-run gate,
but it still does not constitute a Mooncake real-system run.

The Mooncake gate supports `direct`, embedded/standalone store, and combined
topologies. It verifies the selected virtual environment, Mooncake Transfer
Engine minimum version, exact direct/store bundle roles, topology-specific JSON
invariants and service executables, model, accelerator inventory, ports, fresh
evidence directory, and core revision without launching a service. Host 112
preflights on 2026-08-29 passed the model, eight-NPU inventory, requested ports,
bundle, config, and revision checks. Direct correctly blocked because
`mooncake.engine` and `mooncake-transfer-engine>=0.3.8` were absent;
store-embedded additionally blocked because `mooncake_master` was unavailable.
These are environment-readiness records, not connector or performance results.

Mooncake direct mode now has a process-owned real-run harness for three
mutually exclusive next-start states: `legacy`, `typed`, and `rollback`. Every
state requires a successful preflight for the exact core revision, source tree,
model, runnable CLI, bundle roles, device set, free-memory threshold, and port
set; it writes to a new evidence directory and uses a deterministic request
workload. The runner repeats volatile GPU-memory and port checks immediately
before launch, fails as soon as a retained child exits, and cleans up only its
own prefiller, decoder, and proxy process groups.

The controlled A100 audit is deliberately recorded as blocked rather than as a
connector result. An isolated environment reached Mooncake 0.3.10, Torch 2.11,
the exact editable vLLM-HUST source, CUDA platform detection, and a runnable
vLLM CLI. Before matched runs could complete, an unrelated 32B service occupied
both GPUs and the selected proxy port. The attempted child groups were cleaned
without touching that service. At core revision
`b0ea14144941891022693bf0dfdc3b6fccad3dd5`, the strengthened preflight then
reported both A100s ineligible because each had less than the required 20,000
MiB free. This proves resource admission and cleanup behavior only; no
real-online, equivalence, hardware-performance, or Mooncake-failure claim is
made.

## 5. Migration order

1. Keep current named and module-path connector behavior unchanged.
2. Maintain separate system and connector entries in the canonical registry.
3. Publish repository profiles that list services/providers and connector
   bridges as separate artifacts.
4. Define a KV-specific selection and composition schema mapped to
   `KVTransferConfig`. The closed selection topology, admitted-component
   resolution, scheduler/worker/telemetry role declarations, cache-layout
   compatibility checks, and mutually exclusive `KVTransferConfig` mapping are
   implemented.
5. Add a factory-owned adapter that consumes admitted descriptors only after
   the immutable startup snapshot exists. Typed `single` and `ordered_multi`
   are implemented. Factory-level materialization equivalence for the four
   built-in Mooncake and LMCache names is verified; real-system equivalence
   remains pending.
6. Run matched real-system tests for built-in Mooncake and LMCache connectors,
   external PegaFlow module-path loading, LMCache-Ascend, and `MultiConnector`.
7. Run scheduler/worker process, HMA, failure, recovery, and shutdown tests.
8. Publish an exact core/connector/system/platform release record and rollback
   configuration before recommending the typed path.

PegaFlow now publishes a Bundle v1 manifest with separate scheduler, worker, and
API telemetry components. The package initializer is a lazy compatibility facade:
legacy `pegaflow.connector.PegaKVConnector` and the typed facade resolve to the
same class, while importing the telemetry component does not import Torch or the
worker facade. The benchmark runner can emit either the legacy module-path config
or the typed selection, and typed mode declares its bundle and the explicit
`device_access`, `ipc`, and `network_egress` host permission allowlist. This proves
configuration and import compatibility only.

The same runner has a safe real-run preflight and runbook. It labels preflight
separately from `real-online`, requires a fresh output directory, records exact
command/environment/model/hardware/revision inputs, and stops only process groups
it created. The 2026-08-29 host-112 typed preflight verified the manifest, model,
ports, and eight idle 910B2 devices, then correctly refused to launch because the
invoking user could not access a controlled runtime environment or built server
binary. This is readiness evidence, not connector equivalence or a negative
performance result.

LMCache-Ascend now publishes a wheel-carried Bundle v1 manifest for a separate
scheduler component, worker/device component, and lightweight API telemetry
provider. The adapter constructor accepts both its historical two-argument call
and the host's three-argument `kv_cache_config` contract. The telemetry package
does not import the heavy `lmcache_ascend` initializer, whose monkey patches and
device/runtime dependencies remain confined to connector materialization. The
bundle explicitly requests its broad trusted-process filesystem, IPC, network,
shared-memory, subprocess, and worker device permissions. These six static and
admission tests establish packaging and contract compatibility, not matched
LMCache behavior or Ascend hardware equivalence.

LMCache-Ascend also has a fail-closed `preflight-only` command and real-run
runbook. It preserves the selected virtual-environment interpreter, requires a
fresh evidence directory, and records exact imports and dependency versions,
bundle roles, model, ports, NPU inventory, and both Git revisions without
starting or terminating a service. The 2026-08-29 host-112 preflight passed the
model, two requested ports, eight-device inventory, split-role manifest, and
core/provider revision checks. It correctly blocked because `lmcache` 0.4.4,
`lmcache_ascend`, and `torch_npu` were unavailable in the isolated core
environment. That record is environment-readiness evidence only.

## 6. Blocking acceptance gates

The built-in materialization gate above is complete. It does not satisfy the
remaining real-run gates below.

KV bundle materialization is blocked until all of these are testable:

- zero typed KV providers is behavior-identical to current configuration;
- scheduler and worker providers cannot be accidentally crossed;
- a worker provider cannot be used as the API-plane telemetry codec;
- explicit ambiguity errors name the qualified candidates for that plane;
- `MultiConnector` order is explicit and deterministic;
- external module-path connectors remain supported during the migration
  window; PegaFlow and LMCache-Ascend have static and unit-test evidence for this
  gate, while matched real-run evidence remains pending;
- HMA capability checks run for typed and legacy paths identically;
- implementation import occurs after admission and in the owning process only;
- ordered children cannot require conflicting KV cache layouts;
- a connector failure never changes the lifecycle classification of the
  external KV system;
- rollback needs no package uninstall and is verified on the next process
  start;
- hardware and performance claims identify the external system, connector,
  platform, and exact revisions separately.
- each real-run harness passes environment, model, accelerator, port, workload,
  unique-output, command, and revision preflight; it never kills or silently
  reuses processes it did not start;
- legacy module-path, typed selection, and next-start rollback use matched
  topology and retain raw request, hit/miss, telemetry, failure, and shutdown
  evidence.

Until these gates pass, Mooncake, LMCache, PegaFlow, and LMCache-Ascend may be
first-class ecosystem integrations without being described as Bundle v1
materialized plugins.
