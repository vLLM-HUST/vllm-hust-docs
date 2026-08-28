# External Control Plane and Runtime Bridge

Status: **normative design gate**

Scope: external decision systems, local runtime bridges, and
`vllm.control.action.v1` / `vllm.control.receipt.v1`

## 1. Decision

The control path has three separately governed components: the external control
plane, a remote runtime sidecar, and the core-delivered local control host.

- The control plane owns cross-request, cross-instance, or cross-cluster
  admission, placement, routing, capacity, workflow, and global KV decisions.
- The remote sidecar owns remote peer identity, TLS/mTLS termination, reconnect,
  delivery policy, and forwarding. It is currently a concept with no canonical
  repository or implementation evidence.
- The local host is a narrowly scoped, default-off core adapter that
  authenticates and validates same-host actions, applies only runtime-owned
  operations, and emits receipts. It is implemented in `vllm-hust` and has
  integration-test evidence.
- The vLLM process does not import the external control-plane application as a
  plugin implementation.
- A bundle may eventually deliver the bridge, but it does not deliver or own
  the external control plane.

The canonical registry therefore gives the external control plane no vLLM
integration contract. It records the unimplemented remote sidecar and the local
core host independently; they share action/receipt contracts but not topology,
delivery, ownership, maturity, repository, or evidence.

## 2. Current implementation status

`vllm/plugins/contracts.py` defines versioned action and receipt identities and
the `bridge` execution plane. The core now also packages closed Draft 2020-12
action and receipt schemas plus side-effect-free parsing/admission code under
`vllm/control_bridge/`. The first action vocabulary contains only
`runtime.health_probe` with `runtime.read` scope. It validates target runtime,
epoch, trusted-issuer policy input, granted scope, expiry, state precondition,
and idempotency-ledger input without executing or mutating anything.

The core now also provides two local security foundations. First, it verifies
an issuer-selected HMAC-SHA256 signature over the exact bounded UTF-8 JSON wire
bytes before strict contract parsing; duplicate JSON fields, unknown issuers,
short keys, malformed signatures, and payload tampering fail closed. Second, a
mode-`0600` SQLite ledger atomically binds each idempotency key, action ID, and
semantic action fingerprint. It distinguishes first reservation, in-progress
duplicate, terminal duplicate, and conflict; persists the validated action and
one immutable terminal receipt; and restores both after process restart.
Receipt completion must correlate with the reserved action's runtime, trace,
and causation identities. An `accepted` admission receipt cannot close the
terminal record.

Versioned authentication uses the canonical header
`v1;kid=<key-id>;sha256=<digest>`. Immutable issuer-scoped key sets declare a
monotonic generation, activation time, optional expiry, and optional revocation
time. A reloadable host store swaps complete generations atomically and rejects
generation rollback. Rotation overlap accepts both exact key IDs; an unknown,
inactive, expired, or revoked key never falls back to another key. Because the
signature header is outside the signed action bytes, a previously completed
action can be re-signed with the new active key and recover its durable receipt
without re-execution. The old `sha256=<digest>` form remains available only
when the caller explicitly supplies the legacy issuer-to-secret mapping; a
versioned key set rejects that form as a downgrade.

A fixed core-owned reference executor now establishes the first real process
boundary. Its materializer accepts only a component that declares exactly the
action/receipt v1 contracts, the `bridge` plane, `process_isolated`, the single
`ipc` permission, and the core health-probe worker reference. It never imports
or executes a bundle-supplied implementation. The worker uses `spawn`, an
explicit ready handshake, one non-blocking request slot, bounded request and
shutdown timeouts, fail/terminate behavior, drain/stop states, and explicit
restart. Runtime, epoch, state precondition, and receipt correlation are
rechecked at the boundary.

