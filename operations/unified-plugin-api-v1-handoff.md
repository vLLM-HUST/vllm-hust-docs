# vLLM-HUST 统一插件 API v1 标准化改造交接书

> **边界变更（2026-08-31）：** 本文保留为早期设计审计资料，但不再是当前
> 实施入口。核心仓库已经从官方重新建立规范 fork；manifest discovery、安装状态、
> enable/disable、配置持久化和生命周期管理迁移到独立 `vLLM-HUST/vllmhust` 包。
> vLLM 核心只保留外部组件不可替代的薄领域 hook。当前执行规范见
> `operations/core-rebaseline-20260831.md`。

> 状态：待专用实现线程接管
>
> 编写日期：2026-08-28
>
> 主要实现仓库：`/home/shuhao/vllm-hust`
>
> 参考原型仓库：`/home/shuhao/statecentric-ascend-engine`

## 1. 接管指令

你现在负责接管 vLLM-HUST 与 State-Centric Native Engine 的统一标准插件体系改造。

请直接完成代码实现、CPU 测试、微基准、架构文档和 gap report，不要只停留在设计讨论。除非遇到会实质改变架构方向且无法从仓库中查明的问题，否则应通过代码审计做出保守、可验证的决定并继续推进。

此次工作的核心不是包装旧 vLLM entry point，而是建立一套由 vLLM-HUST 和 State-Centric Native Engine 共用、版本化、显式、可隔离、热路径安全的插件标准。

## 2. 用户最新决策

早期需求曾包含兼容原有 vLLM entry point，但用户后来明确决定：

> 向后兼容没必要，我们可以制作一套更好的插件系统给两个系统。

因此，以该最新决定为准：

1. 不要求旧的 `vllm.general_plugins`、`vllm.platform_plugins` 等插件未经修改即可运行。
2. 不需要实现以 `importlib.metadata` 为核心的旧 entry-point compatibility bridge。
3. 不要为兼容旧插件保留任意 import-time registry mutation。
4. 不要声称旧插件已兼容。
5. 必须审计旧扩展的能力需求，判断新体系能否通过显式、类型化契约接纳这些行为。
6. 可以制作外部迁移 adapter，但 adapter 不应成为新核心契约或默认启动路径的一部分。
7. “已兼容”必须表示插件行为通过测试，不能只表示 manifest 被读取或模块成功 import。

旧扩展的审计结论应使用以下分类：

- 可直接重写为标准插件；
- 可通过独立 adapter 转换；
- 仅控制面部分可接纳，热路径部分必须改写为 Native plan、C ABI 或设备内核；
- 当前无法安全接纳。

## 3. 仓库、分支和已有状态

### 3.1 主要仓库

在以下仓库实现 vLLM 所拥有的通用 Python 标准：

```text
/home/shuhao/vllm-hust
```

此前记录的基线提交为：

```text
48b27166f36ecd093af6a3328e92651d23feb48e
```

此前 checkout 的起始分支为：

```text
codex/spec-decode-cudagraph-lcm
```

已创建目标分支：

```text
feature/unified-plugin-api-v1
```

接管后必须重新核验，不得假设这些状态仍未变化：

```bash
git -C /home/shuhao/vllm-hust status --short --branch
git -C /home/shuhao/vllm-hust diff --stat
git -C /home/shuhao/vllm-hust log -1 --oneline
```

如果分支不存在，应从本机与上述基线对应的当前 checkout 创建 `feature/...` 分支；不要 fetch、merge 或 rebase main 来“更新环境”。

### 3.2 已有规划文件

此前已创建：

```text
/home/shuhao/vllm-hust/.planning/unified_plugin_api_v1/task_plan.md
/home/shuhao/vllm-hust/.planning/unified_plugin_api_v1/findings.md
/home/shuhao/vllm-hust/.planning/unified_plugin_api_v1/progress.md
```

接管线程应先读取并继续维护这些文件。当前记录的阶段为：

