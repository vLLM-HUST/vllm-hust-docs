# Extension Manager 多宿主验收记录（2026-09-01）

状态：**部分通过，发布继续冻结**。本文只记录已实际执行的证据，不把配置渲染或
模拟故障称为真实宿主端到端验收。

## 1. 已验证代码与包

| 范围 | 结果 | 证据 |
|---|---:|---|
| Extension Manager | 通过 | ruff、format、31 个 pytest；Python 3.10/3.12 |
| BidKV vLLM 接口 | 通过 | `tests/test_vllm_plugin.py` 8 个 pytest |
| 网站多维分类 | 通过 | `tests/test_plugins_page.py` 11 个 pytest |
| LMCache profile metadata | 通过 | wheel 精确依赖 `vllm-hust-ext==0.2.0.dev0` |
| Mooncake/Production profiles | 通过 | wheel 构建及相同 Manager 精确依赖 |
| Production Stack chart render | 通过 | 官方 commit `1b87c11a24c144f6b63a64dbae4fc8c875059731`，Helm `v4.2.4` |
| vLLM 0.23/BidKV compatibility | 正确拒绝 | 真实容器报告 `installed + discovered + incompatible` |

本轮未发布的构建物 SHA-256：

- Manager：`cd9641984137e28a0a833dbacc9d09200f363d4e928dd9fcbcac2cd0ade61fda`
- LMCache profile：`f74f3bddb9672a2bdf900a76876b5dec26ab63007ccba594ad6c22c0604141ed`
- Mooncake profile：`b8eeac953900c5ea4c3a98655968ff8b60f9f88b9beab9149fd31445d5d06b4c`
- Production Stack profile：`05d024ec9dda0a3a9403d72c1705ab98ddb9c86022548b229eda4c0fd54b742a`

## 2. 112 与 91 包生命周期

112 使用 Python 3.12 临时虚拟环境，91 使用 Python 3.10 临时 prefix。两端均完成
LMCache profile 的安装、静态发现、配置、启用、vLLM 启动参数 dry-run、停用、
`forget` 和包卸载。91 还验证了：

- enabled 状态执行 `forget` 被拒绝，退出码为 2；
- `disable` 后才能 `forget`；
- `pip uninstall` 后 discovery 不再出现该 profile；
- 重装后是 `installed + discovered`，不会恢复旧的 enabled/configured 意图。

CLI 按 Provider 声明的 `kv_transfer_config` 能力生成 vLLM 参数，不再按 `mooncake`
名称硬编码。Mooncake 与 LMCache 同时 enabled 时对同一参数发生冲突，CLI fail
closed，退出码为 2。

## 3. 已验证失败与安全边界

- Mooncake、LMCache 的虚构/不可达健康地址投影为 `degraded`，enabled 意图保留；
- LMCache 非官方 dynamic connector module path 被拒绝；
- Production Stack 输出 Helm values 和 operator plan，`apply` 为 `null`；
- Core 拒绝 Provider 生成的 mutating action；
- Manager 不提供 service stop/delete、cache clear/evict 或 Kubernetes apply API。

Production Stack Provider 的示例 values 已实际输入官方 `helm/` chart，`helm
dependency build` 固定取得 `kube-prometheus-stack 82.4.3` 和
`prometheus-adapter 5.3.0`，随后 `helm template` 成功生成 5,889 bytes、8 个资源：
Deployment、PersistentVolumeClaim、Role、RoleBinding、Secret、两个 Service 和
ServiceAccount。该步骤只做本地渲染，没有 kube context，也没有执行 apply。

## 4. 尚未通过的发布门禁

以下项目没有真实证据，因此不能发布 alpha 或冻结 Manifest v1：

1. BidKV 在真实 vLLM scheduler 中被加载、调用并完成进程重启回退；
2. 真实 Mooncake 服务的健康、中断、恢复与 connector 数据路径；
3. 真实 LMCache MP server 的 `/healthcheck`、KV 命中和中断恢复；
4. Production Stack 的 Kubernetes server dry-run 与 rollout 检查；官方 chart
   的本地 Helm template 已通过；
5. 真实宿主版本/API/协议矩阵和权限拒绝。

112 没有可用的上述宿主环境且 Docker socket 无访问权限。91 宿主全局环境没有
LMCache、Mooncake、Helm 或 kubectl；其现有 vLLM 容器不能提供 BidKV 所需协议。
必须在可访问的真实环境重复验收后才能解除发布冻结。

补充审计：91 实际存在空闲 Ascend 910B2 和一个属于 shuhao 的 vLLM-HUST 0.23
容器，但其源码和已安装分发都没有 `vllm.victim_selector`。Manager 已取消“按版本
默认假定协议存在”的错误逻辑。BidKV 真正端到端验收需等待/跟踪上游 #51601 的
可评审契约，或由人审明确固定一个临时上游 commit；不能靠恢复私有 hook 绕过门禁。
未发布 Manager 与 BidKV wheel 已通过容器内 `/tmp` 隔离前缀实际检查，检测到
`vllm 0.23.0+empty` 位于 BidKV 声明的 `>=0.18,<0.20` 范围之外并返回
`incompatible`；没有启动模型或占用 NPU，临时目录随后已清理。
