# Extension Manager 多宿主验收记录（2026-09-01）

状态：**部分通过，发布继续冻结**。本文只记录已实际执行的证据，不把配置渲染或
模拟故障称为真实宿主端到端验收。

## 1. 已验证代码与包

| 范围 | 结果 | 证据 |
|---|---:|---|
| Extension Manager | 通过 | 43 个 pytest；新增 unverified/incompatible 启动拒绝 |
| BidKV 历史接口边界 | 通过 | 主发行包不再注册私有 `vllm.victim_selector`；旧 adapter 仅 import-only |
| 网站多维分类 | 通过 | `tests/test_plugins_page.py` 11 个 pytest |
| LMCache profile metadata | 通过 | wheel 精确依赖 `vllm-hust-ext==0.2.0.dev0` |
| LMCache-Ascend adapter metadata | 通过 | 独立 profile wheel；动态 connector/module 精确配对 |
| Mooncake/Production profiles | 通过 | wheel 构建及相同 Manager 精确依赖 |
| Mooncake NPU service health lifecycle | 通过 | 180 官方 NPU wheel；healthy → degraded → healthy |
| Production Stack chart render | 通过 | 官方 commit `1b87c11a24c144f6b63a64dbae4fc8c875059731`，Helm `v4.2.4` |
| Production Stack server dry-run | 通过 | 临时 kind `v0.33.0`、Kubernetes `v1.34.11`，8/8 资源通过 |
| Production Stack Helm rollout/rollback | 通过 | 实际 install/upgrade/rollback/failure rollback/uninstall |
| vLLM 0.23/BidKV compatibility | 正确拒绝 | 真实容器报告 `installed + discovered + incompatible` |

本轮未发布的构建物 SHA-256：

- Manager（本轮 fail-closed 验收所用未发布 wheel）：`cc87c686f1ad04adf66d79c082e2867a3480f7cd61fb2cda01c26d7fb5cfa35d`
- BidKV（本轮移除私有 entry point 后的未发布 wheel）：`c664cf2cf61772a20c9f189f691c8867935cce739993319eef0ca4e2bd439ea3`
- LMCache profile：`f74f3bddb9672a2bdf900a76876b5dec26ab63007ccba594ad6c22c0604141ed`
- Mooncake profile（本轮最新临时构建）：`46b735b8b56a9c8d787ffc9af49130dcec9331d8c5973805e4315ecd88a307ff`
- Production Stack profile：`05d024ec9dda0a3a9403d72c1705ab98ddb9c86022548b229eda4c0fd54b742a`
- LMCache-Ascend adapter profile（本轮临时构建）：`947549095322eb3e4a9d410950ece2bccb1eb377b3bfd42782e6216486a209dd`

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

另在 Windows 临时虚拟环境实际安装上述 Manager 与 BidKV wheel：静态 discovery
成功，已安装 metadata 中 `vllm.victim_selector` entry point 为零；保存 enabled
意图后状态为 `installed + discovered + configured + enabled + degraded`，由于宿主
版本和协议证据缺失，`run --dry-run` 在生成命令前以退出码 2 拒绝启动。

## 3. 已验证失败与安全边界

- Mooncake、LMCache 的虚构/不可达健康地址投影为 `degraded`，enabled 意图保留；
- LMCache 非官方 dynamic connector module path 被拒绝；
- LMCache connector 与 module 必须精确配对；`LMCacheMPConnector` 不再生成
  实际不存在的 `lmcache.integration.vllm.lmcache_mp_connector`；
- Production Stack 输出 Helm values 和 operator plan，`apply` 为 `null`；
- Core 拒绝 Provider 生成的 mutating action；
- Manager 不提供 service stop/delete、cache clear/evict 或 Kubernetes apply API。
- Manager `run` 对 `incompatible` 扩展一律拒绝；对 vLLM 进程内
  `scheduler_policy` 还要求明确的 compatible 证据，不能凭 enabled 意图启动。

Production Stack Provider 的示例 values 已实际输入官方 `helm/` chart，`helm
dependency build` 固定取得 `kube-prometheus-stack 82.4.3` 和
`prometheus-adapter 5.3.0`，随后 `helm template` 成功生成 5,889 bytes、8 个资源：
Deployment、PersistentVolumeClaim、Role、RoleBinding、Secret、两个 Service 和
ServiceAccount。该步骤只做本地渲染，没有 kube context，也没有执行 apply。