1. 审计参考原型与目标仓库 API；
2. 定义 vLLM 自有 package 和 hook 边界；
3. 迁移 manifest、bundle、协议、sidecar 和 host；
4. 增加类型化控制面 hook；
5. 添加 CPU 行为测试；
6. 完成验证、文档和 Native/Ascend gap report。

### 3.3 参考实现

通用 Python 原型位于：

```text
/home/shuhao/statecentric-ascend-engine/plugin_api/v1/
```

重点参考文件包括：

```text
manifest.py
manifest.schema.json
bundle.py
protocol.py
client.py
sidecar.py
runtime.py
```

父仓库固定的 vLLM 子模块中可能还有薄适配层：

```text
/home/shuhao/statecentric-ascend-engine/third_party/vllm-hust/vllm/plugin_api/
/home/shuhao/statecentric-ascend-engine/third_party/vllm-hust/vllm/plugin_api/v1/
```

Native 参考实现可能包括：

```text
/home/shuhao/statecentric-ascend-engine/native/include/statecentric/plugin_api_v1.h
/home/shuhao/statecentric-ascend-engine/src/plugin_api_v1.rs
/home/shuhao/statecentric-ascend-engine/src/plugin_bundle_v1.rs
/home/shuhao/statecentric-ascend-engine/src/bin/native_plugin_plan.rs
/home/shuhao/statecentric-ascend-engine/benchmarks/native_plugin_hot_path_bench.c
/home/shuhao/statecentric-ascend-engine/tests/test_plugin_api_v1.py
```

这些都只是原型和语义参考。目标 vLLM-HUST 版本更新，禁止机械复制。

## 4. 迁移边界

### 4.1 应迁入 vLLM-HUST 的通用部分

- `vllm.plugin_api.v1` Python package；
- manifest 数据模型和 JSON Schema；
- bundle discovery；
- allowlist/denylist；
- artifact 路径和 SHA-256 验证；
- API 和 feature 协商；
- 依赖解析和稳定拓扑排序；
- framed sidecar protocol；
- sidecar client；
- 通用生命周期 host/runtime；
- 类型化 hook vocabulary 及输入输出 schema；
- 标准 execution plan descriptor；
- CPU 单元测试、集成测试和无插件开销测试；
- 通用架构、迁移矩阵和 gap report。

### 4.2 不应搬入 vLLM-HUST 的 State-Centric 专用部分

- Rust Native host；
- State-Centric scheduler/state policy 实现；
- Native Engine 二进制；
- State-Centric C++ operator；
- State-Centric 专用 policy 示例；
- Ascend/NPU 专用运行代码；
- Qwen3.8、GDN、HCCL executor/probe/evidence；
- SageMate 部署逻辑；
- State-Centric 专用 benchmark。

Python manifest 和 execution plan descriptor 必须能与 Native ABI 对齐，但 vLLM-HUST 不应依赖 State-Centric 顶层 Python 包。

## 5. 安全与仓库纪律

1. vLLM-HUST 的修改只能位于 `feature/...` 分支，不得直接修改 main。
2. 不得 commit 或 push，除非任务所有者明确授权。
3. 不得 fetch、merge、rebase 或盲目同步官方 main。
4. 保留所有他人的未提交修改，禁止使用：
   - `git reset --hard`；
   - `git clean`；
   - broad `git checkout --`；
   - broad `git restore`。
5. 修改前后保存 `git status --short`、`git diff --stat` 和自己文件的定向 diff。
6. 不得修改 Qwen3.8 executor、GDN、HCCL probe 及相关 evidence。
7. 不得占用、探测、终止或重启 NPU 0–3 上的 SageMate/vLLM-HUST 服务。
8. 此阶段只运行 CPU 测试，不根据硬件实验设计 API。
9. 先完整读取目标仓库的 `AGENTS.md`、`CONTRIBUTING.md`、`pyproject.toml` 和测试说明。
10. vLLM-HUST 禁止使用系统 Python 或裸 pip。所有 Python 命令使用 `.venv/bin/python` 或 `uv`。