The host now exposes a narrow health observation adapter over the same
`EngineClient.check_health()` operation used by the canonical `/health` route.
It distinguishes healthy, `EngineDeadError`, and unavailable checks without
copying exception details into the bridge. The isolated worker receives only a
closed observation containing state, timestamp, and the fixed
`engine_client.check_health` source. Observations from the future or older than
five seconds fail before IPC and are checked again in the child. With no valid
observation, a probe remains terminal `failed` /
`RUNTIME_HEALTH_UNAVAILABLE`; IPC liveness is never reported as runtime health.

A transport-agnostic local service now composes authentication, admission,
durable lookup/reservation, and the executor. Authenticated durable bindings
are resolved before new deadline admission, so a terminal retry after its
original expiry returns the prior receipt. New requests still pass admission
before atomic reservation. In-progress duplicates, semantic conflicts,
executor failures, and terminal recovery have separate fail-closed receipts;
unauthenticated bytes produce no trusted receipt.

A Linux-only local transport now exposes that service through a Unix-domain
socket. The host requires `SO_PEERCRED` and the same effective UID, creates the
socket with mode `0600`, and accepts a socket parent only when it already exists,
is owned by the host UID, and is not group- or world-writable. It never removes
an existing path and removes its own socket only when the device/inode identity
still matches the path it created. The closed binary frame preserves the exact
bounded action bytes used by HMAC verification; request signature, action, and
response sizes are independently bounded.

Ingress handlers may run concurrently, but an explicit `max_in_flight` counter
and one serialized authority lane bound all authentication, ledger, admission,
and execution work. Read, health-observation, service, and shutdown waits are
bounded. A service timeout returns only the generic `ACTION_PENDING` transport
state; it does not cancel the authoritative operation or release its ingress
slot until the durable operation actually finishes, preventing an implicit
unbounded executor queue. Peer, framing, authentication, parsing, pending, busy,
and internal failures expose stable generic transport codes without exception
details. SQLite access is serialized across the transport and lifecycle threads.

This is same-host message authentication, not a remote control-plane transport:
it provides neither TLS/mTLS nor production secret provisioning, distribution,
storage, or audit. It is also not an OS sandbox.

The OpenAI-compatible server now has one explicit opt-in lifecycle path through
`--control-bridge-config`. Absence of that option preserves the prior startup
behavior and allocates no bridge resources. The referenced, closed v1 JSON
configuration supplies runtime/epoch/state identity, absolute socket and replay
paths, the exact `runtime.read` grant, a versioned key set, and bounded limits.
Secrets are not embedded in the JSON or CLI: each key references a separate,
host-owned regular file with no group/world access and canonical base64 content.
Configuration and key symlinks, relative paths, unknown fields/scopes, excessive
limits, and multi-API-process startup fail closed.

When configured, FastAPI lifespan owns a core-fixed descriptor, process
executor, replay ledger, orchestration service, health adapter, and socket host.
Startup failure closes every resource already acquired; normal shutdown drains
the socket before closing the worker and ledger. This path still cannot load
bundle-supplied bridge code.

The generic Bundle v1 startup path still:

- grants no non-empty permission requests;
- admits only `trusted_in_process` isolation;
- does not automatically materialize or start the fixed bridge;
- has no production remote transport, TLS/mTLS identity, secret backend, or key
  distribution/audit integration;
- has no general or mutating runtime operation API or external transport.

Consequently the external RIDE-to-runtime bridge remains non-runnable end to
end. The fixed child and same-UID socket host form a tested local
message-authenticated foundation, but the overall system MUST NOT be described
as remotely authenticated, sandboxed, supported, or a complete secure bridge.

## 3. Required action contract

The runtime-owned v1 envelope now defines and tests:

- contract version and action type;
- unique action ID and idempotency key;
- target runtime/engine identity;
- target epoch or generation;
- issue time and expiry/deadline;
- authenticated issuer and authorization scope;
- typed payload with a closed schema;
- expected prior state or compare-and-set precondition;
- trace and causality identifiers.

Unknown action types, fields, versions, targets, expired actions, stale epochs,
failed policy authorization, precondition failures, duplicates, and
idempotency conflicts are rejected by a pure function with
`mutation_occurred=false`. Mutating action payloads remain undefined and are
therefore rejected.