随后在 91 创建了唯一命名的 CPU-only 临时 kind 集群，使用独立 kubeconfig 对同一
渲染结果执行 `kubectl apply --dry-run=server`。Kubernetes 1.34.11 API 接受全部
8 个资源：ServiceAccount、Secret、PersistentVolumeClaim、Role、RoleBinding、
两个 Service 和 Deployment；每项均返回 `created (server dry run)`。没有 apply
实际 workload、没有挂载 NPU，也没有接触任何现有集群。验收后已确认删除 kind
控制面容器、临时 kubeconfig/目录和本次新拉取的 node image。

## 4. 尚未通过的发布门禁

以下项目没有真实证据，因此不能发布 alpha 或冻结 Manifest v1：

1. BidKV 在真实 vLLM scheduler 中被加载、调用并完成进程重启回退；
2. Mooncake connector 的真实 KV 数据路径；官方 NPU master 的健康、中断、恢复
   已通过；
3. 真实 LMCache MP server 的 `/healthcheck`、KV 命中和中断恢复；
4. Production Stack 官方 controller 业务 reconciliation 和实际 autoscaling 决策；
   chart render、server dry-run、隔离集群 Router/controller fixture rollout、CRD API、
   HPA target 引用和 Helm 回滚已通过；
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

## 5. 91 上 LMCache / LMCache-Ascend 实探结论

本轮只在 shuhao 自有容器
`vllm-hust-shuhao-spec-23rc-20260825` 的 `/tmp` 隔离目录内操作，没有修改
全局 Python、模型服务或 NPU 状态。容器为 Python 3.12、vLLM
`0.23.0+empty`、`vllm_ascend 0.23.0rc1`，8 张 910B2 均保持空闲。

实际下载并检查 LMCache 0.4.3 源码后确认：该版本把
`NO_CUDA_EXT=1` 解释为“完全不构建扩展”，会同时缺失 MP HTTP server 所需的
`lmcache.native_storage_ops`。为隔离诊断，仅从同一 0.4.3 源码在 `/tmp` 编译了
通用 CPU C++ 模块；`TTLLock` 导入和 `http_server --help` 均成功。随后以
loopback-only 的 `127.0.0.1:15555/18080` 尝试启动真实 MP server，服务在启动期
因无条件导入 `cupy` 失败，`/healthcheck` 从未就绪。

这不是 Extension Manager 可通过伪健康服务掩盖的问题。当前组织内
LMCache-Ascend commit `578d833f1b2b74311650740ae2dbed5ca1ff4c60` 的 MP 目录同样明确
未完成：`NPUCacheContext` 直接抛出 `NotImplementedError`，并且测试配置跳过全部
MP 测试。因此 91 不能作为“真实 LMCache MP healthy/recovery”通过证据；禁止安装
CuPy stub 或把 legacy CPU/ZMQ server 冒充 MP `/healthcheck`。

同时修正了建模：

- LMCache MP server 仍是 LMCache 自己管理的外部服务；
- LMCache-Ascend 是 LMCache 内部的平台后端，其
  `LMCacheAscendConnector[V1Dynamic]` 是加载到 vLLM 的 adapter；
- 新增独立 `vllm-hust-lmcache-ascend-adapter` profile，无
  `requires_services`，不再把它错误声明为 MP 服务；
- 通用与 Ascend dynamic connector 只允许各自官方精确模块路径。

发布门禁保持不变：应在 CUDA LMCache MP 支持环境完成真实
healthy → outage/degraded → recovery/healthy，再在 Ascend 环境分别完成
LMCache-Ascend in-process connector 的真实 KV 命中验证。

## 6. 180 上 Mooncake NPU 实际健康生命周期

在用户自有容器 `sage-mate-vllm-shuhao-sage-mate` 中，以 `/tmp` 隔离前缀安装
官方 `mooncake-transfer-engine-npu==0.3.13.post1`，wheel SHA-256 为
`ba134f2cc99784aa32404c3a1406e3c85400792fb2c62bb458cd4757a07cc4bb`。
没有修改容器全局包。临时 master 仅绑定 loopback：RPC `127.0.0.1:25051`、
metadata `127.0.0.1:28088`、admin/health `127.0.0.1:29003`。

实际观察到 master `/health` 返回 HTTP 200、`role=leader`、
`ha_state=serving`、`service_ready=true`。把未发布 Manager 与 Mooncake profile
装入另一 `/tmp` prefix 后，CLI 投影为：

1. 服务运行：`installed + discovered + compatible + configured + enabled +
   reachable + healthy`；
2. 测试夹具终止临时 master：enabled 意图保留，投影为 `degraded`，证据是
   connection refused；
3. 以同一配置恢复 master：重新投影为 `reachable + healthy`；
4. 执行 Manager `disable` 和 `forget` 后，master 仍返回 HTTP 200，证明 Manager
   没有接管外部服务生命周期。