禁止：

```bash
python ...
python3 ...
pip install ...
```

应使用：

```bash
.venv/bin/python -m pytest ...
.venv/bin/python -m ruff ...
```

## 6. 核心架构原则

1. Native resident core 保持小型。
2. 未配置插件时，默认启动和请求路径不执行插件扫描、不启动 sidecar、不导入插件实现。
3. 插件发现必须显式启用。
4. 插件是带 manifest 的独立 bundle，不是 import-time 全局 registry mutation。
5. Python 控制面插件默认运行在独立 sidecar 进程。
6. Python 插件可以生成 execution plan、scheduler policy、operator selection、state policy、parser/tokenizer configuration、artifact resolution plan 和 Native kernel descriptor。
7. 禁止任意 Python callback 进入逐 token、逐 decode step 或 scheduler 热路径。
8. 热路径能力必须下沉为 resident Native plan、版本化 C ABI、已验证共享库或设备内核。
9. Rust trait 不能作为跨编译器稳定 ABI。
10. 插件 crash、timeout、cancel、协议错误或 ABI 不匹配不能破坏 resident core。
11. 不支持的 execution domain、isolation、permission、hook 和 failure policy 必须 fail closed。
12. 不允许 manifest 声明成功但运行时静默忽略。

## 7. 建议 package 布局

在 vLLM-HUST 中优先建立：

```text
vllm/plugin_api/__init__.py
vllm/plugin_api/v1/__init__.py
vllm/plugin_api/v1/errors.py
vllm/plugin_api/v1/manifest.py
vllm/plugin_api/v1/manifest.schema.json
vllm/plugin_api/v1/contracts.py
vllm/plugin_api/v1/bundle.py
vllm/plugin_api/v1/protocol.py
vllm/plugin_api/v1/client.py
vllm/plugin_api/v1/sidecar.py
vllm/plugin_api/v1/runtime.py
vllm/plugin_api/v1/host.py
```

可以根据仓库现有风格合并少量文件，但职责必须清晰。

迁移后 sidecar 应通过以下形式启动：

```text
<当前 vLLM 虚拟环境 Python> -m vllm.plugin_api.v1.sidecar --stdio
```

不要继续依赖顶层 `plugin_api.v1`。确认 `manifest.schema.json` 会被 wheel 和 sdist 打包，并增加通过 `importlib.resources` 读取 schema 的测试。

## 8. Manifest v1 元契约

manifest 至少包含：

```text
plugin_id
plugin_version
api_version 或 api_version_range
plugin_kind
capabilities
hooks
execution_domain
isolation
dependencies
required_vllm_features
required_native_features
permissions
failure_policy
hot_path_contract
configuration_schema
deterministic
reentrant
fork_safe
artifacts
```

### 8.1 ID 与版本

- `plugin_id` 必须稳定、可比较、无路径穿越歧义；建议 reverse-DNS 或显式 namespace。
- bundle 集合中不得出现重复或大小写模糊冲突。
- `plugin_version` 使用 `packaging.version.Version` 验证。
- `api_version` 与 `api_version_range` 建议通过 JSON Schema `oneOf` 约束，只允许一种。
- `api_version_range` 使用 `packaging.specifiers.SpecifierSet`，不要手写有限的字符串解析器。
- 版本不兼容错误必须包含 `plugin_id`、host API version、插件请求版本/range 和拒绝原因。

### 8.2 Plugin kind

至少设计以下标准类别：

```text
execution_plan_provider
scheduler_policy_provider
request_transformer
response_transformer
io_processor
metrics_provider
model_descriptor_provider
parser_provider
artifact_resolver
lora_resolver
kv_policy_provider
kv_transport_provider
weight_transfer_provider
operator_provider
platform_provider
native_library
device_kernel
```

类别出现在 schema 中不等于 host 已支持。实际运行支持矩阵必须单独维护。

### 8.3 Execution domain 与 isolation

