# Platform, operator, and model-runner boundaries

Status: **normative design gate**

Scope: `vllm.platform.v1`, `vllm.operator.v1`,
`vllm.model_runner.v1`, legacy platform/general plugins, and platform-specific
worker construction.

## 1. Decision

Platform, operator, and model-runner descriptors may be admitted and exposed in
read-only startup diagnostics, but they MUST remain descriptor-only until the
domain-specific gates in this document pass. A generic
`implementation_ref -> import -> construct` materializer is incorrect for all
three domains.

This is not a reason to classify the corresponding systems as “plugins.” A
platform profile is a coordinated hardware/runtime distribution. An operator
component is an implementation registered into an existing dispatch or graph
system. A model runner is a platform-bound worker implementation. A Bundle is
only one possible delivery mechanism for their in-process components.

Mooncake, LMCache, PegaFlow, and LMCache-Ascend remain external KV state systems
or providers with connector bridges. They are not platform, operator, or model
runner components merely because their connectors eventually invoke device
code.

## 2. Evidence from the current core

The existing platform entry-point value is a **probe factory**, not a platform
class. `vllm/platforms/__init__.py::resolve_current_platform_cls_qualname`
combines built-in and out-of-tree factories, calls each to determine whether it
is active, rejects multiple active providers, and calls the selected factory
again to obtain the class reference. `current_platform` is lazy because an
out-of-tree platform must be able to import the base `Platform` type before
selection completes.

General plugins have different semantics. `vllm/plugins/__init__.py` executes
their callables for import-time registration in API, engine-core, and worker
processes. `tests/plugins_tests/test_platform_plugins.py` demonstrates both
surfaces: one entry point detects a platform, while a general plugin replaces a
model-executor layer class as a custom operation. These effects are not
interchangeable and cannot share one materializer lifecycle.

Model runners are constructed inside platform-specific workers, not at generic
plugin startup:

- `vllm/v1/worker/gpu_worker.py` selects the v1 or v2 GPU runner;
- `vllm/v1/worker/cpu_worker.py` constructs the CPU runner;
- `vllm/v1/worker/xpu_worker.py` selects the XPU runner;
- scheduler, executor, KV connector, LoRA, speculative decoding, graph capture,
  and output transport code all depend on runner behavior and output shape.

Model implementation registration is another separate surface.
`vllm/model_executor/models/registry.py` invokes general plugins before
resolving registered model classes. A model registry entry is not a model
runner replacement.

## 3. Platform-profile gate

A future typed platform materializer MUST define two separate contracts:

1. a side-effect-free probe that returns inactive, active with a stable
   platform identity, or an attributable failure; and
2. a selected platform profile that names the platform class plus the worker,
   executor, communication, native-artifact, and runtime-stack compatibility
   identities it coordinates.

Required rules:

- static Bundle admission imports no platform implementation;
- dynamic probing occurs only at the existing lazy platform boundary;
- exactly one built-in, legacy, or typed platform may be active;
- an explicitly admitted typed probe failure is terminal and cannot silently
  fall through to a different platform;
- every API, engine-core, and worker process records the same selected profile
  identity and compatibility digest before device initialization;
- the profile validates driver/runtime, framework, native extension, collective
  library, and worker/executor compatibility before claiming activation;
- removing the typed manifest on a fresh start restores the unchanged built-in
  and legacy probe order.

The current `vllm.platform.v1` identity does not yet encode this probe/profile
split. Materializing it as a class reference would bypass current detection
semantics and is therefore blocked.

## 4. Operator gate

`vllm.operator.v1` currently collapses several incompatible shapes:

- Python class or method replacement;
- `torch.library` / custom-op registration;
- vLLM IR operation registration;
- compiled native extension loading;
- device-kernel selection and fallback.

Before materialization, the contract MUST be split into explicit registration,
dispatch, and native-artifact roles. Each role must declare:

- owning process and import phase;
- namespace and operation identities;
- supported devices, dtypes, layouts, shapes, graph modes, and quantization;
- collision policy and deterministic registration order;
- reference/fallback behavior and failure semantics;
- native ABI plus framework/runtime compatibility;
- accuracy and performance evidence scoped to the declared capability matrix.

Import-time monkey-patching through `vllm.general_plugins` remains a legacy
compatibility surface. Bundle admission alone does not make such mutation safe,
reversible, isolated, or composable.

## 5. Model-runner gate

A model runner MUST be selected only after platform profile, worker type, runner
generation, model task, and distributed topology are known. The materializer
belongs to the worker/platform construction boundary, not API startup.

A future contract must include:

- the supported platform profile and worker class identities;
- v1/v2 runner generation and constructor contract;
- supported generation, pooling, multimodal, encoder-decoder, and speculative
  execution modes;
- `SchedulerOutput` input and `ModelRunnerOutput` / async-output compatibility;
- KV connector, compilation/graph, LoRA, EPLB, sleep-mode, weight-update, and
  distributed-executor capabilities;
- initialization, warmup, execute, drain, failure, and shutdown behavior;
- next-start rollback to the exact platform-owned default runner.

One global “custom runner class” selector would create ambiguous ownership with
GPU, CPU, XPU, and future platform workers and is prohibited.

## 6. Blocking acceptance gates

The three descriptor identities remain experimental and non-materialized until:

- probe/profile, operator-role, and runner-factory schemas are versioned and
  reject unknown fields;
- legacy and typed selection are mutually deterministic and have exact
  next-start rollback tests;
- API, engine-core, and worker process identity consistency is tested;
- duplicate, collision, missing artifact, ABI mismatch, probe failure,
  constructor failure, and partial-worker-start failures are matched;
- built-in CUDA, CPU, and one out-of-tree platform pass behavior-equivalence
  tests without changing default startup;
- operator accuracy/fallback and runner request/output equivalence are tested on
  their declared hardware matrices;
- the exact core, platform distribution, runtime stack, and external component
  revisions appear in a release record.

Until then, documentation and the website MUST say “descriptor-only” or
“materializer pending,” and no repository, platform distribution, or operator
package may be promoted solely because its manifest is admitted.
