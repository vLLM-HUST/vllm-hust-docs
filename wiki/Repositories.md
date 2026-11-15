# 公开仓库目录

盘点日期：2026-11-16（北京时间）。GitHub API 返回 70 个公开仓库，其中 11 个标记为 GitHub Fork，1 个已归档。用途供检索，分类按主要职责；运行时提供的功能、实验进度和可用条件以各仓库当前文档、发行版及实测记录为准。GitHub Fork 和生命周期是两个字段，未归档条目仍可能处于实验阶段。

## 核心运行时与平台适配

| 仓库 | 用途 | GitHub 状态 |
| --- | --- | --- |
| [`vllm-hust`](https://github.com/vLLM-HUST/vllm-hust) | vLLM 推理与服务核心 Fork，承载组织需要的通用运行时扩展点 | Fork |
| [`vllm-ascend-hust`](https://github.com/vLLM-HUST/vllm-ascend-hust) | Ascend NPU 设备插件与后端适配 | Fork |
| [`vllm-metal-hust`](https://github.com/vLLM-HUST/vllm-metal-hust) | Apple Silicon 的 vLLM 硬件插件 | Fork |
| [`sglang-hust`](https://github.com/vLLM-HUST/sglang-hust) | SGLang 推理与多模态服务 Fork | Fork |

## 编译、算子与模型工具

| 仓库 | 用途 | GitHub 状态 |
| --- | --- | --- |
| [`triton-ascend-hust`](https://github.com/vLLM-HUST/triton-ascend-hust) | 面向 Ascend NPU 的 Triton 语言和编译器 | Fork |
| [`vllm-ascend-quant-hust`](https://github.com/vLLM-HUST/vllm-ascend-quant-hust) | Ascend 上的训练后量化，覆盖 8 位、4 位和混合精度 | — |
| [`vllm-hust-opset`](https://github.com/vLLM-HUST/vllm-hust-opset) | Ascend 算子替换、融合及逐项性能证据 | — |
| [`ascend-runtime-manager`](https://github.com/vLLM-HUST/ascend-runtime-manager) | 部署环境诊断、安装与修复 | — |
| [`vllm-hust-weight-layout-research`](https://github.com/vLLM-HUST/vllm-hust-weight-layout-research) | 双 910B2 上的 Qwen3.5 权重布局实验 | — |

## 集群、路由与服务入口

| 仓库 | 用途 | GitHub 状态 |
| --- | --- | --- |
| [`production-stack-hust`](https://github.com/vLLM-HUST/production-stack-hust) | 面向 Kubernetes 的集群部署与运维 | Fork |
| [`ride`](https://github.com/vLLM-HUST/ride) | 基于 Ray 的推理控制面与 Coder App | — |
| [`ride-controller-demo`](https://github.com/vLLM-HUST/ride-controller-demo) | RIDE Controller 开发模板 | — |
| [`vllm-hust-workstation`](https://github.com/vLLM-HUST/vllm-hust-workstation) | 面向用户的 Web 工作台、部署入口和指标界面 | — |
| [`vllm-hust-prefix-router`](https://github.com/vLLM-HUST/vllm-hust-prefix-router) | 按前缀重用机会路由请求 | — |
| [`vllm-hust-request-lifecycle-profiler`](https://github.com/vLLM-HUST/vllm-hust-request-lifecycle-profiler) | 请求级生命周期追踪与瓶颈归因 | — |

## 扩展管理与开发模板

| 仓库 | 用途 | GitHub 状态 |
| --- | --- | --- |
| [`extension-manager`](https://github.com/vLLM-HUST/extension-manager) | 扩展发现、校验、启用配置与 Host Provider 委托 | — |
| [`extension-template`](https://github.com/vLLM-HUST/extension-template) | 通用扩展与 Host Provider 脚手架 | — |
| [`patch-plugin-template`](https://github.com/vLLM-HUST/patch-plugin-template) | 默认关闭的单机制 runtime patch 插件模板 | — |
| [`vllm-hust-dev-hub`](https://github.com/vLLM-HUST/vllm-hust-dev-hub) | 多仓工作区、Ascend 容器和服务管理 | — |

## KV 缓存、状态管理与存储

| 仓库 | 用途 | GitHub 状态 |
| --- | --- | --- |
| [`vllm-hust-bidkv`](https://github.com/vLLM-HUST/vllm-hust-bidkv) | BidKV 当前成果维护入口，面向 KV 压力的请求驱逐策略 | — |
| [`vllm-ascend-hust-bidkv`](https://github.com/vLLM-HUST/vllm-ascend-hust-bidkv) | BidKV 早期 Ascend 成果仓库，保留历史复现线索 | 已归档 |
| [`pegaflow-hust`](https://github.com/vLLM-HUST/pegaflow-hust) | PegaFlow 在 HUST 栈上的 KV 数据流与传输研究 | — |
| [`mooncake-hust`](https://github.com/vLLM-HUST/mooncake-hust) | Mooncake 服务平台，外置 KV 数据路径相关 | Fork |
| [`LMCache-Ascend`](https://github.com/vLLM-HUST/LMCache-Ascend) | LMCache 的 Ascend 适配 | Fork |
| [`vllm-ascend-kvcompress-hust`](https://github.com/vLLM-HUST/vllm-ascend-kvcompress-hust) | 面向 Ascend 的可扩展 KV-cache 压缩插件 | — |
| [`vllm-ascend-pyramidkv-hust`](https://github.com/vLLM-HUST/vllm-ascend-pyramidkv-hust) | PyramidKV 压缩 Provider | — |
| [`vllm-hust-knorm`](https://github.com/vLLM-HUST/vllm-hust-knorm) | KNorm KV-cache 压缩扩展 | — |
| [`vllm-hust-kv-tiering`](https://github.com/vLLM-HUST/vllm-hust-kv-tiering) | 分层 KV-cache 驻留策略 | — |
| [`vllm-ascend-mapped-kv-offload-hust`](https://github.com/vLLM-HUST/vllm-ascend-mapped-kv-offload-hust) | Ascend 映射主机内存的 KV offload | — |
| [`vllm-ascend-simllm-hust`](https://github.com/vLLM-HUST/vllm-ascend-simllm-hust) | 任务相似度驱动的 KV 重用集成 | — |
| [`vllm-hust-kv-transfer-observability`](https://github.com/vLLM-HUST/vllm-hust-kv-transfer-observability) | KV 传输与恢复的可观测性 | — |
| [`vllm-hust-kv-materialization-arrival-control`](https://github.com/vLLM-HUST/vllm-hust-kv-materialization-arrival-control) | 请求到达时的 KV 物化策略 | — |
| [`gdn-state-codec`](https://github.com/vLLM-HUST/gdn-state-codec) | Qwen3.5/3.8 GDN 循环状态编码 | — |
| [`stateaxis-prefix-cache-policy`](https://github.com/vLLM-HUST/stateaxis-prefix-cache-policy) | StateAxis 负载的 vLLM 前缀缓存激活策略 | — |

## 调度、并行与推测解码

| 仓库 | 用途 | GitHub 状态 |
| --- | --- | --- |
| [`vllm-ascend-hust-diffspec`](https://github.com/vLLM-HUST/vllm-ascend-hust-diffspec) | DiffSpec 长序列差分推测解码成果与运行时集成 | — |
| [`vllm-hust-vSpec`](https://github.com/vLLM-HUST/vllm-hust-vSpec) | Ascend 上的自适应推测解码 | — |
| [`vllm-hust-cuda-mtp`](https://github.com/vLLM-HUST/vllm-hust-cuda-mtp) | CUDA 上 Qwen3.5 MTP 的实验性激活和验证 | — |
| [`vllm-ascend-MuxPD-hust`](https://github.com/vLLM-HUST/vllm-ascend-MuxPD-hust) | Ascend 的 MuxPD 插件 | — |
| [`vllm-ascend-split-batch-hust`](https://github.com/vLLM-HUST/vllm-ascend-split-batch-hust) | Ascend 拆批与全图并行执行实验 | — |
| [`vllm-ascend-layered-prefill-hust`](https://github.com/vLLM-HUST/vllm-ascend-layered-prefill-hust) | Ascend Layered Prefill 机制 | — |
| [`vllm-hust-pipeline-microbatch`](https://github.com/vLLM-HUST/vllm-hust-pipeline-microbatch) | 流水线微批次调度实验 | — |
| [`vllm-hust-qos-scheduler`](https://github.com/vLLM-HUST/vllm-hust-qos-scheduler) | 面向 deadline 的 QoS 调度实验 | — |
| [`vllm-hust-scheduler-policy-lab`](https://github.com/vLLM-HUST/vllm-hust-scheduler-policy-lab) | 调度策略与运行时切换实验 | — |
| [`vllm-hust-unified-comm`](https://github.com/vLLM-HUST/vllm-hust-unified-comm) | 设备无关的通信运行时 | — |
| [`ascend-distributed-metadata`](https://github.com/vLLM-HUST/ascend-distributed-metadata) | Ascend 分布式元数据 | — |
| [`vllm-hust-prefill-microflow`](https://github.com/vLLM-HUST/vllm-hust-prefill-microflow) | Qwen3.5 BF16 TP2 的实验性 Prefill Microflow | — |
| [`vllm-hust-prefill-admission`](https://github.com/vLLM-HUST/vllm-hust-prefill-admission) | 在步预算约束下优化 Prefill 准入和短请求 | — |

## 模型执行路径与细粒度优化

| 仓库 | 用途 | GitHub 状态 |
| --- | --- | --- |
| [`vllm-hust-slicegpt`](https://github.com/vLLM-HUST/vllm-hust-slicegpt) | SliceGPT 离线处理及运行时扩展 | — |
| [`vllm-hust-activation-sparsity`](https://github.com/vLLM-HUST/vllm-hust-activation-sparsity) | TEAL、LaRoSA 等激活稀疏化实验 | — |
| [`vllm-hust-gdn-optimizations`](https://github.com/vLLM-HUST/vllm-hust-gdn-optimizations) | Ascend 上默认关闭的 GDN 执行优化 | — |
| [`vllm-hust-runtime-micro-optimizations`](https://github.com/vLLM-HUST/vllm-hust-runtime-micro-optimizations) | 运行时元数据与细粒度开销优化 | — |
| [`vllm-ascend-attention-optimizations`](https://github.com/vLLM-HUST/vllm-ascend-attention-optimizations) | 默认关闭的 Ascend Attention 路径优化 | — |
| [`vllm-hust-graph-coverage`](https://github.com/vLLM-HUST/vllm-hust-graph-coverage) | 图捕获覆盖配置与回滚验证 | — |
| [`sglang-hust-prepared-dispatch`](https://github.com/vLLM-HUST/sglang-hust-prepared-dispatch) | 固定 SGLang 和 TorchNPU 栈的 FIA graph-update dispatch | — |

## 评测、负载与分析

| 仓库 | 用途 | GitHub 状态 |
| --- | --- | --- |
| [`vllm-hust-benchmark`](https://github.com/vLLM-HUST/vllm-hust-benchmark) | 评测编排、工作负载入口、原始证据和网站数据 | — |
| [`vllm-hust-profiling`](https://github.com/vLLM-HUST/vllm-hust-profiling) | 核心运行时与 Ascend 插件的性能剖析 | — |
| [`agentx-bench`](https://github.com/vLLM-HUST/agentx-bench) | 固定版本的 AgentX 轨迹回放和 smoke 配置 | — |
| [`swe-prefix-reuse`](https://github.com/vLLM-HUST/swe-prefix-reuse) | SWE 工作负载的前缀重用 | — |
| [`hust-agentperf`](https://github.com/vLLM-HUST/hust-agentperf) | 回放真实 Agent 轨迹评估本地推理服务 | Fork |
| [`hust-eval-client-mmlu-pro`](https://github.com/vLLM-HUST/hust-eval-client-mmlu-pro) | 通过已有服务执行 MMLU-Pro 解题、评估和证据封存 | — |
| [`hust-eval-client-frontierscience`](https://github.com/vLLM-HUST/hust-eval-client-frontierscience) | FrontierScience 解题、裁判、基准和证据客户端 | — |
| [`hust-eval-client-hle-verified`](https://github.com/vLLM-HUST/hust-eval-client-hle-verified) | HLE-Verified 文本及图像评估与证据封存 | — |

## 文档、展示与社区

| 仓库 | 用途 | GitHub 状态 |
| --- | --- | --- |
| [`.github`](https://github.com/vLLM-HUST/.github) | 组织主页、贡献指引、支持和安全政策 | — |
| [`vllm-hust-docs`](https://github.com/vLLM-HUST/vllm-hust-docs) | 同步记录、架构、操作手册和组件登记 | — |
| [`vllm-hust-website`](https://github.com/vLLM-HUST/vllm-hust-website) | 官网、MOD 目录、评测和容量成本展示 | — |
| [`vllm-hust.github.io`](https://github.com/vLLM-HUST/vllm-hust.github.io) | GitHub Pages 标准入口，重定向到官网 | — |
| [`cccf-domestic-inference-engine-survey`](https://github.com/vLLM-HUST/cccf-domestic-inference-engine-survey) | 国产推理引擎综述资料 | — |
| [`statesys-2026`](https://github.com/vLLM-HUST/statesys-2026) | StateSys 2026 学术研讨会网站 | — |

## 外围应用与参考 Fork

| 仓库 | 用途 | GitHub 状态 |
| --- | --- | --- |
| [`EvoScientist`](https://github.com/vLLM-HUST/EvoScientist) | 自演化科研智能体应用 | Fork |
| [`claude-code-hust`](https://github.com/vLLM-HUST/claude-code-hust) | IDE 与编码助手方向的外围参考 Fork | Fork |

## 查找新增或迁移的项目

- [GitHub 公开仓库列表](https://github.com/orgs/vLLM-HUST/repositories?type=public)
- [MOD 目录与项目详情](https://vllm-hust.sage.org.ai/plugins.html)
- [组件登记与作用域](https://github.com/vLLM-HUST/vllm-hust-docs/tree/main/registry)
- [历史仓库索引](https://github.com/vLLM-HUST/vllm-hust-docs/blob/main/repo-inventory.md)