`execution_domain` 至少包含：

```text
control_process
worker_process
native_host
device_kernel
```

`isolation` 至少包含：

```text
in_process
subprocess
sandboxed_subprocess
```

第一阶段如果只实现 `subprocess`，必须明确拒绝其他模式。不得把普通 subprocess 假装成 sandboxed subprocess。

### 8.4 Dependencies 与 feature negotiation

- 支持对其他 `plugin_id` 的版本范围依赖；
- 稳定拓扑排序；
- 缺失依赖、版本不满足、依赖环和同名插件均结构化报错；
- `required_vllm_features` 和 `required_native_features` 与 host 显式 feature set 比较；
- 缺失 feature 时列出全部缺失项并 fail closed。

### 8.5 Permissions 与 failure policy

- permissions 默认空。
- 没有真正权限执行器时，非空 permission 必须拒绝，不能仅记录后忽略。
- failure policy 可以定义 `fail_load`、`disable_plugin`、`restart_sidecar` 等，但必须明确 discovery、validation、initialization、invocation 和 shutdown 阶段的语义。
- 未实现的 failure policy 必须拒绝。

### 8.6 Hot-path contract

至少表达：

```text
python_ipc: false
python_callback: false
resident_plan_required
native_abi_required
device_kernel_required
max_control_plane_latency_ms
plan_immutability 或 plan update semantics
```

任何声称进入 Native 热路径的插件都必须满足 `python_ipc=false` 和 `python_callback=false`。

### 8.7 Configuration 与行为声明

- 使用 manifest 的 `configuration_schema` 验证实际配置；
- 配置无效必须在 import/initialize 之前拒绝；
- `deterministic`、`reentrant`、`fork_safe` 应影响 host 的加载和进程使用策略，不能只是注释字段。

### 8.8 Artifacts

每个 artifact 至少包含：

```text
artifact_id
artifact_kind
relative_path
sha256
```

可选包含 size、ABI descriptor、platform constraints。

加载代码前必须：

- 拒绝绝对路径和 `../`；
- 确认解析路径仍位于 bundle root；
- 防止 symlink 逃逸；
- 验证 SHA-256；
- 检测重复 `artifact_id`。

JSON Schema 应优先使用 `additionalProperties: false`、`uniqueItems: true`、`$defs`、稳定 `$id` 和 schema version。

## 9. Hook 标准化与旧扩展审计

先重新审计目标 vLLM-HUST，而不是照抄父仓库旧结论。至少扫描：

```text
vllm.general_plugins
vllm.platform_plugins
vllm.io_processor_plugins
vllm.stat_logger_plugins
vllm.logits_processors
model registry / out-of-tree models
reasoning parser
tool parser
LoRA resolver
KV connector
weight-transfer connector
victim selector / scheduler extension
worker event hooks
operator/platform/device extension
其他 import-time registry mutation
```

建议命令：

```bash
rg -n "entry_points|general_plugins|platform_plugins|io_processor_plugins|stat_logger_plugins" .
rg -n "register|registry|Registry|load_plugin|load_plugins|import_module" vllm
rg -n "reasoning_parser|tool_parser|logits_processor|lora|kv_connector|weight_transfer" vllm
rg -n "victim_selector|scheduler.*policy|stat_logger|io_processor" vllm tests
```

已知目标仓库比父仓库固定的 submodule 更新，并已有：

```text
vllm/v1/core/sched/victim_selector.py
```

它是类型化扩展的重要参考，但不要将 sidecar IPC 放入每次 scheduler step。正确方向是由 Python 控制面生成 resident scheduler plan，再由本地实现执行。

compatibility matrix 对每类旧扩展必须记录：

- 当前发现机制；
- 入口参数和返回值；
- 加载进程；
- 生命周期；
- 是否进入逐 token/逐 step 热路径；
- 是否依赖全局 registry mutation；
- 隔离要求；
- 对应的新 `plugin_kind` 和 hook；
- 能否只在控制面执行；
- 是否必须生成 Native plan、C ABI 或 kernel；
- 可直接迁移、需要 adapter、部分可迁移或不能接纳；
- 具体原因。

