# 插件打包、发布与安装指南

本文介绍 vLLM-HUST Extension Bundle 插件从项目配置、构建、发布到安装使用的流程。文中使用 BidKV 作为示例：

| 项目 | BidKV 示例 |
|---|---|
| PyPI 项目名 | `bidkv` |
| Python 模块名 | `bidkv` |
| Bundle ID（0.2 中为 `extension_id`） | `org.vllm-hust.bidkv` |
| Component ID | `victim-selector` |
| 完整组件 ID | `org.vllm-hust.bidkv/victim-selector` |
| contract | `vllm.scheduler.policy.v1` |
| execution plane | `scheduler` |

制作其他插件时，把示例中的名称换成自己项目的值即可。

插件由 [vLLM-HUST Extension Manager](https://github.com/vLLM-HUST/extension-manager)（命令 `vllm-hust-ext`）统一管理发现、准入、启用与启动渲染，manifest 使用 `0.2-experimental` schema。

> `0.2-experimental` 尚非稳定 API，端到端验收通过前不发布 alpha 包。

## 1. 项目结构

一个最小的插件项目可以按下面组织：

```text
vllm-hust-bidkv/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── bidkv/
│       ├── __init__.py
│       ├── _version.py
│       ├── adapters/
│       │   └── vllm_hust/
│       │       └── selector.py
│       └── manifests/
│           ├── __init__.py
│           └── vllm-hust-extension-v0.2.json
└── tests/
```

`manifests/__init__.py` 留空即可，用于让 entry point 指向的 `bidkv.manifests` 成为可导入目录。manifest 必须打进 wheel，否则 `vllm-hust-ext` 无法发现扩展。

## 2. 配置发行包

BidKV 使用 setuptools 构建，`pyproject.toml` 中与打包有关的配置如下：

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "bidkv"
dynamic = ["version"]
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.10"
dependencies = []

[tool.setuptools.dynamic]
version = {attr = "bidkv._version.__version__"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
bidkv = ["manifests/*.json"]

[project.entry-points."vllm_hust.extension_bundles"]
"org.vllm-hust.bidkv" = "bidkv.manifests"
```

制作自己的插件时，需要替换项目名、Python 模块名和扩展 ID：

```toml
[project]
name = "<PyPI 项目名>"

[tool.setuptools.dynamic]
version = {attr = "<Python 模块>._version.__version__"}

[tool.setuptools.package-data]
<Python 模块> = ["manifests/*.json"]

[project.entry-points."vllm_hust.extension_bundles"]
"<extension_id>" = "<Python 模块>.manifests"
```

`vllm_hust.extension_bundles` 是 `vllm-hust-ext` 的发现入口：entry point name 为 `extension_id`，value 为包含 manifest 的模块目录。发现阶段只读发行元数据和 manifest，不导入实现。

BidKV 不再注册 legacy `vllm.victim_selector` entry point；`VLLM_EXTENSION_MANIFESTS`/`VLLM_EXTENSION_BUNDLES` 由 `vllm-hust-ext run` 自动注入，无需手工设置。

## 3. 编写 manifest

BidKV 的 manifest 位于 `src/bidkv/manifests/vllm-hust-extension-v0.2.json`：

```json
{
  "schema_version": "0.2-experimental",
  "extension_id": "org.vllm-hust.bidkv",
  "extension_version": "0.1.1",
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
    {"name": "vllm.scheduler.policy", "version_range": ">=1,<2"}
  ],
  "implementation": [
    {
      "type": "python_module",
      "module": "bidkv.adapters.vllm_hust.selector",
      "object": "BidkvVictimSelector",
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
      "implementation_ref": "bidkv.adapters.vllm_hust.selector:BidkvVictimSelector",
      "permissions": []
    }
  ],
  "activation": {
    "entry_points": [],
    "environment": {
      "BIDKV_UTILITY_ENABLE": "1",
      "BIDKV_UTILITY_STRATEGY": "bidkv"
    },
    "additional_config": {
      "victim_selector_component": "org.vllm-hust.bidkv/victim-selector",
      "enable_utility_victim_selection": true,
      "utility_strategy": "bidkv"
    }
  }
}
```

| 字段 | 说明 |
|---|---|
| `schema_version` | `0.2-experimental`，当前实验性 schema |
| `extension_id` | 扩展的稳定标识 |
| `extension_version` | 扩展版本，通常与 Python 发行版本一致 |
| `kind` | 域角色，如 `scheduler_policy`、`kv_service_adapter`、`control_plane_extension`、`runtime_bridge` |
| `host` | Provider 身份与兼容范围：`provider`、`name`、`version_range`、可选 `api_range` |
| `runtime` | 运行载体：`type`（`python`/`external_service`/`oci`/`kubernetes`/`composite`）、`process_scope`、`isolation` |
| `lifecycle_owner` | 有权变更运行时生命周期的系统/操作者（`vllm`/`host`/`external_operator`/`kubernetes`/`user`） |
| `protocols` | 显式协议兼容范围，如 `vllm.scheduler.policy >=1,<2` |
| `implementation` | 一个或多个 carrier，BidKV 用 `python_module`（`module`/`object`/`status`） |
| `requires_services` | 依赖的外部服务：`service_id`、`protocol`、`version_range`、`endpoint_config`、`optional` |
| `components` | 可选 typed 组件，沿用 v1 组件结构，用于生成宿主 native v1 manifest |
| `activation` | 启动激活声明：`entry_points`、`environment`、`additional_config` |

`implementation.status` 决定能否启用：`active` 可 `enable`；`import_only`/`legacy_unregistered` 仅可 `inspect`（`activation_ready=false`）。

`components` 由 vLLM Provider 转成宿主原生 v1 manifest 供 vLLM 启动时读取；`host.version_range`/`host.api_range` 为兼容性声明，不替代依赖管理。

contract、execution plane、isolation、permissions 按插件实际行为填写，不能照搬 BidKV 的 `scheduler`。

## 4. 实现组件

实现类需要满足 manifest 中声明的 contract。BidKV 的 victim selector 主要提供以下接口：

```python
class BidkvVictimSelector:
    vllm_victim_selector_api_version = 1

    @classmethod
    def from_vllm_config(cls, vllm_config):
        ...

    def pick_victim(
        self,
        running,
        policy,
        *,
        kv_utilization=None,
        now_s=None,
    ):
        ...

    def emit_observability_log(self, logger, scheduler_name):
        ...

    def export_metrics(self):
        ...
```

以上成员是 `VictimSelector` runtime-checkable protocol 的必需接口。`pick_victim` 从非空 `running` 返回一个 `Request`；`kv_utilization` 与 `now_s` 可为 `None`。对应 manifest 的 `implementation`：`status: "active"` 的 `python_module` carrier。

静态准入阶段不导入实现。模块导入时不得启动线程、联网、访问设备或修改全局状态；配置校验放在 `from_vllm_config`，不合法直接报错。

## 5. 与 vLLM-HUST 主仓库适配

插件运行在 vLLM-HUST 进程中，由 `vllm-hust-ext` 统一管理，无需手工设置宿主环境变量。

- **分层**：Core 负责发现、manifest 校验、兼容性证据、持久化配置、启用意图与冲突拒绝；Provider 负责渲染启动配置。扩展注册在 `vllm_hust.extension_bundles`，Provider 注册在 `vllm_hust_ext.providers`。
- **状态**：基于证据投影：`installed`、`discovered`、`compatible`、`configured`、`enabled`、`reachable`、`healthy`、`degraded`、`incompatible`。
- **启动**：`vllm-hust-ext run -- vllm serve MODEL` 读取已启用扩展，校验兼容性与 `requires_services` 健康，合并 activation 的 `environment`/`additional_config`，把 0.2 manifest 转成宿主原生 v1 manifest，注入 `VLLM_EXTENSION_MANIFESTS`/`VLLM_EXTENSION_BUNDLES`，再执行命令；不兼容或未健康时 fail closed。
- **宿主 seam**：宿主按提交 `5c994cdc` 读取原生 v1 manifest，`get_victim_selector()` 按 `vllm.scheduler.policy.v1` + `scheduler` plane 挑选组件，校验 API version `1` 与 `VictimSelector` protocol。

BidKV 经 pinned vLLM-HUST 0.23 宿主、typed `vllm.scheduler.policy.v1` contract 支持；不适用于官方 vLLM。

### 版本与依赖

`host.version_range`/`host.api_range` 为兼容性声明。发布时记录并测试明确的 vLLM-HUST 版本/commit 与运行环境；第三方依赖写入 `[project].dependencies`。

| 插件版本 | 已验证的 vLLM-HUST 版本或 commit | host version 范围 | host API 范围 | contract | 验证环境 |
|---|---|---|---|---|---|
| `0.1.1` | `<填写实际版本或 commit>` | `>=0.23,<0.24` | `>=1,<2` | `vllm.scheduler.policy.v1` | `<Python、设备、镜像>` |

### 开发验证

1. 核对 `vllm/plugins/contracts.py`、`vllm/plugins/startup.py`、`vllm/v1/core/sched/victim_selector.py`，接口差异收敛在 `adapters/vllm_hust/`。
2. 同环境安装 vLLM-HUST、`vllm-hust-ext` 与插件 wheel。
3. 依次执行 `extension check`/`status`/`plan`/`render` 与 `run --dry-run`，再启动服务验证 provenance 日志与抢占行为。
4. CI 覆盖最低与最新支持版本，并与 baseline 对比功能/性能。

## 6. 版本号

BidKV 从 `src/bidkv/_version.py` 读取发行版本：

```python
__version__ = "0.1.1"
```

同一次发布中，Python 发行版本和 manifest 的 `extension_version` 保持一致。PyPI 不允许覆盖同一版本下已经上传的文件，修改源码后需要增加版本号再重新构建。

## 7. 构建 wheel 和 sdist

在项目根目录记录本次发布对应的 commit，并检查工作树：

```bash
git status --short
git rev-parse HEAD
```

清理旧产物并构建：

```bash
rm -rf dist
uv build --no-sources --out-dir dist
```

PowerShell 使用：

```powershell
if (Test-Path -LiteralPath dist) {
    Remove-Item -LiteralPath dist -Recurse -Force
}
uv build --no-sources --out-dir dist
```

`--no-sources` 会忽略本地 `tool.uv.sources` 覆盖，更接近普通用户的构建环境。

以 `bidkv==0.1.1` 为例，`dist/` 中会生成：

```text
dist/
├── bidkv-0.1.1-py3-none-any.whl
└── bidkv-0.1.1.tar.gz
```

纯 Python 插件通常生成 `py3-none-any` wheel。包含编译扩展的项目需要为支持的 Python ABI 和平台分别构建 wheel。

## 8. 检查构建产物

列出 wheel 的内容：

```bash
python -m zipfile -l dist/bidkv-0.1.1-py3-none-any.whl
```

BidKV wheel 中至少应有：

```text
bidkv/__init__.py
bidkv/_version.py
bidkv/manifests/__init__.py
bidkv/manifests/vllm-hust-extension-v0.2.json
bidkv-0.1.1.dist-info/METADATA
bidkv-0.1.1.dist-info/RECORD
```

`entry_points.txt` 应包含 `vllm_hust.extension_bundles` 入口：

```bash
python -c 'import zipfile; p="dist/bidkv-0.1.1-py3-none-any.whl"; z=zipfile.ZipFile(p); n=next(x for x in z.namelist() if x.endswith(".dist-info/entry_points.txt")); print(z.read(n).decode())'
```

```ini
[vllm_hust.extension_bundles]
org.vllm-hust.bidkv = bidkv.manifests
```

然后把 wheel 安装到临时环境：

```bash
uv venv .release-smoke
uv pip install --python .release-smoke/bin/python \
  --no-deps dist/bidkv-0.1.1-py3-none-any.whl
.release-smoke/bin/python -c \
  'from importlib.metadata import version; print(version("bidkv"))'
```

PowerShell：

```powershell
uv venv .release-smoke
uv pip install --python .release-smoke\Scripts\python.exe `
  --no-deps dist\bidkv-0.1.1-py3-none-any.whl
.\.release-smoke\Scripts\python.exe -c `
  'from importlib.metadata import version; print(version("bidkv"))'
```

临时环境装有 vLLM-HUST 与 `vllm-hust-ext` 时，验证发现结果：

```bash
.release-smoke/bin/vllm-hust-ext extension list --json
.release-smoke/bin/vllm-hust-ext extension inspect org.vllm-hust.bidkv
```

预期：`list` 列出 `org.vllm-hust.bidkv`；`inspect` 显示 `activation_ready=true`、`kind=scheduler_policy`。

## 9. 发布到 PyPI

### 项目和权限

首次发布前，需要确定 PyPI 项目名并准备上传权限。BidKV 的 PyPI 项目名是 `bidkv`，项目归属 `intellistream` Organization。

团队发布可以使用组织或项目管理页面提供的 API Token。只发布一个项目时，使用仅授权该项目的 Token；多项目发布流水线才需要更大的授权范围。

Token 保存在 CI Secret 或密码库中，不写入仓库、`pyproject.toml`、构建脚本和日志。PyPI Token 以 `pypi-` 开头；上传用户名为 `__token__`。设置 `UV_PUBLISH_TOKEN` 后，`uv` 会处理用户名。

### 上传

在发布环境中从安全位置读取 Token：

```bash
export UV_PUBLISH_TOKEN='<从 CI Secret 或密码库读取>'
```

上传 BidKV 的 wheel 和 sdist：

```bash
uv publish \
  --check-url https://pypi.org/simple \
  dist/bidkv-0.1.1-py3-none-any.whl \
  dist/bidkv-0.1.1.tar.gz
```

发布自己的插件时替换两个文件名。正式发布建议显式列出文件，避免把 `dist/` 中残留的其他版本一起上传。

`--check-url` 用于检查索引中是否已有相同文件。如果一次发布只上传了部分文件，可以在本地产物没有变化的前提下重试；如果远端同版本文件与本地内容不同，应改用新版本号。

发布结束后清理当前 shell 中的 Token：

```bash
unset UV_PUBLISH_TOKEN
```

PowerShell：

```powershell
Remove-Item Env:UV_PUBLISH_TOKEN
```

### CI 示例

下面以 GitHub Actions 为例，Token 保存在 `PYPI_TOKEN` Secret 中：

```yaml
- name: Build distributions
  run: uv build --no-sources --out-dir dist

- name: Publish package
  env:
    UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
  run: >-
    uv publish
    --check-url https://pypi.org/simple
    dist/bidkv-0.1.1-py3-none-any.whl
    dist/bidkv-0.1.1.tar.gz
```

发布 job 一般只允许受保护的 tag 或 release 分支触发，并确保构建、测试和上传使用同一个 commit。版本号可以从项目元数据读取，避免长期写死在 YAML 中。

## 10. 从 PyPI 安装

用户按 PyPI 项目名安装插件。BidKV 的安装命令是：

```bash
python -m pip install "bidkv==0.1.1"
```

使用 uv：

```bash
uv pip install --python /path/to/vllm-env/bin/python "bidkv==0.1.1"
```

同时安装 Extension Manager（与 `vllm` 同一环境）：

```bash
python -m pip install "vllm-hust-ext"
```

插件和 manager 都需要安装到运行 `vllm` 命令的同一个 Python 环境：

```bash
command -v python
command -v vllm
command -v vllm-hust-ext
python -c 'import sys; print(sys.executable)'
python -m pip show bidkv vllm-hust-ext
```

发布后还要从正式 PyPI 做一次无缓存安装：

```bash
uv venv .pypi-smoke
uv pip install --python .pypi-smoke/bin/python \
  --no-cache --refresh-package bidkv "bidkv==0.1.1"
.pypi-smoke/bin/python -c \
  'from importlib.metadata import version; assert version("bidkv") == "0.1.1"'
```

安装后确认 `vllm-hust-ext` 能发现扩展：

```bash
vllm-hust-ext extension list
vllm-hust-ext extension status org.vllm-hust.bidkv
```

以上仅证明扩展可被发现；启用见下一节。

## 11. 启用插件

安装只让扩展可被发现；启用是显式动作，存入 `vllm-hust-ext` 用户配置（平台目录 `vllm-hust-ext/config.json`，可用 `VLLM_HUST_EXT_CONFIG` 覆盖）。

```bash
vllm-hust-ext extension list
vllm-hust-ext extension status org.vllm-hust.bidkv
vllm-hust-ext extension check org.vllm-hust.bidkv

vllm-hust-ext extension enable org.vllm-hust.bidkv
vllm-hust-ext run -- vllm serve meta-llama/Llama-3.1-8B-Instruct
```

`run` 合并 activation 的 `additional_config` 与 `environment`，生成宿主原生 v1 manifest 并注入 `VLLM_EXTENSION_MANIFESTS`/`VLLM_EXTENSION_BUNDLES`，再执行命令；不兼容或未健康时 fail closed。

`--dry-run` 只预览注入结果，不启动：

```bash
vllm-hust-ext run --dry-run -- vllm serve meta-llama/Llama-3.1-8B-Instruct
```

BidKV 的默认业务开关（`enable_utility_victim_selection=true`、`utility_strategy="bidkv"`）已写入 manifest 的 `activation.additional_config`，`run` 会自动合并；`utility_kv_gate` 等额外调参仍通过 `--additional-config` 传入，`run` 合并时冲突即报错：

```bash
vllm-hust-ext run -- vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --additional-config '{
    "utility_kv_gate": 0.95
  }'
