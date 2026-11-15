# 评测与发布

## 从实现到正式证据

1. **先固定工况。** 记录构建 commit 与镜像 digest、模型 revision 与精度、设备及并行拓扑、MOD 组合、工作负载版本、上下文、并发、随机种子和测量窗口。B0、B1 与独立参考分母按对应报告的定义执行。 [实验设定](https://github.com/vLLM-HUST/vllm-hust-website/blob/main/docs/BENCHMARK-SETTINGS.md) · [B0/B1 公式](https://github.com/vLLM-HUST/vllm-hust-benchmark/blob/main/docs/B0_BASELINE_METRICS.md)
2. **确认实际生效。** 对 MOD 检查 manifest、宿主版本、多进程加载、行为对照、配置冲突与关闭后恢复。以对应的设备、模型和负载验证兼容性。 [扩展作者指南](https://github.com/vLLM-HUST/vllm-hust-docs/blob/main/operations/extension-author-guide.md) · [ECPA 0.3](https://github.com/vLLM-HUST/vllm-hust-website/blob/main/docs/PLUGIN_STANDARD.md)
3. **按问题做对照。** 单机制结论使用可归因的启用/关闭对照，系统结论记录整套组合。同步核对正确性、吞吐、TTFT、TPOT、失败率、长上下文稳定性及适用工况。Smoke、正式窗口、版本差异和整套系统收益各有原始试验记录。 [测量与发布规则](https://github.com/vLLM-HUST/vllm-hust-website/blob/main/docs/BENCHMARK-SETTINGS.md)
4. **集中归档。** 数据集、测量和原始证据提交到 `vllm-hust-benchmark`，包括适用的 Release assets。实现仓保存源码和软件包，并引用证据提交或固定资产。先复核现有原始记录，确有缺口时补最小试验。 [数据索引](https://github.com/vLLM-HUST/vllm-hust-benchmark/blob/main/DATA_INDEX.md) · [证据归属](https://github.com/vLLM-HUST/vllm-hust-dev-hub/blob/main/docs/benchmark-evidence-custody.md)

| 核对项 | 证据 |
| --- | --- |
| 可复现 | 精确版本、命令、原始日志、数据或资产链接及校验值 |
| 配对可比 | 相同工况、明确变化项和指标单位，说明不同条件 |
| 数据可追溯 | 报告表格可返回原始 run 与评测源提交 |
| 结论有边界 | 写明支持范围、负结果、未验证项和回滚入口 |
| 验收口径明确 | 阶段里程碑读 V1.5 对应记录，最终目标读项目最终要求 |

[阶段里程碑报告](https://github.com/vLLM-HUST/vllm-hust-benchmark/tree/main/reports/vllm-hust-midterm-20261019) · [项目最终目标](https://github.com/vLLM-HUST/vllm-hust-benchmark/tree/main/reports/project-final-goals-20261113)

## 官网数据

公开测量由 Benchmark 的 `website-publication/data/` 提供。官网部署流程使用已合并的固定 Benchmark 提交，生成来源 manifest 和校验值。需要订正时回到 Benchmark 的源文件与生成流程，再核对网页和来源面板。 [发布流程](https://github.com/vLLM-HUST/vllm-hust-website/blob/main/docs/PERFORMANCE-DATA-PUBLICATION.md)

[性能曲线](https://vllm-hust.sage.org.ai/leaderboard-runs.html) · [数据集验证](https://vllm-hust.sage.org.ai/dataset-validation.html) · [容量与成本](https://vllm-hust.sage.org.ai/serving-plan.html)