建议 hook vocabulary：

```text
lifecycle.initialize
lifecycle.health
lifecycle.shutdown

plan.build_execution
scheduler.build_policy
operator.select
state.build_policy

request.build_transform
response.build_transform
io.build_processor_plan
metrics.build_configuration

parser.build_reasoning_config
parser.build_tool_config
tokenizer.build_configuration

artifact.resolve
lora.resolve
model.describe

kv.build_policy
kv.build_transport_plan
weight_transfer.build_plan

native.describe_library
kernel.describe_device_kernel
```

每个 hook 必须有明确 request/response schema。不要实现一个接受任意字符串和任意 dict 的万能 callback。

必须区分：

1. 已知 hook vocabulary；
2. host 当前实现的 hook；
3. host 当前未实现但标准保留的 hook；
4. 完全未知 hook。

后两类均应在插件 import 前 fail closed。

第一阶段至少真正执行并测试：

```text
lifecycle.initialize
plan.build_execution
lifecycle.health
lifecycle.shutdown
```

再选择一个无热路径 IPC 风险的 hook完成行为测试，例如 `io.build_processor_plan`、`metrics.build_configuration` 或 `scheduler.build_policy`。

## 10. Bundle discovery 与依赖解析

新体系使用显式 bundle roots。每个插件目录包含 `plugin.json`、实现模块和可选 artifact/schema/shared library。

要求：

1. discovery 顺序稳定，不依赖文件系统偶然顺序；
2. `plugin_id` 冲突明确报错；
3. allowlist/denylist 同时支持；
4. denylist 优先级明确；
5. 被过滤插件不得 import；
6. allowlist 中不存在的插件产生明确诊断；
7. 依赖拓扑排序稳定；
8. 同一 host 重复加载具有明确幂等语义；
9. 不同进程各自加载的语义可测试；
10. bundle 内容变化后的缓存失效语义写入文档；
11. manifest、configuration、artifact、API 和 feature 验证必须尽量发生在插件 import 之前。

## 11. Sidecar 协议

第一阶段可以使用 stdio framed JSON，禁止 pickle。协议至少包含：

- `protocol_version`；
- `request_id`；
- action/hook；
- payload；
- deadline/timeout；
- status；
- result 或结构化 error；
- 最大 frame size。

错误对象至少包含：

```text
code
message
plugin_id
hook
phase
retryable
details
```

协议应支持 handshake、initialize、health、hook invocation、cancel 和 shutdown。

重点修正参考原型可能存在的取消语义缺口：如果 sidecar 主循环同步执行插件函数，那么插件阻塞时无法读取 cancel frame。应选择以下明确方案之一：

- 使用受控 worker thread/process 执行 hook，让协议循环继续读取 cancel；
- 对合作式插件传递 cancellation token；
- 对不可合作插件在 hard timeout 后终止并重建 sidecar。

必须区分 cooperative cancellation 和 hard timeout restart，并测试超时/取消后 host 仍可继续处理健康请求。

插件 crash、EOF、错误 request ID、无效 JSON、超大 frame 或协议版本不匹配均不得使 host 崩溃。`restart_sidecar` 应恢复并重新初始化必要插件，避免无意义的双重 restart。

## 12. Host/runtime 生命周期

建议生命周期：

```text
discover
validate manifests
filter allowlist/denylist
negotiate API/features
verify configuration/artifacts
topological sort
start sidecar
handshake
initialize
invoke control-plane hooks
validate returned plans
materialize/publish plans
health
shutdown
```

要求：