```

启动日志应出现：

```text
Extension startup snapshot: admitted_bundles=('org.vllm-hust.bidkv',) disabled_bundles=() admitted_components=('org.vllm-hust.bidkv/victim-selector',)
Loaded typed victim selector component=org.vllm-hust.bidkv/victim-selector source=... api_version=1
```

`check`/`inspect` 不导入实现；出现 `Loaded typed victim selector` 才表示实现已加载。健康检查：

```bash
curl --fail http://127.0.0.1:8000/health
```

功能/性能需与 baseline 对比验收。

## 12. 升级、停用和卸载

升级（先停用相关 vLLM 实例）：

```bash
python -m pip install --no-cache-dir --upgrade "bidkv==<新版本>"
vllm-hust-ext extension check org.vllm-hust.bidkv
```

升级后必须启动新进程；回退：

```bash
python -m pip install --no-cache-dir --force-reinstall "bidkv==0.1.1"
```

停用与清除意图：

```bash
vllm-hust-ext extension disable org.vllm-hust.bidkv
vllm-hust-ext extension forget org.vllm-hust.bidkv
```

`disable` 移除启用意图；`forget` 删除 manager 配置与意图（须先 `disable`），不停止共享服务、不清 KV、不删 K8s 资源。

卸载：

```bash
python -m pip uninstall bidkv
python -c 'import importlib.util; assert importlib.util.find_spec("bidkv") is None'
```

卸载前先 `disable`/`forget`，否则 `run` 会因找不到已启用扩展而 fail closed。

## 13. 常见问题

### wheel 中没有 manifest

检查 `pyproject.toml` 中的 package data，清理 `dist/` 后重新构建：

```toml
[tool.setuptools.package-data]
bidkv = ["manifests/*.json"]
```

### `extension list` 找不到扩展

常见原因有：

- 插件与 `vllm`/`vllm-hust-ext` 安装在不同的 Python 环境；
- wheel 缺少 manifest 或 `manifests/__init__.py`；
- `pyproject.toml` 缺少 `[project.entry-points."vllm_hust.extension_bundles"]`，或 entry point name 与 manifest 的 `extension_id` 不一致；
- entry point value 没有指向包含 manifest 的模块目录。

### `extension enable` 报 `activation_ready=false`

`implementation` 的 Python carrier `status` 不是 `active`（如 `import_only`/`legacy_unregistered`）。声明 `status: "active"` 后可 `enable`。

### `run` 拒绝启动

常见原因有：

- 扩展不兼容（`host.version_range`/`host.api_range` 不匹配当前宿主）；
- 非可选 `requires_services` 未健康；
- `trusted_in_process` 的 vLLM 扩展未通过兼容性检查；
- 已在环境中手工设置了 `VLLM_EXTENSION_MANIFESTS`/`VLLM_EXTENSION_BUNDLES`（这两个变量由 manager 拥有）。

### 兼容性检查报 host 不兼容

插件声明的 `host.api_range` 与当前 vLLM-HUST 不匹配。应升级插件、切换到兼容的 vLLM-HUST，或发布声明正确兼容范围的新版本。

### PyPI 返回 `403`

检查 Token 是否完整、是否已撤销、是否有目标项目的上传权限，以及环境变量中是否带有换行或空格。PyPI 与 TestPyPI 使用不同的 Token。

### PyPI 提示文件已经存在

同一版本的文件不能覆盖。确认远端内容，增加版本号后重新构建和上传。

### 安装后插件行为没有变化

先确认扩展已启用且会被启动：

```bash
vllm-hust-ext extension status org.vllm-hust.bidkv
vllm-hust-ext run --dry-run -- vllm serve meta-llama/Llama-3.1-8B-Instruct
```

`pip show bidkv` 只能说明包已安装，不能说明运行中的服务已经启用 BidKV。检查日志中是否出现 `Loaded typed victim selector component=org.vllm-hust.bidkv/victim-selector`。

## 14. 检查表

### 插件配置

- [ ] PyPI 项目名和 Python 模块名已经确定。
- [ ] `extension_id` 和 Component ID 唯一且稳定。
- [ ] `kind`、contract、execution plane、isolation 和 permissions 与实现一致。
- [ ] manifest 已加入 package data，且 `manifests/__init__.py` 存在。
- [ ] 已注册 `[project.entry-points."vllm_hust.extension_bundles"]`，entry point name 等于 `extension_id`。
- [ ] `implementation` 的 Python carrier 使用可导入的 `module`/`object`，并声明 `status: "active"`。
- [ ] 实现声明 API version `1`，并完整实现 `VictimSelector` protocol。
- [ ] 发行版本与 `extension_version` 一致。
- [ ] 已记录并验证目标 vLLM-HUST 版本或 commit、`host.version_range`、`host.api_range`、contract 和运行环境。
- [ ] 主仓库的最低支持版本与最新支持版本均已完成插件集成测试。

### 构建与发布

- [ ] 测试通过，发布 commit 已记录。
- [ ] `dist/` 中只有本次发布的 wheel 和 sdist。
- [ ] wheel 包含 manifest、`manifests/__init__.py`、发行元数据和 `vllm_hust.extension_bundles` entry point。
- [ ] wheel 的隔离安装测试通过，且 `vllm-hust-ext extension list` 能发现扩展。
- [ ] API Token 的权限范围符合发布需要。
- [ ] PyPI 上传成功，文件名和哈希已记录。

### 安装与使用

- [ ] 已从正式 PyPI 无缓存安装，并安装 `vllm-hust-ext`。
- [ ] 安装版本与发布版本一致。
- [ ] `extension check` 显示兼容，`inspect` 显示 `activation_ready=true`。
- [ ] 已执行 `extension enable`。
- [ ] `run --dry-run` 预览的 native manifest、环境变量和 additional_config 正确。
- [ ] 启动日志显示 typed victim selector 已物化。
- [ ] 服务完成健康检查。
- [ ] 功能或性能效果经过单独验收。

## 参考资料

- [vLLM-HUST Extension Manager](https://github.com/vLLM-HUST/extension-manager)
- [Extension Manifest 0.2 — experimental](https://github.com/vLLM-HUST/extension-manager/blob/main/docs/manifest-0.2-experimental.md)
- [Core and Host Provider architecture](https://github.com/vLLM-HUST/extension-manager/blob/main/docs/architecture.md)
- [BidKV typed scheduler-policy 适配提交 `5c994cdc`](https://github.com/vLLM-HUST/vllm-hust/commit/5c994cdc029dfebe318ca745a39920473033038b)
- [vLLM-HUST 核心运行时仓库](https://github.com/vLLM-HUST/vllm-hust)
- [PyPI Organization Accounts](https://docs.pypi.org/organization-accounts/)
- [PyPI API Token 帮助](https://pypi.org/help/#apitoken)
- [uv：构建与发布 Python 包](https://docs.astral.sh/uv/guides/package/)
- [uv 发布相关环境变量](https://docs.astral.sh/uv/configuration/environment/)
