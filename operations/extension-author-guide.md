# vLLM-HUST 扩展制作、打包、安装与发布指南

> 适用基线：vLLM-HUST Extension Manager `0.2.0.dev0`、Manifest
> `0.2-experimental`。本接口尚未冻结为稳定 v1；插件作者必须声明并测试精确的宿主
> 兼容范围，不能把“manifest 能被读取”写成“运行时已经兼容”。

本文面向准备给 vLLM-HUST 生态贡献扩展的同学。BidKV 是进程内 scheduler policy
的完整参考实现；外部 KV 服务和 Kubernetes control plane 使用不同的 Host Provider，
不能照抄 BidKV 的生命周期。

## 1. 先判断你做的是不是插件

| 形态 | 典型例子 | 应归类为 | 谁拥有生命周期 |
| --- | --- | --- | --- |
| 修改一次 vLLM 请求在 scheduler 内的选择逻辑 | BidKV | `scheduler_policy` 扩展 | vLLM 进程 |
| 把 vLLM scheduler/worker 接到外部 KV 系统 | Mooncake connector | `kv_connector` / `kv_service_adapter` | connector 由 vLLM 加载，服务由外部 operator 管理 |
| 提供传输、存储、元数据或共享 KV 服务 | Mooncake HUST | 外部系统，不是插件 | 外部 operator |
| 提供 Router、CRD、controller、autoscaler 或 Helm chart | Production Stack HUST | control-plane 系统或 `control_plane_extension` | Kubernetes/operator |
| 持续跟随官方项目的完整发行分支 | vLLM-HUST、vLLM Ascend HUST、SGLang HUST | 上游同步系统 fork，不是插件 | 对应系统维护者 |
| 只用于 benchmark、profiling、诊断或数据处理 | benchmark/profiling 仓库 | 工具，不是运行时插件 | 工具调用者 |

只有“能够作为独立制品安装，并通过明确宿主契约改变一个有限运行时行为”的能力，
才适合做插件。不要因为某个系统可以被 Manager 发现，就把系统本体称为插件。

## 2. 必须遵守的边界

1. Extension Manager 负责静态发现、校验、配置、enable intent、状态投影、冲突检查
   和向 Host Provider 委托。
2. 安装只表示 `installed + discovered`，不得自动 import 实现或改变服务行为。
3. `enable` 只保存启用意图；它不等于 workload 已经启动或健康。
4. vLLM 进程内插件由 vLLM 加载和停止。禁用后必须启动新进程才能保证回退，不承诺
   热卸载。
5. Manager 不默认启动/停止共享外部服务，不改驱动，不删 KV 数据，也不直接 apply
   生产 Kubernetes 资源。
6. 非官方扩展注册使用 `vllm_hust.extension_bundles`；第三方 Provider 使用
   `vllm_hust_ext.providers`。不要占用新的 `vllm.*` entry-point namespace。
7. 不得静默忽略未知字段、冲突或不兼容。无法证明兼容时必须 fail closed。

## 3. 推荐的插件仓库结构

以下以包名 `example-policy`、Python namespace `example_policy`、扩展 ID
`org.vllm-hust.example-policy` 为例：

```text
example-policy/
├── LICENSE
├── README.md
├── pyproject.toml
├── src/
│   └── example_policy/
│       ├── __init__.py
│       ├── policy.py
│       └── manifests/
│           └── vllm-hust-extension-v0.2.json
└── tests/
    ├── test_manifest.py
    ├── test_packaging.py
    ├── test_policy.py
    └── test_host_contract.py
```

扩展 ID 应稳定、全小写并带组织前缀；distribution 名和 Python import 名可以不同。
一旦公开发布，不要仅为美观修改扩展 ID，因为 Manager 的保存状态以它为键。

## 4. 实现一个最小进程内 policy

宿主契约决定类或函数需要实现什么，不由 manifest 自行发明。以下仅展示结构；实际方法
签名必须以所声明的宿主契约为准：

