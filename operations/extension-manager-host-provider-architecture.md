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
进程持有。Manager 生成 entry-point 选择、环境变量和 `additional_config`，实际
加载仍由 vLLM 执行。核心只保留通用 `vllm.victim_selector` 窄 hook。

### 3.2 Mooncake / LMCache

Mooncake 本体是外部 KV 状态、传输和存储系统；`MooncakeConnector` 与
`MooncakeStoreConnector` 是 vLLM connector。无侵入 Provider 只生成官方
`kv_transfer_config`、检查服务 API，并把服务不可达投影为 `degraded`。它不启动、
停止、升级 Mooncake，不删除 KV 数据，也不立即引入自维护 Mooncake Fork 或 C++
动态插件 ABI。

LMCache 采用独立的无侵入 Provider，而不是 Mooncake Provider 的别名。它优先生成
官方 `LMCacheMPConnector`（也可显式选择兼容的 V1/dynamic connector）配置，检查
外部 MP HTTP 服务的 `/healthcheck`，并可输出 Production Stack 所需的 LMCache
values。LMCache 内部 backend、transport、runtime plugin、controller 以及 KV 数据
仍由 LMCache 管理；Manager 不调用 clear、evict 或 delete 接口。

实现以 LMCache 官方的 [MP 配置说明](https://docs.lmcache.ai/mp/configuration.html)
和 [vLLM dynamic connector 说明](https://docs.lmcache.ai/api_reference/dynamic_connector.html)
为准；`LMCacheConnectorV1` 属于兼容路径，新增部署默认使用 MP 模式。

Mooncake 与 LMCache Provider 都可把标准 `kv_transfer_config` 委托给 `vllm-hust-ext
run`。单个 vLLM 进程只能接受一份该配置；若两者同时 enabled，Manager 必须报告
冲突并拒绝启动，不能按 Provider 名称硬编码优先级。实验 profile 精确依赖同版本
Manager，冻结兼容契约后再改为稳定的版本范围。

### 3.3 Production Stack / Kubernetes

该 Provider 描述 `control_plane_extension`，支持 Helm values、渲染后的
Kubernetes manifest、CRD、controller、router、autoscaler 和 OCI 载体。第一阶段
只生成 values、`helm template` 计划、server dry-run 输入和 rollout 检查；实际
apply/uninstall 必须由拥有 kube context 和审批的 Kubernetes operator 执行。

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
2. Mooncake 与 LMCache 各自使用官方 connector，完成真实外部服务
   健康/中断/恢复，且无隐式服务或 KV 数据变更；
3. Production Stack 对官方 chart 渲染、server dry-run、rollout 检查，且无
   apply/uninstall；
4. 冲突、版本不兼容、缺服务、不可达、部分健康、降级、禁用、重启回退；
5. 112 与 91 clean environment 安装/卸载和宿主一致性。

当前完成的是 Provider 原型、静态 schema、单元测试和 clean-environment
plan/render/check smoke；不等于真实 Mooncake 或 Kubernetes 集群验收。

逐项执行证据见 [2026-09-01 验收记录](extension-manager-acceptance-20260901.md)。