1. host 显式声明支持的 domain、isolation、hooks、permissions 和 feature set；
2. 不支持情况 fail closed；
3. 返回 plan 后验证 `plugin_id`、plan schema、plan version 和 artifact 引用；
4. 返回 plan 必须声明 `python_ipc=false`；
5. plan 中不得包含任意 Python callable；
6. initialize/load 具有明确幂等性；
7. shutdown 释放 sidecar、pipe/socket 和临时资源；
8. 对象销毁后不遗留僵尸进程；
9. crash/timeout 后 host 状态仍可用；
10. 错误保留 `plugin_id`、phase、hook 和结构化原因。

默认执行 `import vllm` 时不得自动创建 host、扫描 bundle 或启动 sidecar。

## 13. Native ABI 边界

vLLM-HUST 主要负责 Python 控制面标准。文档和 plan descriptor 必须遵守以下 Native ABI 原则：

1. Rust trait 不作为稳定 ABI；
2. 跨语言热路径使用版本化 C ABI；
3. 所有公开结构首部含 `uint32_t struct_size` 和 `uint32_t abi_version`；
4. 使用 opaque handle；
5. 明确定义 create、load/initialize plan、execute、cancel、health、destroy/free；
6. 定义 allocator、ownership、buffer/string/error 生命周期、线程安全、可重入、fork、取消、超时和释放规则；
7. 允许较大的 `struct_size` 向前扩展；
8. 拒绝小于所需最小 size 的结构；
9. 拒绝不支持的 major ABI；
10. 可选尾部字段通过 size gate 读取；
11. 不可信控制面代码优先 sidecar；进程内 Native library 必须显式批准并验证 ABI；
12. Python 只生成 descriptor/plan，Native host 加载后热路径不再调用 Python。

## 14. CPU 测试矩阵

建议测试目录：

```text
tests/plugins_tests/test_plugin_api_v1.py
```

按目标仓库惯例调整。优先使用 `tmp_path` 动态构造 bundle。

### 14.1 Manifest/schema

- 合法 manifest；
- 缺失必需字段；
- 非法 additional property；
- 非法 `plugin_id`/`plugin_version`；
- `api_version` 与 range 冲突；
- 非法 range；
- configuration schema 成功/失败；
- unique items；
- 重复 artifact ID；
- package resource 中能读取 schema。

### 14.2 Discovery/filter/order

- 稳定 discovery；
- allowlist；
- denylist；
- denylist 优先级；
- 被过滤插件不 import；
- plugin ID 冲突；
- 稳定依赖排序；
- 缺失依赖；
- 依赖版本不匹配；
- dependency cycle。

### 14.3 Artifact/security

- 正确 SHA-256；
- digest mismatch；
- artifact 缺失；
- 绝对路径拒绝；
- `../` 拒绝；
- symlink 逃逸拒绝；
- 验证失败时实现模块不被 import。

### 14.4 API/features/capabilities

- exact API 成功；
- API range 成功；
- API 不兼容；
- 缺失 vLLM feature；
- 缺失 Native feature；
- 不支持 execution domain；
- 不支持 isolation；
- 未实现 permission；
- 未知/未实现 hook fail closed。

错误必须包含版本或缺失 capability 的具体原因。

### 14.5 Lifecycle 与 plan 行为

- initialize 确实执行；
- 重复 load/initialize 幂等；
- build execution plan 确实执行；
- plan plugin ID 错误拒绝；
- `python_ipc=true` 拒绝；
- health；
- shutdown；
- 资源释放；
- 无遗留 sidecar。

### 14.6 Isolation/recovery

- import 异常；
- initialize 异常；
- hook 异常；
- sidecar crash；
- timeout；
- cancel；
- crash/timeout 后 recovery；
- recovery 后健康插件继续工作；
- malformed/oversized frame；
- protocol/request ID mismatch；
- host 保持存活。

### 14.7 多进程与无插件路径

- 两个独立进程加载相同 bundle；
- `fork_safe=false` 时不复用 fork 前 sidecar/handle；
- parent/child 不共享 pipe；
- shutdown 不互相破坏；
- 未提供 bundle root 返回空集合；
- 不启动 sidecar；
- 不 import 插件实现；
- `import vllm` 不自动扫描；
- 默认请求路径没有 Python IPC。