```python
from __future__ import annotations

from collections.abc import Sequence
from typing import Any


class ExamplePolicy:
    """A bounded policy implementation loaded by the vLLM host."""

    vllm_victim_selector_api_version = 1

    @classmethod
    def from_vllm_config(cls, vllm_config: object) -> "ExamplePolicy":
        return cls()

    def pick_victim(
        self,
        running: Sequence[Any],
        policy: Any,
        *,
        kv_utilization: float | None = None,
        now_s: float | None = None,
    ) -> Any:
        if not running:
            raise ValueError("running is empty, cannot pick victim")
        return running[-1]

    def emit_observability_log(self, logger: Any, scheduler_name: str) -> None:
        pass

    def export_metrics(self) -> dict[str, Any]:
        return {}
```

实现应满足：

- import 时不修改全局 registry、不 monkey-patch scheduler、不访问设备；
- 默认路径不启用扩展；
- 相同输入产生可解释、可测试的结果；
- 异常行为、超时和无候选项有明确语义；
- 不把模型权重、token、用户 prompt 或密钥写入日志；
- 需要 native/device 能力时，在 manifest 中如实声明权限和执行面。

BidKV 的现行实现可参考
[`bidkv.adapters.vllm_hust.selector`](https://github.com/vLLM-HUST/vllm-hust-bidkv/tree/feature/host-provider-v0/src/bidkv/adapters/vllm_hust)。

## 5. 编写 Manifest 0.2

文件名必须是 `vllm-hust-extension-v0.2.json`。下面是 scheduler policy 的最小完整
示例：

```json
{
  "schema_version": "0.2-experimental",
  "extension_id": "org.vllm-hust.example-policy",
  "extension_version": "0.1.0",
  "kind": "scheduler_policy",
  "host": {
    "provider": "vllm",
    "name": "vllm",
    "version_range": ">=0.23,<0.24",
    "api_range": ">=1,<2"
  },
  "runtime": {
    "type": "python",
    "process_scope": "scheduler",
    "isolation": "trusted_in_process"
  },
  "lifecycle_owner": "vllm",
  "protocols": [
    {
      "name": "vllm.scheduler.policy",
      "version_range": ">=1,<2"
    }
  ],
  "implementation": [
    {
      "type": "python_module",
      "module": "example_policy.policy",
      "object": "ExamplePolicy",
      "status": "active"
    }
  ],
  "requires_services": [],
  "components": [
    {
      "component_id": "victim-selector",
      "contracts": ["vllm.scheduler.policy.v1"],
      "execution_planes": ["scheduler"],
      "isolation": "trusted_in_process",
      "implementation_ref": "example_policy.policy:ExamplePolicy",
      "permissions": []
    }
  ],
  "activation": {
    "entry_points": [],
    "environment": {"EXAMPLE_POLICY_ENABLE": "1"},
    "additional_config": {
      "victim_selector_component": "org.vllm-hust.example-policy/victim-selector",
      "enable_utility_victim_selection": true
    }
  }
}
```

### 5.1 字段如何填写

- `kind`：领域角色。当前允许 `in_process_plugin`、`scheduler_policy`、
  `kv_connector`、`kv_service_adapter`、`control_plane_extension`、
  `runtime_bridge`。
- `host.provider`：负责解释该扩展的 Provider；首期为 `vllm`、`mooncake` 或
  `production-stack`。
- `host.version_range`：经过测试的宿主 package 版本范围。不能用一个宽范围代替
  测试证据。
- `host.api_range`：宿主扩展 API 范围；宿主没有独立 API 版本时不要伪造。
- `runtime.type`：`python`、`external_service`、`oci`、`kubernetes` 或
  `composite`。
- `runtime.process_scope`：实现真正运行的位置，如 `scheduler`、`worker`、
  `sidecar` 或 `cluster`。
- `runtime.isolation`：例如 `trusted_in_process`、`process_isolated`。
- `lifecycle_owner`：`vllm`、`host`、`external_operator`、`kubernetes` 或
  `user`。它决定谁有权启动、停止、升级和删除运行载体。
- `protocols`：扩展真正消费的协议；上游接口没有独立语义版本时，
  `version_range` 使用 `null`，不要杜撰 `1.0`。
- `implementation`：可声明 `python_entry_point`、`python_module`、
  `host_builtin`、`external_service`、`oci_image`、`helm_values`、
  `kubernetes_manifest`、`crd` 或 `controller` 等载体。
- `requires_services`：每项需写 `service_id`、`protocol`、`version_range`、
  `endpoint_config` 和可选的 `optional`。进程内纯 policy 应为空数组。
- `components[].permissions`：只声明实际需要的最小集合：`device_access`、
  `filesystem_read`、`filesystem_write`、`ipc`、`network_egress`、
  `shared_memory`、`subprocess`。空权限写 `[]`。
- `activation`：只放宿主启动所需的 entry point、环境变量和
  `additional_config`。不要在这里放密钥；密钥应由部署环境注入。

`additional_config` 只对应 vLLM 的 `--additional-config`。如果扩展需要
`--speculative-config`，不要把字段塞进 `additional_config`；应在用户配置文件中
使用 Provider 支持的动态启动项：

```json
{
  "launch_options": {
    "speculative_config": {
      "method": "eagle3",
      "model": "/models/draft",
      "draft_context_policy": "diffspec"
    }
  }
}
```

模型路径、端点、密钥等部署值属于用户配置，不属于可发布的静态 manifest。

### 5.2 Manifest 的关键一致性条件

- `extension_id` 必须与 entry-point 注册名完全相同；
- `extension_version` 应与 distribution 版本同步；
- `implementation_ref` 必须能指向实际对象；
- 一个 component 的 ID 在同一 manifest 内必须唯一；
- contracts、执行面、权限和 runtime 位置必须与代码行为一致；
- 声明外部服务不等于把服务生命周期交给 Manager；
- 不得同时交付两个会争用同一 vLLM `--kv-transfer-config` 的启用方案。

## 6. 配置 Python 包

`pyproject.toml` 的核心部分如下：

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "example-policy"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
example_policy = ["manifests/*.json"]

[project.entry-points."vllm_hust.extension_bundles"]
"org.vllm-hust.example-policy" = "example_policy.manifests"
```

这里的 entry point 是静态 manifest 目录定位符，不是“安装后立即 import 并执行”的
回调。Manager 会从 distribution metadata 定位 JSON 文件并在实现 import 前校验。

如果要编写第三方 Host Provider，工厂只能注册在：

```toml
[project.entry-points."vllm_hust_ext.providers"]
example_host = "example_provider:provider_factory"
```

Provider 是高级扩展点。普通 vLLM policy 不需要编写 Provider。

## 7. 插件作者的本地开发流程

建议每次从干净虚拟环境开始：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip build
python -m pip install -e '.[dev]'
python -m pytest -q
python -m ruff check .
```

在 Windows PowerShell 中激活命令为：

```powershell
.venv\Scripts\Activate.ps1
```

不要只做 editable install。正式打包前必须验证 wheel：

```bash
python -m build
python -m pip install --force-reinstall dist/example_policy-0.1.0-py3-none-any.whl
python -m pip show -f example-policy
```

也可用 Python 检查 wheel 是否包含 manifest：

```bash
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile

wheel = next(Path("dist").glob("*.whl"))
with ZipFile(wheel) as archive:
    names = archive.namelist()
assert any(name.endswith("manifests/vllm-hust-extension-v0.2.json") for name in names)
print(wheel, "contains the manifest")
PY
```

## 8. 安装 Manager 和插件

在 Manager 尚未正式发布 alpha 时，从经过审核的仓库 revision 安装：

```bash
python -m pip install 'git+https://github.com/vLLM-HUST/extension-manager.git@COMMIT_SHA'
python -m pip install ./dist/example_policy-0.1.0-py3-none-any.whl
```

正式发布后，目标体验是：

```bash
python -m pip install vllm-hust-ext
python -m pip install example-policy
```

验证安装和静态发现：

```bash
vllm-hust-ext extension list
vllm-hust-ext extension inspect org.vllm-hust.example-policy
vllm-hust-ext extension validate org.vllm-hust.example-policy
vllm-hust-ext extension status org.vllm-hust.example-policy
```

预期行为：

- `list` 中只出现一次扩展 ID；
- `inspect/validate` 能显示 manifest，且不会 import `example_policy.policy`；
- 刚安装时为 disabled；
- 宿主或 API 不兼容时显示 `incompatible`，不能靠 enable 绕过。

可用 `VLLM_HUST_EXT_CONFIG` 指向隔离配置，避免开发测试污染个人状态：

```bash
export VLLM_HUST_EXT_CONFIG="$PWD/.tmp/manager-config.json"
```

## 9. 配置、启用和启动

需要 Provider 配置时，先写 JSON 对象，例如：

```json
{"threshold": 0.95, "mode": "conservative"}
```

对于 DiffSpec 这类 speculative-decoding 扩展，配置文件应包含完整
`launch_options.speculative_config`。Manager 会把它安全合并为
`--speculative-config`，若用户命令已经包含不同值则 fail closed。普通
`vllm.general_plugins` 扩展不会被伪装成 vLLM-HUST typed host manifest；只有明确
声明 `host.api_range` 的扩展才生成宿主原生 manifest。

然后执行：

```bash
vllm-hust-ext extension configure org.vllm-hust.example-policy \
  --file ./example-policy-config.json
vllm-hust-ext extension check org.vllm-hust.example-policy
vllm-hust-ext extension plan org.vllm-hust.example-policy
vllm-hust-ext extension enable org.vllm-hust.example-policy
vllm-hust-ext run --dry-run -- vllm serve MODEL
```

必须先审阅 dry-run 输出中的最终命令、环境变量、`additional_config`、宿主原生
manifest，以及不兼容、冲突或未验证警告。确认无误后启动：

```bash
vllm-hust-ext run -- vllm serve MODEL --host 0.0.0.0 --port 8000
```

不要同时手工设置 Manager 拥有的 `VLLM_EXTENSION_MANIFESTS` 或
`VLLM_EXTENSION_BUNDLES`。Manager 会拒绝双重所有权，避免加载两个不同实现。

## 10. 运行中验证

“进程启动成功”不是插件验收。至少要证明：

1. 日志或结构化证据显示目标 component 被宿主实际加载；
2. 请求触发了插件代码，而不是仅解析 manifest；
3. 插件行为与内置 baseline 可区分；
4. 请求仍能完成，错误码和输出契约正确；
5. 状态能够区分 `installed`、`discovered`、`compatible`、`configured`、
   `enabled`、`reachable`、`healthy`、`degraded`、`incompatible`；
6. 不兼容、重复注册、缺失服务和配置冲突会 fail closed；
7. 性能声明使用相同模型、请求、并发、输入输出长度、硬件、版本和启动参数的
   matched baseline。

对 scheduler/KV 类插件，还要覆盖 KV 压力、无候选、抢占、请求完成和资源回收。
对 native/device 插件，CPU smoke 不能替代目标硬件测试。

## 11. 停止、禁用、回退和卸载

Manager 不拥有 vLLM 服务进程。前台进程用 `Ctrl-C` 停止；systemd、容器或
Kubernetes 部署由相应 operator 停止。不要把 `extension disable` 当作 stop。

标准回退和卸载顺序是：

```bash
vllm-hust-ext extension disable org.vllm-hust.example-policy
# 停止旧进程
vllm-hust-ext run --dry-run -- vllm serve MODEL
vllm-hust-ext run -- vllm serve MODEL
# 验证新进程已恢复内置实现后：
vllm-hust-ext extension forget org.vllm-hust.example-policy
python -m pip uninstall example-policy
vllm-hust-ext extension list
```

`forget` 只删除 Manager 保存的配置和 enable intent。它不会停止进程、删除外部服务、
清理 KV 数据或卸载 Python 包。启用状态下 `forget` 会被拒绝。

## 12. 外部 KV 系统和 connector 的特别规则

外部 KV 系统本体与 vLLM connector 必须拆开建模：

```text
external KV system
  -> scheduler connector
  -> worker connector
  -> optional telemetry/API adapter
  -> vLLM-owned connector contract
```

外部服务 manifest 应使用 `lifecycle_owner=external_operator`，并在
`requires_services` 中声明 endpoint 配置键。Provider 可执行
`plan/render/check`，但不得默认启动、停止、升级服务或删除 KV 数据。

首期 Mooncake 应复用官方 `MooncakeConnector` / `MooncakeStoreConnector`，不要为了
统一外观维护大 fork 或动态 C++ 插件管理器。服务不可达应投影为 degraded，并保留
enable intent，服务恢复后不应要求重装 Manager。

## 13. Control plane / Kubernetes 扩展的特别规则

Helm、CRD、controller、Router、autoscaler 和 OCI 是控制面载体，不是 Python
进程内插件。Provider 只负责生成计划、渲染输入、server dry-run 和检查证据：

- `apply`、upgrade、rollback、uninstall 由 Kubernetes/operator 明确执行；
- 生成计划中这些 operator-owned mutation 必须保持显式 `null`；
- 必须检查 controller 与 HPA 是否争用同一字段；
- mock backend 只能算 smoke，不能冒充真实模型 Router 健康证据；
- 集群不可达、权限不足、rollout 不完整必须进入 degraded/incompatible。

## 14. 必需测试矩阵

### 14.1 单元与静态测试

- manifest 字段、ID、版本范围和枚举；
- distribution entry point 与 `extension_id` 一致；
- wheel/sdist 都包含 manifest；
- discovery 不 import 实现模块；
- duplicate registration 被拒绝；
- implementation ref 存在；
- 配置文件必须是 JSON object；
- 冲突环境变量和 `additional_config` 被拒绝；
- 默认安装路径不改变宿主行为。

### 14.2 宿主契约测试

- 支持范围内的宿主/API/协议通过；
- 范围外版本 fail closed；
- 真实 hook 被调用；
- exception、timeout、空输入和取消路径明确；
- disable + 新进程恢复内置实现；
- legacy adapter 与 typed path 不能同时启用。

### 14.3 干净安装测试

```bash
python3 -m venv /tmp/example-policy-clean
. /tmp/example-policy-clean/bin/activate
python -m pip install MANAGER_WHEEL PLUGIN_WHEEL
vllm-hust-ext extension validate org.vllm-hust.example-policy
vllm-hust-ext extension enable org.vllm-hust.example-policy
vllm-hust-ext run --dry-run -- vllm serve MODEL
vllm-hust-ext extension disable org.vllm-hust.example-policy
vllm-hust-ext extension forget org.vllm-hust.example-policy
python -m pip uninstall -y example-policy
```

112/91 等目标宿主验收必须使用相同 pushed commit 或相同 wheel 哈希，并记录 Python、
宿主、驱动/运行时、模型、命令、退出码和证据路径。

## 15. CI 最低门禁

```yaml
name: plugin
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pip install --upgrade pip build
      - run: python -m pip install -e '.[dev]'
      - run: python -m ruff check .
      - run: python -m pytest -q
      - run: python -m build
```

不要维护 self-hosted runner。必须依赖 NPU/真实集群的验收按需在授权机器运行，保存
外部证据并把精确 commit/wheel hash 回填到支持矩阵。

## 16. 发布到 TestPyPI/PyPI

发布前确认版本号、manifest 版本和 changelog 一致；tag 指向已验收 commit；wheel
和 sdist 都通过干净环境验证；README 写明兼容范围、实验状态、启停和回滚；仓库中
没有 token、`.env`、内部地址或测试凭据；性能结论具有 matched evidence。

```bash
python -m build
python -m pip install twine
python -m twine check dist/*

export TWINE_USERNAME=__token__
export TWINE_PASSWORD="$TEST_PYPI_TOKEN"
python -m twine upload --repository testpypi dist/*
```

从 TestPyPI 安装精确版本并重复 discovery、enable、dry-run、disable、forget、uninstall
门禁。通过后才发布 PyPI：

```bash
export TWINE_PASSWORD="$PYPI_TOKEN"
python -m twine upload dist/*
```

不要把 token 写进命令历史、仓库、日志或 CI YAML；使用 CI secret 或临时环境变量。
PyPI 文件不可覆盖，发布错误必须增加新版本或按发布策略 yank。

## 17. PR 验收清单

- [ ] 它为什么是插件，而不是系统 fork、外部服务、connector、control plane 或工具？
- [ ] `kind`、`host`、`runtime`、`lifecycle_owner` 是否真实？
- [ ] 宿主/API/协议兼容范围由哪些测试证明？
- [ ] 安装是否完全无副作用？
- [ ] discovery 是否不 import 实现？
- [ ] 权限是否最小化？
- [ ] 配置冲突和重复注册是否 fail closed？
- [ ] enable 后是否证明真实 hook 被调用？
- [ ] disable + 新进程是否证明回退？
- [ ] forget + pip uninstall 是否无残留？
- [ ] wheel/sdist 是否包含 manifest？
- [ ] 是否在干净 venv 和目标宿主验证？
- [ ] 性能声明是否使用 matched baseline？
- [ ] 是否更新支持矩阵、网站 registry 和用户文档？

## 18. 常见故障

### `extension list` 看不到插件

检查 distribution 是否安装在运行 CLI 的同一 Python 环境、entry-point group 是否为
`vllm_hust.extension_bundles`、注册名是否与 `extension_id` 相同，以及 wheel 是否包含
`manifests/vllm-hust-extension-v0.2.json`。

### `validate` 报 manifest 数量不是 1

每个注册目录必须恰好包含一个受支持文件名的 manifest。删除旧 v1 manifest或把
不同扩展拆成不同注册目录。

### `status` 为 incompatible

不要扩大版本范围绕过。核对实际安装的宿主 distribution、版本、API 和协议；补齐真实
契约测试后再修改范围。

### `run` 拒绝 scheduler policy

进程内 scheduler policy 必须有明确兼容证据。官方 vLLM 当前不等同于带
`vllm.scheduler.policy.v1` 的 vLLM-HUST 0.23。

### disable 后行为没有变化

旧进程已经加载了实现。停止旧进程并用 Manager 启动新进程；当前设计不承诺热卸载。

### uninstall 后 Manager 仍保存 enabled intent

正确顺序是 disable、回退验证、forget、pip uninstall。若先卸载，重新安装同 ID 的
distribution 前必须检查隔离配置文件，避免恢复陈旧意图。

## 19. 参考实现

- [Extension Manager](https://github.com/vLLM-HUST/extension-manager)
- [BidKV 插件实现](https://github.com/vLLM-HUST/vllm-hust-bidkv)
- [DiffSpec 插件实现](https://github.com/vLLM-HUST/vllm-ascend-hust-diffspec)
- [Manifest 0.2 说明](https://github.com/vLLM-HUST/extension-manager/blob/main/docs/manifest-0.2-experimental.md)
- [Host Provider 架构](extension-manager-host-provider-architecture.md)
- [支持矩阵](extension-manager-support-matrix-20260901.md)
- [验收记录](extension-manager-acceptance-20260901.md)

如果新扩展无法明确填写 `kind`、`host`、`runtime` 和 `lifecycle_owner`，先暂停编码并
提交架构讨论；这通常意味着系统边界还没有理清，而不是 manifest 字段不够多。
