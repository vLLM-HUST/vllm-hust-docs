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
| 插件生命周期管理 | `vLLM-HUST/vllmhust` | 独立 Python distribution | 已建立可运行基线 |

迁移前 metadata、分支引用、Issue/PR 清单和校验和保存在：

```text
/home/shuhao/repository-archives/rebaseline-20260831
```

旧 Issue、PR、fork 和提交历史保留在 legacy 仓库。历史证据链接必须直接指向 legacy 地址；新 fork 不承接旧 PR 编号语义。

## 2. 强制架构分层

### 2.1 官方运行时核心

`vllm-hust` 必须可持续同步官方 vLLM。核心补丁必须同时满足：

1. 外部组件没有该 hook 就无法实现；
2. hook 属于通用机制，不包含 BidKV、Mooncake、LMCache、PegaFlow 等系统名称；
3. 未启用时与官方行为一致，且不扫描、不 import 插件实现；
4. 接口有版本、明确输入输出和 fail-closed 验证；
5. 补丁可单独向官方上游提交；
6. 有默认路径等价测试和外部实现行为测试。

manifest、安装状态、enable/disable、配置持久化、进程管理、sidecar 编排、目录和发布逻辑不属于 vLLM 核心。

### 2.2 平台实现

`vllm-ascend-hust` 是官方 vLLM Ascend 的规范 fork和平台 profile，不是所有 Ascend 优化的收纳仓库。只有 vLLM Ascend 本身必须修改且有上游价值的代码进入该 fork。独立 scheduler policy、KV policy、算子族、实验 runner 和控制系统分别外置。

### 2.3 薄领域 hook

核心 hook 是引擎机制，不是 bundle。首个重基线 hook 为：

```text
vllm.victim_selector (API version 1)
```

它只负责显式调用 scheduler-local selector。没有配置时保持官方 FCFS/priority 行为且不扫描 entry point；显式选择时校验唯一性、API 版本、初始化结果和返回 request 身份。

### 2.4 `vllmhust` 生命周期管理器

独立 `vllmhust` 包负责：

- 从 installed distribution metadata 静态发现 manifest；
- 在 import 实现前校验 identity、版本和 manifest；
- 保存显式 enable/disable 状态；
- 合并插件声明的环境和 `additional_config`；
- 生成或执行 vLLM 启动命令；
- 后续承载 install/uninstall、服务、health、rollback 和诊断。

它不得覆盖全局 `VLLM_PLUGINS` 而意外禁用 `ascend` 等平台插件。

### 2.5 插件 Bundle

插件是可独立构建、安装、启用、禁用和卸载的发行包。安装只表示可发现，不自动改变服务行为。manifest 描述 bundle/components；activation 描述实际 entry point、环境和 vLLM 配置。

```bash
pip install vllmhust
pip install bidkv
vllmhust plugin list
vllmhust plugin enable org.vllm-hust.bidkv
vllmhust run -- vllm serve MODEL
```

### 2.6 KV 系统与 connector

Mooncake、LMCache、PegaFlow 是外部 KV 状态/传输/存储系统，不是 vLLM 插件本体：

```text
external KV system
  -> scheduler connector
  -> worker connector
  -> optional API/telemetry adapter
  -> vLLM-owned KV connector contract
```

connector 可以由 distribution 或 bundle 交付，但系统、connector、交付方式必须分别建模。

### 2.7 Control plane 与 bridge

control plane 负责跨实例 admission、placement、routing 和全局策略，必须位于引擎之外。vLLM 只提供有界、本地、可授权、可回执的 bridge contract。通用 sidecar 编排属于 `vllmhust` 或独立 bridge 包，不进入默认核心启动路径。

## 3. 核心补丁预算

每个 release window 维护下游补丁表，至少记录 hook、上游缺口、默认路径证据、外部消费者、上游计划和删除条件。

禁止把旧仓库的 733/563 个 downstream-only 提交整体 merge 或 rebase 到新 fork。每项能力必须重新分类：

- 官方已实现：删除下游实现；
- 必需薄 hook：重写为最小补丁；
- runtime component：迁移到插件仓库；
- 外部系统/bridge：迁移到系统或 connector 仓库；
- benchmark/docs/evidence：迁移到工具或文档仓库；
- 无消费者或无证据：仅保留在 legacy archive。

## 4. 插件迁移验收

1. clean environment wheel 安装成功；
2. 静态 manifest 发现不 import 实现；
3. 未启用时核心默认行为不变；
4. enable 后真实 hook 被调用，而非仅解析 manifest；
5. 配置冲突和缺失 hook fail closed；
6. start、health、stop、disable、uninstall、baseline restart 均有记录；
7. 性能声明使用 matched baseline；
8. 文档和网站区分插件、connector、外部系统、control plane、平台和工具。

## 5. 修订版执行顺序

1. 保持两个新 fork 的 `main` 与官方同步；
2. 在 `feature/unified-plugin-api-v1` 逐个重写必需薄 hook；
3. 完成并发布 `vllmhust`；
4. 用 BidKV 验证 install → discover → enable → run → disable → uninstall；
5. 依次迁移 KV compression、DiffSpec、LatchMoE 和其他旧能力；
6. 为 Mooncake、LMCache、PegaFlow 分离 system 与 connector 清单；
7. 更新网站 registry、文档、CI 和兼容矩阵；
8. 修正所有语义上属于 legacy PR 的历史链接。
