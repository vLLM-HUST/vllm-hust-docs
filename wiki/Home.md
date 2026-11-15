# vLLM-HUST 组织 Wiki

vLLM-HUST 维护面向国产算力、兼容上游 vLLM 的推理运行时、Ascend 适配和配套工程工具。组织也维护独立的研究成果、运行时扩展、评测基础设施及面向使用者的工作台。

| 要做的事 | 从这里开始 |
| --- | --- |
| 找到问题归属，理解运行时、硬件后端、MOD 和部署层 | [技术架构与仓库分工](Architecture.md) |
| 查询公开仓库的用途和归档状态 | [公开仓库目录](Repositories.md) |
| 准备开发环境、找评审人、提 Issue 或 PR | [开发与协作](Collaboration.md) |
| 复现实验、验证 MOD、补证或发布性能数据 | [评测与发布](Validation.md) |
| 接手工作、跟踪复测和跨仓依赖 | [工作看板](Workboard.md) |
| 更新 Wiki、核对资料和发布 | [Wiki 维护](Maintenance.md) |

## 第一次接手工作

1. 从工作看板打开原 Issue，确认范围、当前状态与已有结果。新增工作先在职责对应的仓库登记。
2. 从 Dev Hub 准备工作区，从运行环境支持矩阵选定设备和镜像。跨仓工作先固定 core、Ascend 插件和 MOD 的版本。
3. 在实现仓库提交代码与最小验证。涉及实验数据、测量结果或原始证据时，在 Benchmark 建立出处并回链实现 PR。

[GitHub 组织](https://github.com/vLLM-HUST) · [官网](https://vllm-hust.sage.org.ai/) · [开发工作区](https://github.com/vLLM-HUST/vllm-hust-dev-hub) · [评测数据索引](https://github.com/vLLM-HUST/vllm-hust-benchmark/blob/main/DATA_INDEX.md)

盘点日期：2026-11-16（北京时间）。实时状态以链接指向的源仓库为准。
