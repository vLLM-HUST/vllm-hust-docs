# 开发与协作

## 找维护入口

| 场景 | 处理入口 |
| --- | --- |
| 核心服务、CLI、调度或模型执行 | [vllm-hust Issues](https://github.com/vLLM-HUST/vllm-hust/issues) |
| Ascend 设备、算子与 NPU 回归 | [vllm-ascend-hust Issues](https://github.com/vLLM-HUST/vllm-ascend-hust/issues) |
| 容器、环境和工作区 | [Dev Hub Issues](https://github.com/vLLM-HUST/vllm-hust-dev-hub/issues) · [Ascend Runtime Manager](https://github.com/vLLM-HUST/ascend-runtime-manager) |
| MOD 行为、兼容性或组合问题 | 先到 [MOD 对应仓库](https://vllm-hust.sage.org.ai/plugins.html)，共用 manifest 或 Provider 问题到 [Extension Manager](https://github.com/vLLM-HUST/extension-manager/issues) |
| 评测条件、复现、数据或报告 | [Benchmark Issues](https://github.com/vLLM-HUST/vllm-hust-benchmark/issues) |
| 官网、快照展示和目录 | [Website Issues](https://github.com/vLLM-HUST/vllm-hust-website/issues) |
| 文档和变更记录 | [Docs Issues](https://github.com/vLLM-HUST/vllm-hust-docs/issues) |

公开人员信息从 [核心贡献者页面](https://vllm-hust.sage.org.ai/contributors.html) 和 [贡献者口径](https://github.com/vLLM-HUST/.github/blob/main/CONTRIBUTORS.md) 获取。具体工作以原 Issue 的 assignee 为准。评审请求按目标仓库维护者、评审记录和仓库级规则发起。BidKV 和 ECPA 的公开项目责任分别由其 [BidKV README](https://github.com/vLLM-HUST/vllm-hust-bidkv) 和 [Extension Manager README](https://github.com/vLLM-HUST/extension-manager) 维护。

## 开发与提交

1. 在 Dev Hub 准备多仓工作区。Ascend 机器按支持矩阵选择镜像并记录 OCI digest。已准备好的 Dev Hub 机器由 `./manage.sh` 管理服务启动、健康检查与验证。 [Dev Hub](https://github.com/vLLM-HUST/vllm-hust-dev-hub) · [环境支持矩阵](https://github.com/vLLM-HUST/vllm-hust-dev-hub/blob/main/docs/ascend-official-runtime-support-matrix.zh-CN.md)
2. 先确认变更属于通用引擎、设备适配、独立 MOD 还是部署工具。通用变更核对上游归属。跨仓改动在 PR 里记录依赖 PR、提交顺序、适用版本和回滚方式。 [组织贡献指南](https://github.com/vLLM-HUST/.github/blob/main/CONTRIBUTING.md)
3. 按目标仓库说明运行最小测试。引擎与设备插件成对验证，记录精确 commit、设备、镜像、模型及命令。技术文档回链对应实现、Issue 和验证记录。 [优化仓库工作手册](https://github.com/vLLM-HUST/vllm-hust-docs/blob/main/operations/optimization-repository-playbook.md)

## 提报模板

| Issue 字段 | 填写内容 |
| --- | --- |
| 问题与预期 | 观察到的行为、预期行为、影响范围 |
| 固定环境 | repo/commit、core 和 Ascend 配对、设备和卡数、镜像 digest、模型和精度、MOD |
| 最小复现 | 请求、命令或配置，附脱敏日志与复跑结果 |
| 已有关联 | 上游或组织现有 Issue、相关 PR、复现或实验记录 |
| 交付口径 | 验收条件、依赖、回滚和需要评审的内容 |

一般问题可按 [支持指南](https://github.com/vLLM-HUST/.github/blob/main/SUPPORT.md) 提报。漏洞或凭据暴露按 [安全策略](https://github.com/vLLM-HUST/.github/blob/main/SECURITY.md) 走受影响仓库的私密报告渠道。