### 14.8 端到端样例

由于不再要求旧 entry-point 向后兼容，至少实现：

1. 标准 execution-plan 插件：完成发现、初始化、plan 生成、plan schema 验证和 `python_ipc=false` 验证；
2. 标准 IO、metrics 或 scheduler-policy 插件：验证真实输出行为；
3. 不兼容插件：因 API/capability 不满足明确拒绝；
4. 崩溃插件：sidecar 隔离且 host 存活；
5. 超时插件：timeout 生效、无僵尸进程、后续健康请求可执行。

如制作旧插件 adapter，必须标注它是迁移示例，不是核心向后兼容保证。

## 15. 微基准

提供 CPU-only 微基准，分别报告：

- discovery/validation；
- sidecar startup；
- initialize；
- plan generation；
- resident-plan hot loop；
- 每种阶段是否发生 IPC。

微基准应证明：

1. 无插件时不启动 sidecar；
2. 无插件时常规路径没有插件 IPC；
3. plan 生成后模拟热路径只读取 resident plan/native descriptor；
4. 每 token/iteration 不调用 Python sidecar。

可以对比 no-plugin loop、resident-plan loop 和明确标注为禁止方案的 per-step IPC loop，但不要隐藏 sidecar 启动成本，也不要运行 NPU 测试。

## 16. 文档交付

vLLM-HUST 中至少提供：

```text
docs/design/plugin_api_v1.md
docs/vllm-plugin-compatibility-matrix.md
docs/plugin-gap-report.md
docs/plugin-validation.md
```

具体路径可按目标仓库文档布局调整。

主设计文档必须说明 manifest、bundle、API/feature 协商、hook vocabulary、sidecar protocol、取消/超时/恢复、artifact integrity、permissions、Native C ABI 边界、默认无插件路径，以及新插件开发示例。

compatibility matrix 至少覆盖 general/platform/IO/stat logger/logits/model registry/reasoning/tool/LoRA/KV/weight transfer/victim selector 和其他 registry mutation。

gap report 使用严格状态：

- 已兼容：行为测试通过；
- 部分兼容：仅控制面或 descriptor 已覆盖；
- 可迁移但尚未实现；
- 不兼容：给出安全、生命周期、ABI 或热路径原因。

禁止把“schema 已定义字段”写成“插件类别已兼容”。

## 17. 推荐实施阶段

1. 恢复上下文：读规范、status、planning files，记录基线。
2. 重审目标 vLLM-HUST 的全部扩展入口和新版 victim selector。
3. 建立 `vllm.plugin_api.v1`、manifest schema 和结构化错误。
4. 实现 bundle loader、artifact 验证、版本/feature 协商和稳定依赖排序。
5. 实现 framed protocol、sidecar、timeout、cancel、crash recovery。
6. 实现 host/runtime、hook registry/schema、plan validation 和幂等生命周期。
7. 完成 execution plan 与第二类标准插件端到端样例。
8. 完成 CPU 测试、lint、format 和微基准。
9. 完成架构文档、compatibility matrix、gap report 和 validation record。
10. 最终审计 Git diff，确认未触及禁止区域、未 commit、未 push。

## 18. 参考实现必须改进的问题

迁移原型时重点检查：

1. sidecar module 改为 `vllm.plugin_api.v1.sidecar`；
2. 使用 `packaging` 实现完整版本协商；
3. configuration schema 真正验证配置；
4. 未实现 `sandboxed_subprocess` 时拒绝；
5. 非空 permissions 未实施时拒绝；
6. 未支持的 failure policy 拒绝；
7. unsupported hook 在 import 前拒绝；
8. plan 验证 `plugin_id` 和 `python_ipc=false`；
9. artifact 验证 digest、重复 ID、路径和 symlink；
10. crash/timeout 后避免双重 restart；
11. 明确区分 request timeout 与 cancellation；
12. 修复同步 sidecar 无法及时读取 cancel 的问题；
13. host 不依赖 State-Centric 顶层包；
14. `import vllm` 不自动发现插件；
15. hook 输入输出使用类型或 schema，不使用无约束 dict callback。

