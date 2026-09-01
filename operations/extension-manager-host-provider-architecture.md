# vLLM-HUST Extension Manager：Core + Host Provider 重构基线

状态：实施中，禁止发布 alpha 或宣称 Manifest v1 稳定。

## 1. 产品边界

正式产品名为 **vLLM-HUST Extension Manager**，仓库为
`vLLM-HUST/extension-manager`，候选 PyPI 包和 CLI 为 `vllm-hust-ext`。

它统一处理安装态发现、静态校验、兼容性证据、配置、启停意图、状态投影、冲突
检查以及向宿主委托。它不是 vLLM 发行版、control plane、Kubernetes 部署系统，
也不取得外部 KV 服务的生命周期所有权。

## 2. Core 与 Provider

Core 只提供：

- `vllm_hust.extension_bundles` 静态 manifest 发现；
- 实验 schema 解析与 host/protocol version range 校验；
- 配置持久化和 enabled intent；
- `installed`、`discovered`、`compatible`、`configured`、`enabled`、
  `reachable`、`healthy`、`degraded`、`incompatible` 状态证据；
- plan 冲突检查，以及 `plan`、`render`、`check` 委托。

Provider factory 使用 `vllm_hust_ext.providers`。第一阶段协议没有 `apply`、
`delete` 或 `uninstall_service`；Core 拒绝 Provider 生成的隐式 mutating action。
包卸载由 pip 等包管理器负责。标准顺序是宿主回退/重启、`disable`、`forget`、
`pip uninstall`；`forget` 仅删除 Manager 保存的配置和启用意图，并拒绝仍处于
enabled 的扩展，防止重装后意外恢复陈旧状态。

## 3. 三类宿主

### 3.1 vLLM / BidKV

BidKV 是 `scheduler_policy`，运行在 vLLM scheduler 进程中，生命周期由 vLLM
进程持有。Manager 只在宿主和协议兼容证据明确时生成宿主原生 manifest 与启动
配置，实际加载仍由 vLLM 执行。vLLM-HUST 0.23 提供最小、通用且不含 BidKV
名称的 `vllm.scheduler.policy.v1` typed materializer；不恢复私有
`vllm.victim_selector` 自动发现。

