# Extension Manager 实验支持矩阵与发布判定（2026-09-01）

本文区分三种结论：

- **数据面/控制面已验证**：固定版本和固定环境中观察到真实行为；
- **实验兼容范围**：Manifest 允许进入检查，不代表范围内每个版本都已验证；
- **可发布支持**：有官方载体、重复矩阵、权限与回滚证据。当前没有任何一项因此
  获得稳定 v1 承诺。

## 1. 版本与载体矩阵

| 宿主/扩展 | 固定版本与环境 | 已通过 | 未通过或未验证 | 当前投影 |
|---|---|---|---|---|
| Extension Manager Core | `0.2.0.dev0`；Windows Python 3.12、112 Python 3.12、91 Python 3.10 | wheel 安装、静态发现、validate、configure/enable/disable/forget、非变更 plan/render/check | 尚未发布；Manifest `0.2-experimental` 未冻结 | experimental，发布冻结 |
| vLLM-HUST / BidKV | vLLM-HUST `0.23.x` typed `vllm.scheduler.policy.v1`；91 Ascend/Qwen3-0.6B | 契约测试；真实加载；KV 100% 下 3 次 `UTILITY_ACTIVE`；3 请求完成；disable→新进程→内置策略回退 | 需从干净 release image/wheel 重复；官方 vLLM 上游契约未冻结 | vLLM-HUST supported；官方 vLLM unsupported；发布载体仍阻塞 alpha |
| Mooncake standalone | 官方 non-CUDA `0.3.12.post1`，A100 host、CPU DRAM/TCP | 两进程 1 MiB TransferEngine；Store REST put/exist/get/lease-aware remove | 未覆盖跨节点、RDMA、CUDA wheel 与版本回归 | 固定点通过，范围仍 experimental |
| Mooncake + vLLM Ascend | NPU wheel `0.3.11.post1`；vLLM `0.23.0`；vLLM Ascend `0.19.1.post1.dev474+g4edbc9258`；Ascend 910B，NPU 4 | `MooncakeStoreConnector` 9-key save/load；master 中断降级及原 vLLM 进程恢复 | 此路径要求 `transport_protocol=ascend`、`load_async=true`；未覆盖声明范围 `>=0.3.11.post1,<0.4` 的全部版本 | healthy（固定组合），矩阵未冻结 |
| Production Stack 控制面 | 官方 commit `1b87c11…`、chart `0.1.12`、Helm `4.2.4`、Kubernetes `1.34.11`、metrics-server `0.9.0` | template/server dry-run；Helm install/upgrade/explicit+automatic rollback/uninstall；controller reconciliation；独立所有权 HPA 1→3；双写冲突 | 只验证一个 Kubernetes/Helm 组合；controller/HPA 不能共同写 replicas | integration-tested，矩阵未冻结 |
| Production Stack Router + 真实模型 | 同 commit 源码构建 arm64 Router；180 既有 GLM-4-32B vLLM | 不可达后端 500；只重建测试 Router 后真实模型 200/`ROUTER_OK`；生产 vLLM 未重启 | 官方 `router:v0.1.12` 无 `linux/arm64/v8`；未验证官方 amd64 release image | healthy + degraded；发布载体阻塞 |

## 2. 生命周期与回滚边界

| 类型 | Manager 可做 | 宿主/operator 必须做 | 回滚定义 |
|---|---|---|---|
| vLLM 进程内 policy | 保存配置和 enable intent，生成下一次启动参数，启动前 fail closed | vLLM 加载实现并拥有 scheduler/KV；operator 重启进程 | disable 后启动**新进程**恢复内置策略；不承诺热卸载 |
| Mooncake 外部 KV 系统 | 检查 endpoint/版本/操作证据；服务不可达时保留 intent 并投影 degraded | KV 系统启动、停止、升级、backend/transport、数据保留与删除 | 服务恢复后无需重装 Manager；disable 不停服务、不清 KV |
| vLLM KV connector | 渲染唯一 `kv_transfer_config`，拒绝多个 Provider 争用同一参数 | vLLM 在新进程中构造 connector；外部服务保持独立 | disable 后新 vLLM 进程不再加载；不在运行中替换 connector |
| Production Stack/Kubernetes | plan、render、server dry-run 输入、check、冲突投影 | operator 持有 kube credentials，执行 Helm/CRD/controller/router/HPA 生命周期 | 以 Helm revision/history 和 operator 审批 rollback；Manager 无 apply/rollback/uninstall API |

所有类型都禁止 Manager 默认修改驱动、删除共享 KV 数据、停止共享服务或直接修改
生产集群。`enabled` 是委托意图，不是宿主工作负载已经运行。

## 3. Alpha 判定

结论：**NO-GO，继续冻结 PyPI/alpha 和 Manifest v1。**

阻塞项按优先级为：

1. BidKV 在 vLLM-HUST 0.23 上已有受支持的 typed scheduler contract，在线模型
   抢占和进程重启回退已通过；仍需从干净发布镜像/wheel 重复。官方 vLLM 继续明确
   为 unsupported。
2. Production Stack v0.1.12 缺少 arm64 官方 Router image；源码构建通过不能替代
   release artifact 支持矩阵。
3. Mooncake/Production Stack 目前是固定版本点验证，不是跨版本、跨架构、
   权限拒绝与升级矩阵。

满足以下条件后才能重新评估：BidKV 在线结果由干净发布载体重复；每个
拟支持宿主至少有一个官方发布载体；固定矩阵可重复；缺权限、冲突、不可达、部分
失败、升级和回滚均有机器可判定结果；clean install/uninstall 不留下 enabled intent。
