# 工作看板

## 实时查询

- [组织公开未关闭 Issues](https://github.com/issues?q=org%3AvLLM-HUST+is%3Aopen+is%3Aissue+is%3Apublic+sort%3Aupdated-desc)
- [组织公开未关闭 PRs](https://github.com/pulls?q=org%3AvLLM-HUST+is%3Aopen+is%3Apr+is%3Apublic+sort%3Aupdated-desc)
- [组织 Projects](https://github.com/orgs/vLLM-HUST/projects) · [Benchmark 周期性工作入口](https://github.com/vLLM-HUST/vllm-hust-benchmark/issues)

## 跨仓工作入口

2026-11-16 盘点时，GitHub 搜索返回 79 个公开开放 Issue 和 16 个公开开放 PR。下表列出近期需要跨仓对齐的公开入口。当前状态、优先级和责任人从原 Issue 获取。

| 工作 | 原始跟踪 | 接手时先核对 |
| --- | --- | --- |
| 成果补证与归档 | [Benchmark #664](https://github.com/vLLM-HUST/vllm-hust-benchmark/issues/664) | 汇总源码提交、复测记录、适用范围和报告出入口 |
| B0/B1、参考分母和官网展示 | [Benchmark PR #682](https://github.com/vLLM-HUST/vllm-hust-benchmark/pull/682) · [Website PR #661](https://github.com/vLLM-HUST/vllm-hust-website/pull/661) | 固定 MOD 组合，确认参考分母，核对网页字段和来源记录 |
| DiffSpec 外部适配与 Ascend 复测 | [DiffSpec #1](https://github.com/vLLM-HUST/vllm-ascend-hust-diffspec/issues/1) · [Benchmark PR #680](https://github.com/vLLM-HUST/vllm-hust-benchmark/pull/680) | 固定 TP4 与 Eagle3 配对，记录兼容性及回归范围 |
| KVCompress 收益与代价 | [KVCompress #32](https://github.com/vLLM-HUST/vllm-ascend-kvcompress-hust/issues/32) · [Benchmark PR #678](https://github.com/vLLM-HUST/vllm-hust-benchmark/pull/678) | 复核压缩收益、TTFT 回退和适用负载 |
| GDN、Layered Prefill 补证 | [Split Batch #59](https://github.com/vLLM-HUST/vllm-ascend-split-batch-hust/issues/59) · [Layered Prefill #7](https://github.com/vLLM-HUST/vllm-ascend-layered-prefill-hust/issues/7) · [Benchmark PR #679](https://github.com/vLLM-HUST/vllm-hust-benchmark/pull/679) | 定位单机制生效点、运行时引用及证据边界 |
| PegaFlow 复现 | [PegaFlow #18](https://github.com/vLLM-HUST/pegaflow-hust/issues/18) · [Benchmark PR #648](https://github.com/vLLM-HUST/vllm-hust-benchmark/pull/648) | 固化实现、运行时引用与 DMA 优化前后证据 |
| INT4/INT8 精度与长上下文 | [Benchmark #547](https://github.com/vLLM-HUST/vllm-hust-benchmark/issues/547) | 同工况复核精度归因，补正式长上下文窗口 |
| ECPA 可组合性、失败与回滚 | [Extension Manager #44](https://github.com/vLLM-HUST/extension-manager/issues/44) · [#61](https://github.com/vLLM-HUST/extension-manager/issues/61) · [#63](https://github.com/vLLM-HUST/extension-manager/issues/63) | 核对真实 MOD 组合、版本偏差和回滚证据 |
| Core 与 Ascend 上游同步 | [Core #71](https://github.com/vLLM-HUST/vllm-hust/issues/71) · [Ascend #59](https://github.com/vLLM-HUST/vllm-ascend-hust/issues/59) | 检查失败工作流、上游基线及配对验证 |

## 任务交接

每个 Issue 保持一个当前动作，并链接实现 PR、依赖 PR 和证据源。跨仓任务记录适用版本、验收条件和阻塞项。 PR 合并后，确认涉及的验证记录、文档和发布快照已更新，再按原 Issue 口径关闭。
