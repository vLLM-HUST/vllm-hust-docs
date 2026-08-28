# External Control Plane and Runtime Bridge

Status: **normative design gate**

Scope: external decision systems, local runtime bridges, and
`vllm.control.action.v1` / `vllm.control.receipt.v1`

## 1. Decision

An external control plane and its local runtime bridge are separate systems.

- The control plane owns cross-request, cross-instance, or cross-cluster
  admission, placement, routing, capacity, workflow, and global KV decisions.
- The bridge is a narrowly scoped local adapter that authenticates and
  validates actions, applies only runtime-owned operations, and emits receipts.
- The vLLM process does not import the external control-plane application as a
  plugin implementation.
- A bundle may eventually deliver the bridge, but it does not deliver or own
  the external control plane.

The canonical registry therefore gives the external control plane no vLLM
integration contract. The separate bridge component implements
`vllm.control.action.v1` and `vllm.control.receipt.v1` in the `bridge` execution
plane.

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

The configured startup path still:

- grants no non-empty permission requests;
- admits only `trusted_in_process` isolation;
- has no process-isolated bridge executor;
- has no authenticated transport or host key provisioning/rotation mechanism;
- has no runtime operation executor, health transport, drain, or shutdown path.

Consequently the bridge remains non-runnable end to end. The contract,
authentication primitive, and replay ledger MUST NOT be described as a
process-isolated, transport-authenticated, supported, or complete secure bridge.

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

The bridge materializer owns initialize, authenticate, ready, degraded, drain,
failed, and shutdown behavior. The generic bundle loader continues to own only
configured, parsed, admitted/disabled/rejected, and snapshotted states.

Network egress, IPC, shared memory, filesystem, and credential access must be
declared and enforced by an explicit host policy. A `trusted_in_process`
component cannot provide a security boundary against a remote control plane.

## 6. Dependency direction

```text
external control plane
  -> authenticated versioned action
  -> process-isolated local bridge
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
- transport authentication, key provisioning, rotation, and revocation;
- authorization, expiry, epoch, replay, and idempotency integration tests
  across the real transport and executor;
- process-isolated executor with enforced permission policy;
- atomic rejection and no-partial-mutation tests;
- restart, reconnect, duplicate-delivery, drain, and shutdown tests;
- bounded backpressure and failure behavior when the control plane is absent;
- default runtime behavior remains usable with no bridge configured;
- rollback removes bridge configuration without uninstalling the runtime;
- exact core, bridge, and control-plane revisions appear in the release record;
- the website continues to classify the external control plane and bridge as
  separate components and evidence levels.

Until these gates pass, RIDE is a concept-level external system and its runtime
bridge is a concept-level integration with tested wire-contract,
authentication-primitive, and durable-replay foundations, not a supported
Bundle v1 plugin.
