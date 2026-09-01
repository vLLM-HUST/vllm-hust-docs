# Legacy optimization extraction and extension migration

Status: working migration inventory  
Source repositories:

- [`intellistream/vllm-hust-legacy-20260831`](https://github.com/intellistream/vllm-hust-legacy-20260831)
- [`intellistream/vllm-ascend-hust-legacy-20260831`](https://github.com/intellistream/vllm-ascend-hust-legacy-20260831)

The source repositories are immutable archives. They preserve authorship,
review discussion, paired host changes, tests, and benchmark evidence. They are
not extension distributions and must not be used as the installation source.

## Migration rule

Do not copy every HUST-only commit into a package. Each historical change is
classified before extraction:

1. **Extension**: an independently installable behavior implementation with a
   stable host contract and explicit activation.
2. **Connector or provider**: an adapter to an external KV system, router,
   control plane, deployment system, or device runtime.
3. **Offline tool**: model conversion, calibration, profiling, or artifact
   generation outside the serving process.
4. **Host seam**: a narrow, neutral interface that remains in vLLM or
   vLLM-Ascend and is exercised by at least one external extension.
5. **Upstream patch**: a bug fix or generally useful hot-path optimization that
   should be proposed upstream rather than packaged.
6. **Research-only branch**: incomplete, reverted, unsafe, or unverified work.

An extracted repository must preserve the original author and PR links. A new
maintainer must not be inferred from organization membership. The original
team must confirm project attribution, code provenance, and ongoing ownership
before a stable release or website ownership label is added.

## First-wave extraction candidates

| Candidate | Historical owners and evidence | Correct target | Migration decision |
| --- | --- | --- | --- |
| Prefix-aware routing | `@Amber1qq`: [core PR #80](https://github.com/intellistream/vllm-hust-legacy-20260831/pull/80), [final PR #173](https://github.com/intellistream/vllm-hust-legacy-20260831/pull/173); reliability work by `@WMASTER123`; node-load work by `@Adr1anZheng` | control-plane router extension plus a small vLLM cache-event adapter | Extract the proxy/router, node registry, cache-state reconciliation, and routing policy. Keep only a neutral cache-event publication seam in the host. Do not run the global router as an in-process scheduler plugin. |
| KV tiering | `@JieYang2001`: [core PR #124](https://github.com/intellistream/vllm-hust-legacy-20260831/pull/124) | KV residency provider with CPU/filesystem tiers | Extract tier managers and lifecycle policy behind the vLLM KV offload/connector contract. The manager may render configuration and check tiers but must not delete retained KV data. Coordinate with [`intellistream/vllm-agent-state-tiering`](https://github.com/intellistream/vllm-agent-state-tiering) instead of creating a competing implementation. |
| KNorm KV compression | `@kotoriqaq0`: [initial PR #76](https://github.com/intellistream/vllm-hust-legacy-20260831/pull/76); `@SuccinctPaul`: [activation repair PR #214](https://github.com/intellistream/vllm-hust-legacy-20260831/pull/214) | KV-compression method extension | Extract scoring and selection as a method package. Reuse one host-owned transactional KV-compression lifecycle. Prefix caching and other KV mutation owners must be declared as conflicts until composition is proven. |
| PyramidKV on Ascend | `@Irisuko`: [core lifecycle PR #232](https://github.com/intellistream/vllm-hust-legacy-20260831/pull/232), [Ascend provider PR #225](https://github.com/intellistream/vllm-ascend-hust-legacy-20260831/pull/225) | Ascend KV-compression method/provider extension | High-value recovery candidate. Preserve the fail-closed matrix, prompt-admission guard, quality evidence, graph modes, and model restrictions. Do not silently merge it into an unrelated team's repository. |
| SliceGPT | `@qingfengyuhuoda`: [core/runtime PR #158](https://github.com/intellistream/vllm-hust-legacy-20260831/pull/158), [Ascend PR #150](https://github.com/intellistream/vllm-ascend-hust-legacy-20260831/pull/150) | offline SliceGPT toolkit plus a model-loader/runtime extension | Split conversion/calibration from serving-time model loading. The artifact format is versioned and validated before the runtime extension is enabled. |
| SimLLM | `@GuMorming`: Ascend [runtime PR #66](https://github.com/intellistream/vllm-ascend-hust-legacy-20260831/pull/66), [validation PR #70](https://github.com/intellistream/vllm-ascend-hust-legacy-20260831/pull/70), [performance PR #80](https://github.com/intellistream/vllm-ascend-hust-legacy-20260831/pull/80) | cache-reuse runtime extension | Extract only after scheduler accounting and paged-KV materialization have typed host hooks. The legacy scheduler rewrite and KV injection must not be reproduced as import-time patching. |
| Full-graph parallel / split-batch | `@ilnnfover` and `@Raing5Days`: [core PR #273](https://github.com/intellistream/vllm-hust-legacy-20260831/pull/273), Ascend split-batch [PRs #280-#283](https://github.com/intellistream/vllm-ascend-hust-legacy-20260831/pulls) | Ascend execution-strategy extension | The merged core admission/key strategy is a candidate host seam. Stream, event, capture, split planning, and replay policy belong in the external extension. The four open split-batch PRs remain research input, not release artifacts. |
| Pipeline microbatch scheduling | `@xsun2001`: [core PR #135](https://github.com/intellistream/vllm-hust-legacy-20260831/pull/135), [Ascend PR #136](https://github.com/intellistream/vllm-ascend-hust-legacy-20260831/pull/136) | scheduler/execution policy extension | Recover only after an owner-confirmed policy contract is defined. It must fail closed for unsupported PP topology and graph modes. |
| Unified communication / multi-NIC | `@machuanhu`: [core PR #42](https://github.com/intellistream/vllm-hust-legacy-20260831/pull/42), [multi-NIC PR #168](https://github.com/intellistream/vllm-hust-legacy-20260831/pull/168) | communication-backend provider | Keep the neutral communication selection seam in the host. Backend discovery, topology capability, environment requirements, and native libraries belong in a provider distribution. |
| Dynamic INT8/KIVI KV | `@hustcui`: [core PRs #118/#161](https://github.com/intellistream/vllm-hust-legacy-20260831/pulls?q=is%3Apr+author%3Ahustcui), Ascend [PR #62](https://github.com/intellistream/vllm-ascend-hust-legacy-20260831/pull/62) | quantized-KV runtime extension | Do not release from the legacy branches. Reconcile with the Adaptive Quantized KV project, freeze scale/layout/graph contracts, and obtain real accuracy and lifecycle evidence first. |

## Existing extraction carriers

The following work already has a separate carrier and should be migrated or
adapted instead of copied into a second repository:

| Historical area | Existing carrier |
| --- | --- |
| BidKV victim selection | [`vLLM-HUST/vllm-hust-bidkv`](https://github.com/vLLM-HUST/vllm-hust-bidkv) |
| Differential speculative decoding | [`vLLM-HUST/vllm-ascend-hust-diffspec`](https://github.com/vLLM-HUST/vllm-ascend-hust-diffspec) |
| LatchMoE | [`vLLM-HUST/vllm-ascend-hust-LatchMoE`](https://github.com/vLLM-HUST/vllm-ascend-hust-LatchMoE) |
| Adaptive quantized KV | [`vLLM-HUST/vllm-ascend-adaptive-quantized-kv-hust`](https://github.com/vLLM-HUST/vllm-ascend-adaptive-quantized-kv-hust) |
| Host-control batching | [`intellistream/vllm-host-control-batching`](https://github.com/intellistream/vllm-host-control-batching) |
| Prefix-routing reliability | [`intellistream/prefix-cache-routing-reliability`](https://github.com/intellistream/prefix-cache-routing-reliability) |
| Agent-state tiering | [`intellistream/vllm-agent-state-tiering`](https://github.com/intellistream/vllm-agent-state-tiering) |
| Request-lifecycle profiling | [`intellistream/vllm-request-lifecycle-profiler-plugin`](https://github.com/intellistream/vllm-request-lifecycle-profiler-plugin) |
| KV prefix sharing | [`intellistream/kv-prefix-sharing-plugin`](https://github.com/intellistream/kv-prefix-sharing-plugin) |
| Ascend topology/parallelism research | [`intellistream/ascend-topology-aware-parallelism`](https://github.com/intellistream/ascend-topology-aware-parallelism) |

## Changes that are not plugin repositories

The following classes remain host/upstream work unless a separate behavior
implementation and stable seam are demonstrated:

- EAGLE/EAGLE3 and DeepSeek proposer compatibility fixes that implement normal
  vLLM or vLLM-Ascend model support;
- EPLB inner-loop optimizations, DP metadata buffer reuse, attention boundary
  vectorization, logprob/pooling materialization, and other general hot-path
  fixes;
- device initialization, build, packaging, CI, benchmark, security, and
  compatibility repairs;
- Mooncake server-name fixes inside the official connector;
- experimental patches that were closed unmerged or later reverted.

These should be rebased and proposed upstream, retained as host-seam commits,
or kept in research carriers. Packaging a patch does not make it a plugin.

## Required repository shape

Every extracted extension repository must contain:

- `pyproject.toml` with a unique distribution and Python namespace;
- a static manifest registered through `vllm_hust.extension_bundles`;
- explicit `kind`, `host`, `runtime`, `lifecycle_owner`, permissions,
  compatibility range, conflicts, and required services;
- source provenance mapping every extracted file to legacy PRs and authors;
- install, inspect, validate, enable, run, disable, and uninstall instructions;
- host-contract tests that use public seams rather than monkey patches;
- disabled-path equivalence, incompatible-host rejection, conflict, degraded
  dependency, restart, and uninstall/rollback tests;
- real-device evidence only where the repository makes a device-performance
  or correctness claim.

The first release remains `0.x` until the host contract and extension manifest
are frozen and the package passes the Extension Manager acceptance suite.

## Execution order

1. Ask each original owner to confirm attribution, license/provenance, intended
   maintainer, and whether the project should continue.
2. Recover exact source commits and tests into an owner-approved development
   repository while retaining `NOTICE` and `PROVENANCE.md`.
3. Reduce host changes to a neutral seam and submit that seam independently to
   the fresh HUST fork or upstream project.
4. Implement the external package and static manifest without activation side
   effects.
5. Run host-unit, package, conflict, disabled-path, failure, restart, and
   uninstall tests.
6. Run matched real-device validation for supported profiles.
7. Publish an alpha, add the website card with accurate team ownership, and
   freeze the compatibility contract only after acceptance.

Recommended first batch: Prefix Routing, PyramidKV, KV Tiering, KNorm, and
SliceGPT. SimLLM, graph-parallel/split-batch, pipeline microbatch scheduling,
and unified communication follow after their host seams and owners are
confirmed.
