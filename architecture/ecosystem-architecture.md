# vLLM-HUST Ecosystem Architecture

Status: **normative draft**  
Scope: vLLM-HUST organization, integrations, and public catalog  
Supersedes: repository-level use of “plugin” as a universal system category

## 1. Governing principle

vLLM-HUST uses the following rule across code, documentation, repository
metadata, release notes, and the website:

> A plugin is a delivery and governance mechanism, not a system role. A
> connector is an integration contract, not the external system itself. A
> control plane is an external decision system, not an in-process vLLM plugin.

Every catalog entry MUST classify what the artifact does independently from
how it is installed.

## 2. Classification axes

Every supported or incubating component MUST declare these axes:

| Axis | Meaning | Examples |
|---|---|---|
| `artifact_type` | The kind of deliverable | runtime core, platform profile, runtime component, external system, bridge, tool |
| `system_role` | The responsibility in the serving system | scheduler policy, KV state manager, store, transport, control plane, benchmark |
| `integration_contracts` | Typed contracts used to integrate | KV connector, platform interface, operator ABI, action/receipt bridge |
| `execution_planes` | Where behavior executes | API, scheduler, worker, native, device, external service, cluster control |
| `deployment_topology` | Process and service topology | built-in, in-process, sidecar, daemon, distributed service, separate application |
| `delivery_model` | Installation and upgrade mechanism | core release, platform distribution, plugin bundle, package, container, external service |
| `ownership` | Maintenance responsibility | HUST-owned, upstream-owned, jointly maintained, certified third-party |
| `maturity` | Evidence-backed lifecycle state | concept, incubating, experimental, supported, verified, deprecated, archived |

A repository MAY contain multiple components. A component MUST NOT be assigned
only a repository-wide `plugin` label when its runtime and service artifacts
have different roles or execution planes.

## 3. System layers

### 3.1 Runtime core

`vllm-hust` owns the inference engine, scheduler, model runner, KV manager,
stable typed extension contracts, event schemas, action/receipt schemas, and
built-in default implementations.

The core MUST NOT absorb an external system's private configuration or service
protocol into a general-purpose extension API. Its default behavior MUST remain
usable without optional bundles or external services.

### 3.2 Platform profiles

`vllm-ascend-hust` and `vllm-metal-hust` are platform integration profiles,
not ordinary single-component plugins. A profile may provide platform
discovery, model runners, operators, loaders, native libraries, and device
capability negotiation.

Platform profiles MUST publish an explicit compatibility matrix with the core
runtime and hardware software stack.

### 3.3 Runtime mechanism components

BidKV, DiffSpec, LatchMoE, and KV compression are runtime mechanism components.
Their typed contracts belong to the runtime core; a plugin bundle or platform
distribution may deliver their implementations.

Hot-path implementations MUST execute directly through the appropriate typed
contract after initialization. They MUST NOT route token-by-token or
scheduler-step calls through a generic plugin sidecar.

### 3.4 KV state infrastructure

KV infrastructure is decomposed into five independent roles:

1. state manager and placement policy;
2. store and durability tier;
3. transfer substrate;
4. metadata or management control plane;
5. vLLM scheduler/worker connector adapter.

Mooncake, LMCache, and PegaFlow are systems that may contain several of these
roles. Their vLLM connectors are adapters and do not define the systems in
their entirety.

- Mooncake Transfer Engine is a transport substrate.
- Mooncake Store is an external distributed KV store.
- `MooncakeConnector` is a P/D transfer adapter.
- `MooncakeStoreConnector` is a shared-store adapter.
- LMCache is a multi-tier KV state manager whose remote backends may include
  Mooncake.
- LMCache Controller is a KV management control plane.
- `LMCacheConnectorV1` and `LMCacheMPConnector` are vLLM integration adapters.
- `LMCache-Ascend` is a platform-specific provider and integration
  distribution, not a separate general-purpose KV system.
- PegaFlow is a HUST-owned external KV state system containing services,
  transport, storage, metadata, and vLLM connectors.
- NIXL is a transfer substrate.
- `MultiConnector` is a core composition mechanism.
- BidKV is a scheduler policy, not a store or transport connector.

### 3.5 External control planes

An external control plane owns cross-request, cross-instance, or cross-cluster
decisions such as admission, placement, routing, capacity, workflow policy, and
global KV actions.

The runtime integrates through a narrow bridge with versioned actions, epochs
or generations, idempotency, expiry, rejection reasons, and receipts. The
external control plane itself MUST NOT be loaded as a vLLM runtime plugin.

### 3.6 Delivery and governance

A plugin bundle owns identity, version, artifacts, component descriptors,
configuration, declared permissions, enablement, diagnostics, and optional
sidecar lifecycle. It materializes a validated component into a domain
contract; it does not redefine that contract.

The unified extension design is split into:

1. **Extension Bundle Specification** for delivery and governance;
2. **Domain Contracts** owned by `vllm-hust`;
3. **Ecosystem Registry** for public classification, ownership, compatibility,
   maturity, and evidence.

## 4. Dependency direction

```text
external control plane -> bridge -> versioned runtime action contract
platform profile       -> platform/operator contracts -> runtime core
runtime component      -> typed domain contract        -> runtime core
runtime core           -> KV connector adapter         -> KV state system
plugin bundle          -> materializes component       -> typed domain contract
benchmark/evidence     -> verifies runtime, platform, and integration behavior
website                -> consumes the ecosystem registry and evidence
```

Dependencies in the opposite direction require an architecture decision
record. In particular, the runtime core MUST NOT import website metadata,
benchmark publication state, or external control-plane implementation code.

## 5. Canonical ownership

| Concern | Canonical home |
|---|---|
| Runtime contracts and built-in implementations | `vllm-hust` |
| Platform behavior | platform profile repository |
| Organization architecture and governance | `vllm-hust-docs` |
| Ecosystem classification registry | `vllm-hust-docs/registry` |
| Benchmark specifications and evidence | `vllm-hust-benchmark` |
| Public rendering of catalog and evidence | `vllm-hust-website` |
| Technique implementation and reproduction | owning research repository |

The website MUST display canonical registry fields and MUST NOT independently
declare an artifact to be a runtime plugin or supported integration.

## 6. Evidence levels

Support statements use distinct levels:

- `descriptor_only`: metadata validates, no runtime behavior asserted;
- `cpu_smoke`: control and import paths run without target hardware;
- `integration_tested`: contract behavior is tested across real processes;
- `hardware_verified`: correctness is verified on the declared hardware stack;
- `performance_verified`: a reproducible workload and provenance record support
  the performance statement;
- `production_observed`: operational evidence exists, with scope and date.

Lower evidence levels MUST NOT be presented as higher ones.

## 7. Compatibility and migration

Legacy Python entry points remain an explicit compatibility profile during
migration. They are not automatically conformant with the new bundle
specification. Migration changes the delivery mechanism only after typed
behavior tests exist for the component.

The removal of a legacy path requires a release notice, tested rollback, and a
catalog update. Platform profiles and hardware hot paths are migrated after
control-plane and descriptor-only components.
