# 技术架构与仓库分工

## 从请求到硬件

| 层 | 主要职责 | 入口 |
| --- | --- | --- |
| 应用与调用方 | SAGE 组织流式推理与智能体工作流，Sage Mate 是基于 SAGE 的应用。Workstation 提供部署与使用界面 | [SAGE](https://github.com/RIDE-Lab/SAGE) · [Sage Mate](https://github.com/RIDE-Lab/sage-mate) · [Workstation](https://github.com/vLLM-HUST/vllm-hust-workstation) |
| 服务和引擎 | OpenAI 兼容服务入口、请求调度、模型执行及 KV-cache 生命周期 | [vllm-hust](https://github.com/vLLM-HUST/vllm-hust) · [对应上游](https://github.com/vllm-project/vllm) |
| 设备后端 | Ascend 设备插件、设备执行及算子集成。Apple Silicon 有独立的 Metal 插件 | [vllm-ascend-hust](https://github.com/vLLM-HUST/vllm-ascend-hust) · [对应上游](https://github.com/vllm-project/vllm-ascend) · [vllm-metal-hust](https://github.com/vLLM-HUST/vllm-metal-hust) |
| 编译与模型准备 | Triton Ascend 编译后端、Ascend 量化及环境诊断 | [Triton Ascend](https://github.com/vLLM-HUST/triton-ascend-hust) · [量化](https://github.com/vLLM-HUST/vllm-ascend-quant-hust) · [环境管理](https://github.com/vLLM-HUST/ascend-runtime-manager) |
| 扩展与外部服务 | Extension Manager 管理 manifest、兼容性、冲突、启用意图和 Provider 委托。vLLM、Mooncake、Kubernetes 分别负责各自实际执行 | [Extension Manager](https://github.com/vLLM-HUST/extension-manager) · [ECPA 架构](https://github.com/vLLM-HUST/vllm-hust-website/blob/main/docs/PLUGIN_STANDARD.md) |
| 部署与控制面 | 管理单机或容器服务、Kubernetes 扩缩容、Ray 控制器 | [Dev Hub](https://github.com/vLLM-HUST/vllm-hust-dev-hub) · [Production Stack](https://github.com/vLLM-HUST/production-stack-hust) · [RIDE](https://github.com/vLLM-HUST/ride) |
| 测量与展示 | Benchmark 保存工作负载、测量、报告和发布源。官网消费已提交的数据快照 | [Benchmark](https://github.com/vLLM-HUST/vllm-hust-benchmark) · [Website](https://github.com/vLLM-HUST/vllm-hust-website) |

vLLM-HUST 负责推理底座，RIDE Lab 主要维护 SAGE 核心仓库。跨组织调用按接口和依赖版本定位。这里的 `vLLM-HUST/ride` 是 Ray 推理控制面仓库，`RIDE-Lab` 是 GitHub 组织。SGLang 是独立运行时线，适配 SGLang 的成果需单列宿主、版本及验证结果。 [组织主页](https://github.com/vLLM-HUST) · [SGLang HUST](https://github.com/vLLM-HUST/sglang-hust)

## 研究成果与 MOD

| 入口 | 核心机制 | 接手时先检查 |
| --- | --- | --- |
| [BidKV](https://github.com/vLLM-HUST/vllm-hust-bidkv) | KV 压力下按效用挑选待驱逐请求 | 当前仓库、论文/实验世代、宿主版本和启用、回滚证据。旧 Ascend 仓库已归档 |
| [DiffSpec](https://github.com/vLLM-HUST/vllm-ascend-hust-diffspec) | 用差分推测解码加速长序列生成 | 外部集成接口、目标 Ascend 配置和配对证据 |
| [ECPA / Extension Manager](https://github.com/vLLM-HUST/extension-manager) | 扩展的发现、组合、校验和可回滚启用 | 管理器版本、宿主与 Provider 契约、实际生效及冲突测试 |
| [MOD Catalog](https://vllm-hust.sage.org.ai/plugins.html) | 按具体机制查找缓存、调度、算子、编译、精度、可观测性等扩展 | 条目生命周期、支持范围、固定版本、是否可执行及对应验证来源 |

源码流向见 [引擎执行链](https://github.com/vLLM-HUST/vllm-hust-docs/blob/main/architecture/vllm-hust-engine-execution-chain.md) 和 [平台插件链](https://github.com/vLLM-HUST/vllm-hust-docs/blob/main/architecture/vllm-hust-platform-plugin-chain.md)。