## 19. 验证命令

按实际路径调整，但必须使用 `.venv`：

```bash
cd /home/shuhao/vllm-hust

git status --short --branch
git diff --check

.venv/bin/python -m pytest -q tests/plugins_tests/test_plugin_api_v1.py
.venv/bin/python -m pytest -q tests/plugins_tests/ -k plugin_api
.venv/bin/python -m ruff check vllm/plugin_api tests/plugins_tests
.venv/bin/python -m ruff format --check vllm/plugin_api tests/plugins_tests
```

如果仓库使用 pre-commit 且环境中已有模块：

```bash
.venv/bin/python -m pre_commit run --files <本次修改文件>
```

记录完整命令、exit code、passed/failed/skipped 数、耗时、skip 原因，以及未运行硬件测试的原因。不要通过裸 pip 临时安装依赖。

## 20. 官方上游审计策略

1. 审计官方 vLLM 最新代码和公开 RFC/issue/discussion，不盲目合并 main。
2. 只引用官方仓库、官方文档和官方 issue/discussion/RFC。
3. 记录 URL、版本/提交和访问日期。
4. 如果官方已有 manifest 或 extension registry，优先保持命名和版本协商可适配，但未验证前不能声称兼容。
5. vLLM-HUST 通用修改和 State-Centric/Ascend 专用修改分离。
6. 通用 manifest、bundle loader、typed control hooks、sidecar protocol 和错误模型才是潜在 upstream 内容。
7. 不创建 PR、不 commit、不 push，除非任务所有者授权。

## 21. 完成标准

当前阶段只有同时满足以下条件才算完成：

1. 新插件使用版本化 manifest；
2. API 版本协商有测试；
3. configuration schema 有测试；
4. discovery 和 dependency ordering 稳定；
5. allowlist/denylist 正确；
6. 名称冲突明确拒绝；
7. unsupported hook fail closed；
8. 静态验证尽量发生在插件 import 前；
9. crash/timeout/cancel 不破坏 host；
10. recovery 有行为测试；
11. 默认 import/startup 不自动扫描或启动 sidecar；
12. execution plan 验证 `python_ipc=false`；
13. 热路径微基准没有 Python IPC；
14. 至少两个标准插件完成端到端行为测试；
15. 不兼容插件错误包含 capability 和版本原因；
16. 文档没有将“已声明”冒充“已兼容”；
17. 所有测试均为 CPU-only；
18. 未触碰 NPU 0–3 或运行中服务；
19. 未修改 Qwen3.8/GDN/HCCL；
20. 未清理他人工作，未 commit，未 push。

## 22. 最终汇报格式

完成后按以下结构汇报：

1. **结论**：实现范围、实际行为兼容范围、默认路径开销和热路径边界。
2. **架构**：manifest、bundle、sidecar、host/runtime、plan 和 Native ABI。
3. **已接纳能力**：说明标准化重写、adapter 或直接标准插件，附行为测试。
4. **未接纳能力**：缺失 hook、热路径、平台或 ABI 原因。
5. **改动文件**：使用绝对路径逐项说明。
6. **验证结果**：精确命令、exit code、测试统计和 benchmark 数据。
7. **安全确认**：未碰 NPU/服务/禁止区域，未清理、未 commit、未 push。
8. **Git 状态**：分支、基线、`git status --short` 和 `git diff --stat`。
9. **Gap report**：已兼容、部分兼容、尚未兼容及可验证理由。
10. **下一步**：区分 vLLM-HUST 通用工作和 State-Centric Native 工作。

接管线程应从读取 `/home/shuhao/vllm-hust/AGENTS.md`、Git 状态、已有 planning files 和参考原型开始，先更新 planning files，再修改代码，并持续执行到实现、CPU 测试、微基准、文档和 gap report 均完成。
