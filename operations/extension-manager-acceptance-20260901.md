# Extension Manager 多宿主验收记录（2026-09-01）

状态：**部分通过，发布继续冻结**。本文只记录真实宿主证据；配置渲染和模拟故障
不计作端到端通过。

## 已通过

| 范围 | 结果 | 证据 |
|---|---:|---|
| Extension Manager | 通过 | Core + Host Provider 单元测试、静态发现、配置、状态与非变更 plan/render/check |
| vLLM-HUST / BidKV | 91/112 干净载体通过 | 相同 pushed commits `87096bd3d`/`2b55997`/`b4f221f`；Qwen3-0.6B 与 Qwen2.5-3B 均在 KV 满载下三次 `UTILITY_ACTIVE`；各自 3×1,400-token 请求完成；disable 后新进程恢复内置策略；forget/uninstall 无残留 |
| Mooncake standalone | 通过 | 官方 non-CUDA 0.3.12.post1；两进程 1 MiB TransferEngine TCP；Store REST put/exist/get/lease-aware remove |
| Mooncake / vLLM Ascend | 固定组合通过 | NPU 4；`MooncakeStoreConnector` 9-key save/load；master 中断后推理保持可用，原 vLLM 进程在服务恢复后重新命中 |
| Mooncake HUST fork | 已建立，零核心补丁 | [`vLLM-HUST/mooncake-hust`](https://github.com/vLLM-HUST/mooncake-hust) 直接 fork 官方 Mooncake；上游现有 Ascend/arm64 发布能力继续作为实现基线 |
| Production Stack chart | 通过 | 官方 commit `1b87c11…`；Helm template、Kubernetes server dry-run、install/upgrade/rollback/uninstall |
| Production Stack controller/Router/HPA | 通过 | controller reconciliation、Router 转发、Metrics API 1→3，以及 HPA/controller replicas 双写冲突拒绝 |
| Production Stack 真实模型 Router | 固定源码构建通过 | 180 上不可达后端返回 500；只重建测试 Router 后既有 GLM-4-32B 返回 200/`ROUTER_OK`，未重启生产 vLLM |
| Production Stack HUST fork | arm64 发布通过 | [`vLLM-HUST/production-stack-hust`](https://github.com/vLLM-HUST/production-stack-hust) commit `7611dfa` 由 GitHub-hosted runner 构建、入口烟测并发布 GHCR；91 arm64 拉取与入口验收通过 |

## 安全与所有权边界

- Manager 只保存 intent、生成配置并执行 `plan/render/check`；不默认启停共享服务、
  修改驱动、删除 KV 数据或 apply 生产集群。
- vLLM 进程内扩展在下次进程启动时加载或回退，不承诺热卸载。
- Mooncake 保留服务、传输、存储与 KV 数据生命周期。
- Kubernetes operator 持有凭据并执行 Helm/CRD/controller/router/autoscaler 生命周期。
- Provider 配置冲突、宿主/API/协议不兼容、缺少证据和 mutating action 均 fail closed。
- 两个 HUST fork 不维护 self-hosted Actions runner 或 self-hosted server；
  91/180 只作为 operator 管理的目标宿主按需验收，不属于项目基础设施。

## 尚未通过

1. BidKV 的 91/112 干净 wheel/carrier 门禁均已通过；官方 vLLM 在上游
   scheduler contract 冻结前仍不支持，更宽版本/平台矩阵仍未冻结。
2. Mooncake 需要补跨版本、跨节点和传输矩阵。
3. Production Stack 的 HUST arm64 workflow 已完成发布并在 91 拉取验收；仍需
   补跨版本与权限拒绝矩阵。产品不要求 amd64 或 self-hosted 基础设施。
4. 需要补齐权限拒绝、升级和干净安装/卸载矩阵。

## 发布判定

结论：**NO-GO**。继续冻结 PyPI alpha 和 Manifest v1，直到每个拟支持宿主都有
可重复的官方发布载体、失败/冲突/回滚证据和 clean install/uninstall 结果。
