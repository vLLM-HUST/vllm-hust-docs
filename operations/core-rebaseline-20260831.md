# vLLM-HUST 核心仓库重基线与外部扩展边界

> 状态：执行中；生效日期：2026-08-31。
>
> 本文取代旧方案中“在 vLLM 核心实现完整 Bundle host/CLI/sidecar”的实施边界。

## 1. 仓库重基线

| 角色 | 当前仓库 | 关系 | 验证状态 |
| --- | --- | --- | --- |
| vLLM 规范 fork | `vLLM-HUST/vllm-hust` | fork of `vllm-project/vllm` | `main` 与上游逐 SHA 一致 |
| Ascend 规范 fork | `vLLM-HUST/vllm-ascend-hust` | fork of `vllm-project/vllm-ascend` | `main` 与上游逐 SHA 一致 |
| 旧 vLLM-HUST | `intellistream/vllm-hust-legacy-20260831` | 保留原 fork network | 已归档、只读 |
| 旧 Ascend 主线 | `intellistream/vllm-ascend-hust-legacy-20260831` | 保留原 network | 已归档、只读 |
| 扩展发现与启用管理 | `vLLM-HUST/extension-manager` | 独立 Python distribution `vllm-hust-ext` | 已建立可运行基线 |

迁移前 metadata、分支引用、Issue/PR 清单和校验和保存在：

```text
/home/shuhao/repository-archives/rebaseline-20260831
```

旧 Issue、PR、fork 和提交历史保留在 legacy 仓库。历史证据链接必须直接指向 legacy 地址；新 fork 不承接旧 PR 编号语义。

## 2. 强制架构分层

### 2.1 官方运行时核心

`vllm-hust` 必须可持续同步官方 vLLM。核心补丁必须同时满足：

1. 外部组件没有该 hook 就无法实现；
2. hook 属于通用机制，不包含具体扩展或外部系统名称；
3. 未启用时与官方行为一致，且不扫描、不 import 插件实现；
4. 接口有版本、明确输入输出和 fail-closed 验证；
5. 补丁可单独向官方上游提交；
6. 有默认路径等价测试和外部实现行为测试。

manifest、安装状态、enable/disable、配置持久化、进程管理、sidecar 编排、目录和发布逻辑不属于 vLLM 核心。

### 2.2 平台实现

`vllm-ascend-hust` 是官方 vLLM Ascend 的规范 fork和平台 profile，不是所有 Ascend 优化的收纳仓库。只有 vLLM Ascend 本身必须修改且有上游价值的代码进入该 fork。独立 scheduler policy、KV policy、算子族、实验 runner 和控制系统分别外置。

### 2.3 薄领域 hook

核心 hook 是引擎机制，不是 bundle。旧归档 fork 曾验证：

```text
vllm.victim_selector (API version 1)
```

新 vLLM-HUST 0.23 不恢复该私有 entry point，而是提供最小通用 typed
`vllm.scheduler.policy.v1` materializer，并从 legacy 吸收显式选择、重复检测、API
版本校验和来源日志。官方 vLLM 支持仍需跟踪 RFC #51608 / PR #51601。

### 2.4 vLLM-HUST Extension Manager（Core + Host Provider）

独立 `vllm-hust-ext` 包负责：

- 从 installed distribution metadata 静态发现 manifest；
- 在 import 实现前校验 identity、版本和 manifest；
- 保存显式 enable/disable 状态；
- 合并插件声明的环境和 `additional_config`；
- 生成或执行 vLLM 启动命令；
- 通过 Host Provider 承载 plan/render/check、health、rollback evidence 和诊断。

2026-09-01 起，Manager 不再按单一 vLLM/Python Bundle 建模。Core 负责发现、
兼容性、配置、状态和委托；vLLM、Mooncake、Production Stack/Kubernetes
分别由自己的 Host Provider 管理运行时边界。当前 schema 为
`0.2-experimental`，旧 Bundle v1 仅作为未承诺兼容的迁移输入。Manager 默认不
启停共享外部服务、不修改驱动、不删除 KV 数据，也不 apply 生产集群资源。