2026-09-01 已从 legacy HUST 实现恢复显式选择、重复检测、API 版本校验和来源日志，
并与新的 typed admission 合并。91 上 8 个核心契约测试及 4 个真实 BidKV
materialization/轨迹回放测试通过。随后真实 Qwen3-0.6B 服务在 KV 100% 压力下
产生 3 次 `UTILITY_ACTIVE`，三个请求均完成；disable 后的新进程未加载 BidKV 并
成功返回 completion。官方 vLLM 上游已有
[Scheduler Plugin RFC #51608](https://github.com/vllm-project/vllm/issues/51608)
和 [draft PR #51601](https://github.com/vllm-project/vllm/pull/51601)，目标是
`vllm.scheduler_plugins`、只读 feature 和独立 PreemptionScore。新 fork 不应再
创建竞争的私有接口。BidKV 主发行包不注册该非官方 entry point；当前 manifest
声明 `vllm.scheduler.policy.v1` 和 active Python carrier。Manager 只在宿主实际
导出该契约时报告 compatible，并拒绝 unverified/incompatible scheduler policy。
官方 vLLM 继续明确为 unsupported。

截至 draft PR #51601 head
`f8b7db61e446911e0d62fcb8220f863d6098c471`，代码仍是单一
`PreemptionPlugin.preemption_key(Request, position)` 和进程内 registry；同一提交的
设计文档却描述可组合、加权、批量、只读 feature 的 `PreemptionScore` 以及未来
`vllm.scheduler_plugins` descriptor。RFC 还明确把 out-of-tree 支持放在接口稳定
之后。BidKV 首期只映射“核心已批准候选后的 victim ranking”；主动触发抢占、修改
waiting queue、KV cleanup 和 reinsertion 仍归核心，不能通过 monkey patch 带回。

### 3.2 Mooncake

Mooncake 本体是外部 KV 状态、传输和存储系统；`MooncakeConnector` 与
`MooncakeStoreConnector` 是 vLLM connector。无侵入 Provider 只生成官方
`kv_transfer_config`、检查服务 API，并把服务不可达投影为 `degraded`。它不启动、
停止、升级 Mooncake，也不删除 KV 数据。[`vLLM-HUST/mooncake-hust`](https://github.com/vLLM-HUST/mooncake-hust)
是 `kvcache-ai/Mooncake` 的上游优先薄 fork：官方已经提供 Ascend NPU CI、aarch64
NPU wheel、arm64 wheel 与多架构镜像，因此当前不维护核心实现差异，也不引入自有
C++ 动态插件 ABI。只有在 HUST 主机复现明确缺口后才加入窄补丁，并优先回馈上游。

`mooncake-transfer-engine-non-cuda==0.3.12.post1` 已在 A100 主机用无 GPU
一次性容器完成两条相互独立的真实数据路径：两个 TransferEngine 进程通过
TCP/P2PHANDSHAKE 写入并逐字节校验 1 MiB，以及隔离 Master、内置 HTTP metadata
和 Store REST 的 put/exist/get/remove。普通 remove 受对象 lease 约束，Manager
因此不得把删除 KV 当作 adapter disable/uninstall。上游没有为 Store REST 与
`kv_transfer_config` 单独发布协议 semver，实验 manifest 将其明确标为 unversioned，
不再虚构 `1.0`；兼容性由 Mooncake package/host 范围和可执行验收证据约束。

Mooncake Provider 可把标准 `kv_transfer_config` 委托给 `vllm-hust-ext run`。
单个 vLLM 进程只能接受一份该配置；冲突时 Manager 必须拒绝启动，不能硬编码
优先级。实验 profile 精确依赖同版本 Manager，冻结兼容契约后再改为稳定范围。

### 3.3 Production Stack / Kubernetes

该 Provider 描述 `control_plane_extension`，支持 Helm values、渲染后的
Kubernetes manifest、CRD、controller、router、autoscaler 和 OCI 载体。第一阶段
只生成 values、`helm template` 计划、server dry-run 输入和 rollout 检查；实际
apply/uninstall 必须由拥有 kube context 和审批的 Kubernetes operator 执行。
Provider 的健康证据必须拆成 controller reconciliation、Router traffic 和
autoscaler decision，并额外提交真实模型 Router 的结构化失败/恢复证据；mock
backend 只能算 smoke，不能支撑 healthy。`VLLMRouter.spec.replicas` 与 HPA 对同一 Deployment 的
`spec.replicas` 是双写冲突；除非上游 controller 明确委托副本所有权，否则 Manager
必须投影为 `incompatible + degraded`，不得自动选择胜者。

## 4. Manifest 0.2-experimental

当前单一 Python Bundle v1 假设冻结为未承诺兼容的历史实验。新实验 manifest
必须显式声明 `kind`、`host`、`runtime`、`lifecycle_owner`、`protocols`、
`implementation` 和 `requires_services`，并可附带 typed components 与
activation。

载体可为 Python entry point、host builtin、外部服务、OCI image、Helm values、
Kubernetes manifest、CRD 或 controller。非官方注册不得占用新 `vllm.*`
命名空间。

## 5. 发布门禁

只有以下三条真实端到端链和横向失败测试全部通过后，才能修订并冻结 v1，再发布
alpha：

1. BidKV 安装、发现、配置、启用、真实 vLLM 加载、回退；
2. Mooncake 使用官方 connector，完成真实外部服务健康/中断/恢复，且无隐式
   服务或 KV 数据变更；
3. Production Stack 对官方 chart 渲染、server dry-run、rollout 检查，且无
   apply/uninstall；
4. 冲突、版本不兼容、缺服务、不可达、部分健康、降级、禁用、重启回退；
5. 112 与 91 clean environment 安装/卸载和宿主一致性。

当前已完成 Provider 原型、静态 schema、单元测试、clean-environment
plan/render/check smoke、官方 Mooncake 0.3.12.post1 TransferEngine TCP 与 Store
对象数据路径，以及官方
Production Stack chart 的本地 Helm template 和隔离 kind API server dry-run。
已在隔离 Kubernetes 1.34.11 中完成 Production Stack 官方 controller 调谐、官方
Router 到外部测试后端的真实转发，以及真实 Metrics API 驱动的 1→3 扩容；同时验证
controller/HPA 双写冲突。Mooncake 的真实 vLLM connector 命中和 Production Stack
Router 到既有 GLM-4-32B 的 500→200 数据面恢复也已通过。Production Stack 仍需
固化可复现的 vLLM-HUST arm64 发布载体；产品不要求 amd64。
该载体由官方仓库的薄 fork
[`vLLM-HUST/production-stack-hust`](https://github.com/vLLM-HUST/production-stack-hust)
维护，只包含 arm64 构建/发布和极少必要集成补丁。BidKV scheduler 的干净发布
载体验收也尚未完成。

逐项执行证据见 [2026-09-01 验收记录](extension-manager-acceptance-20260901.md)。

> 注：首期范围不包含 LMCache。