## 4. Required receipt contract

Every accepted or rejected action MUST return a receipt containing:

- action ID, runtime identity, and observed epoch/generation;
- accepted, applied, rejected, expired, duplicate, or failed status;
- stable reason/error code and safe diagnostic text;
- whether any mutation occurred;
- resulting state/version when applicable;
- completion time and trace identifiers.

A network acknowledgement is not an applied receipt. Retrying the same
idempotent action must return the previous terminal result or an explicitly
defined in-progress result, not apply the mutation twice.

## 5. Isolation, permissions, and lifecycle

The first bridge executor MUST be process-isolated. Calling an ordinary child
process “sandboxed” is prohibited unless filesystem, network, subprocess,
device, IPC, and credential capabilities are actually enforced.

The fixed core worker satisfies the process-isolation requirement only for its
closed read-only code path. Exact manifest admission limits it to `ipc`, but an
ordinary spawned process is not proof of OS capability confinement. No
bundle-supplied bridge code is admitted in v1.

The bridge materializer owns initialize, authenticate, ready, degraded, drain,
failed, and shutdown behavior. The generic bundle loader continues to own only
configured, parsed, admitted/disabled/rejected, and snapshotted states.

Network egress, IPC, shared memory, filesystem, and credential access must be
declared and enforced by an explicit host policy. A `trusted_in_process`
component cannot provide a security boundary against a remote control plane.

## 6. Dependency direction

```text
external control plane
  -> remote-authenticated versioned action
  -> remote runtime sidecar
  -> same-UID authenticated local action
  -> core local host and process-isolated executor
  -> runtime-owned operation API
  -> versioned receipt
  -> external control plane
```

The runtime core must not depend on control-plane scheduling libraries, global
state stores, UI models, or workflow implementation code. The control plane
must not reach into scheduler or worker internals outside the versioned
operation API.

## 7. Blocking acceptance gates

Control-plane bridge materialization is blocked until all of these pass. The
schema, pure-admission, exact-byte authentication, and durable replay
foundations are complete; the remaining end-to-end gates are not:

- closed action and receipt schemas with compatibility tests — complete;
- exact-byte HMAC authentication and persistent replay/idempotency recovery
  primitives — complete;
- versioned key IDs, overlap, activation, expiry, revocation, atomic generation
  replacement, rollback prevention, and explicit legacy mode — complete;
- same-UID Unix-socket message authentication, exact bounded framing, bounded
  concurrent ingress, serialized authority, safe path ownership/cleanup, and
  timeout-to-pending recovery — complete;
- closed opt-in host configuration, protected separate key files, single-API
  guard, FastAPI lifecycle ownership, startup cleanup, shutdown cleanup, and
  default-disabled behavior — complete;
- production remote transport, TLS/mTLS peer identity, and production secret
  provisioning, distribution, storage, and audit integration;
- authorization, expiry, epoch, replay, and idempotency integration tests
  across the real transport and executor;
- fixed core-only process executor, IPC-only manifest policy, bounded slot,
  lifecycle, authoritative health observation, freshness checks, and
  fail-closed missing-health result — complete;
- OS-enforced capability confinement for any future non-core bridge code;
- atomic rejection and no-partial-mutation tests;
- local restart/retry, duplicate-delivery, bounded backpressure, drain, and
  shutdown behavior — complete for the same-host socket; remote reconnect and
  control-plane-absence behavior remain open;
- default runtime behavior remains usable with no bridge configured — complete;
- rollback removes bridge configuration without uninstalling the runtime —
  complete for the local host;
- exact core, bridge, and control-plane revisions appear in the release record;
- the website continues to classify the external control plane and bridge as
  separate components and evidence levels.

Until these gates pass, RIDE is a concept-level external system and its runtime
bridge is a concept-level integration with tested wire-contract,
authentication, durable-replay, fixed process-executor, and bounded same-host
transport foundations, not a supported Bundle v1 plugin.