它不得覆盖全局 `VLLM_PLUGINS` 而意外禁用 `ascend` 等平台插件。

### 2.5 插件 Bundle

插件是可独立构建、安装、启用、禁用和卸载的发行包。安装只表示可发现，不自动改变服务行为。manifest 描述 bundle/components；activation 描述实际 entry point、环境和 vLLM 配置。

```bash
pip install vllm-hust-ext
pip install bidkv
vllm-hust-ext extension list
vllm-hust-ext extension status org.vllm-hust.bidkv
```

当前 BidKV 主包静态注册 typed manifest，不注册私有 `vllm.victim_selector`；
Manager 在 vLLM-HUST 0.23 上生成宿主原生 manifest，并拒绝
unverified/incompatible 的进程内 scheduler policy。

### 2.6 KV 系统与 connector

Mooncake、PegaFlow 是外部 KV 状态/传输/存储系统，不是 vLLM 插件本体：

```text
external KV system
  -> scheduler connector
  -> worker connector
  -> optional API/telemetry adapter
  -> vLLM-owned KV connector contract
```

connector 可以由 distribution 或 bundle 交付，但系统、connector、交付方式必须分别建模。

### 2.7 Control plane 与 bridge

control plane 负责跨实例 admission、placement、routing 和全局策略，必须位于引擎之外。vLLM 只提供有界、本地、可授权、可回执的 bridge contract。Extension Manager 只管理已安装 bridge adapter 的发现与启动配置；通用 sidecar 和 control-plane 服务编排属于独立系统，不进入管理器或默认核心启动路径。

## 3. 核心补丁预算

每个 release window 维护下游补丁表，至少记录 hook、上游缺口、默认路径证据、外部消费者、上游计划和删除条件。

禁止把旧仓库的 733/563 个 downstream-only 提交整体 merge 或 rebase 到新 fork。每项能力必须重新分类：

- 官方已实现：删除下游实现；
- 必需薄 hook：重写为最小补丁；
- runtime component：迁移到插件仓库；
- 外部系统/bridge：迁移到系统或 connector 仓库；
- benchmark/docs/evidence：迁移到工具或文档仓库；
- 无消费者或无证据：仅保留在 legacy archive。

## 4. 多宿主扩展迁移验收

1. clean environment wheel 安装成功；
2. 静态 manifest 发现不 import 实现；
3. 状态区分 compatible/configured/enabled/reachable/healthy/degraded；
4. vLLM enable 后真实 hook 被调用，而非仅解析 manifest；
5. Mooncake 服务不可达进入 degraded，但不隐式变更服务；
6. Production Stack 只做 plan/render/check 和 server dry-run，不默认 apply；
7. 配置冲突、宿主/API/协议不兼容和缺失 hook fail closed；
8. health、disable、uninstall、baseline restart 和 operator rollback 均有记录；
9. 性能声明使用 matched baseline；
10. 文档和网站区分插件、connector、外部系统、control plane、平台和工具。

## 5. 修订版执行顺序

1. 保持两个新 fork 的 `main` 与官方同步；
2. 在 `feature/unified-plugin-api-v1` 逐个重写必需薄 hook；
3. 完成 Extension Manager Core、实验 schema 和 Provider 协议；
4. 用 BidKV 验证 vLLM 宿主链；
5. 用 Mooncake 验证外部 KV service + 官方 connector 链；
6. 用 Production Stack 验证 Helm/CRD/controller/router/autoscaler/OCI 链；
7. 完成冲突、降级、不可达、回滚和无隐式外部变更测试；
8. 更新网站 registry、文档、CI 和兼容矩阵；
9. 在 112/91 完成三类端到端验收；
10. 通过后修订并冻结 v1，再发布 `vllm-hust-ext` alpha。