CLI 同时生成官方
`--kv-transfer-config {"kv_connector":"MooncakeStoreConnector","kv_role":"kv_both"}`。
Provider 已补充检测所有官方互斥 wheel 变体（CUDA、CUDA 13、non-CUDA、NPU、
MUSA、EFA）；同一环境发现多个变体时 fail closed。

本轮没有把 Mooncake KV 数据路径标记为通过。`put/get` 客户端在初始化 NPU
Transfer Engine 时因 ACL context 为空失败；该生产容器的 4 张 NPU 均已由现有
vLLM TP workers 占用约 46.9 GiB，未为验收创建额外 device context，也未中断现有
推理服务。应在空闲 NPU 或官方允许的 CPU/non-CUDA 环境重做 store `put/get` 和
vLLM connector 命中测试。

验收完成后已终止临时 master，确认三个 loopback 端口关闭，并删除容器与宿主的
全部本轮临时目录；现有 vLLM worker 和认证代理未被修改。

## 7. Production Stack 实际 Helm 生命周期

在 91 创建了唯一的临时 kind `v0.33.0` 集群，node image 固定为 Kubernetes
`v1.34.11` digest
`sha256:44e222ee2132dab25ff87301682f89eb82c7880ea3a1bf543bfe9708fd08d67d`。
验收使用官方 Production Stack commit
`1b87c11a24c144f6b63a64dbae4fc8c875059731` 的 chart
`vllm-stack-0.1.12` 和 Helm `v4.2.4`。

为了不下载模型、不占用 GPU/NPU，也不把模拟 workload 冒充真实 vLLM，新增了可复现
fixture `operations/fixtures/production-stack-rollout-probe/`。它只启用官方 Router
Deployment/Service/RBAC 模板，关闭 serving engine 和 Prometheus，并使用一个仅提供
`/health` 的 BusyBox 测试 OCI image。该 fixture 验证的是 Production Stack/Kubernetes
控制面生命周期，不证明真实 Router 路由算法或模型数据面。

实际执行结果：

1. Helm revision 1：安装成功，Router Deployment `1/1` available，image `v1`；
2. revision 2：升级到 `2/2` available，image `v2`；
3. revision 3：显式 `helm rollback` 回到 `1/1` 和 image `v1`；
4. revision 4：指定不存在且 `imagePullPolicy=Never` 的 image，升级以退出码 1 失败；
5. `--rollback-on-failure` 自动创建 revision 5，恢复到 `1/1` 和 image `v1`；
6. `helm uninstall --wait` 后，release 及其 Deployment、Service、ServiceAccount、
   Role、RoleBinding 均不存在。

随后删除了临时 kind 控制面、测试 image 两个 tag、固定 node image 和远端 staging
目录，并逐项确认不存在。未接触任何现有 Kubernetes 集群。

Manager 仍没有执行上述变更的 API。Production Stack Provider 只生成非变更的
template/server-dry-run/rollout-history argv；install、upgrade、rollback、uninstall
在 operator plan 中均保持 `null`。同时修复了状态证据漏洞：
`cluster_reachable=true` 和 `rollout_healthy=true` 现在必须分别提供非空证据，且
healthy 不能与 unreachable 并存，防止仅靠布尔配置伪造健康状态。

第二个唯一临时集群启用了 LoRA controller 和 Router HPA，共渲染 12 个资源。Router
和 controller probe Deployment 均为 `1/1` available；
`loraadapters.production-stack.vllm.ai` CRD 的 `Established=True`、
`NamesAccepted=True`，合法 `LoraAdapter` 对象通过 API server dry-run。HPA 成功读取
Deployment scale subresource（`AbleToScale=True/SucceededGetScale`），但由于该最小
kind 集群刻意没有 metrics-server，`ScalingActive=False/FailedGetResourceMetric`；
因此不能声称发生了真实 CPU 扩缩容。

这次实测还纠正了 manifest 中两个事实错误：官方 chart 当前 CRD 是
`LoraAdapter`，不是此前声明的 `Model/Router`；且 Helm 4.2.4 已实际成功，
`helm-values` 协议范围从 `>=3,<4` 修为 `>=3,<5`。官方 controller image 的 registry
查询在该环境超时，因此运行的是明确标注的健康 probe image，不声称验证 controller
业务逻辑。

Helm uninstall 后 release-owned Router/controller/HPA/RBAC 资源均消失，而 chart
`crds/` 安装的 `LoraAdapter` CRD 按 Helm 语义保留；Manager 不应擅自删除它。随后
删除整个隔离集群，CRD、测试 image、node image 和 staging 目录一并清理。

剩余控制面门禁是官方 controller 业务 reconciliation、带 metrics-server 的真实
autoscaling 决策及真实 Router/模型后端联通；轻量 fixture 不覆盖这些数据面行为。
