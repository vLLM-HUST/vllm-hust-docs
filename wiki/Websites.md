# 网站与网页总索引

核对日期：2026-11-19（北京时间）。本页覆盖 70 个公开仓库的网页入口、28 个官网已部署 HTML 文件，以及仓库登记的项目外链和上游参考入口。公开目录不包含权限受限的仓库资料。

## 从哪里开始

| 要做的事                       | 推荐入口                                                                                                                          |
| ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| 了解组织与三项主产品           | [官网](https://vllm-hust.sage.org.ai/)                                                                                            |
| 找组织协作规则和项目分工       | [组织 Wiki](https://github.com/vLLM-HUST/.github/wiki)                                                                            |
| 查当前引擎和安装入口           | [引擎页](https://vllm-hust.sage.org.ai/engine.html)                                                                               |
| 找 MOD 及其原件                | [MOD 目录](https://vllm-hust.sage.org.ai/plugins.html)                                                                            |
| 查性能、任务范围与版本证据     | [B0/B1](https://vllm-hust.sage.org.ai/b0-b1.html)、[运行记录](https://vllm-hust.sage.org.ai/leaderboard-runs.html)                |
| 找服务控制与组件               | [服务控制产品页](https://vllm-hust.sage.org.ai/control-plane.html)、[限流与调度组件](https://vllm-hust.sage.org.ai/controlplane/) |
| 查长期记忆                     | [长期记忆产品页](https://vllm-hust.sage.org.ai/continuum.html)                                                                    |
| 查每个公开仓库的 README 和主页 | [公开仓库网页入口](Web-Repositories.md)                                                                                           |

## 网站归属与部署

| 入口                                                    | 类型与归属       | 维护位置                                                                      | 核对结果                                                                  |
| ------------------------------------------------------- | ---------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| [vllm-hust.sage.org.ai](https://vllm-hust.sage.org.ai/) | 组织官网         | [Website](https://github.com/vLLM-HUST/vllm-hust-website)，Actions 构建发布   | HTTPS 可达；Pages 使用自定义域名                                          |
| [vllm-hust.github.io](https://vllm-hust.github.io/)     | 旧地址兼容跳转壳 | [旧组织站仓库](https://github.com/vLLM-HUST/vllm-hust.github.io)              | HTTP 返回 200 跳转页；真实浏览器会保留路径/参数跳往官网，不是第二套内容站 |
| [组织 Wiki](https://github.com/vLLM-HUST/.github/wiki)  | 组织知识入口     | [源稿](https://github.com/vLLM-HUST/vllm-hust-docs/tree/main/wiki)与原生 Wiki | 源稿与原生页面分开维护，链接按目标形式转换                                |
| [组织 GitHub](https://github.com/vLLM-HUST)             | 组织与仓库入口   | [.github/profile](https://github.com/vLLM-HUST/.github/tree/main/profile)     | 仓库、贡献、议题等以 GitHub 当时状态为准                                  |

公开 Wiki 是 GitHub 页面，不是额外启用的 Pages 站点。多个 MOD 仓库共用官网插件目录，属于共享入口。

## 官网完整 HTML 目录

目录来自正式 Pages 构建产物，包含没有出现在主导航的历史页、安装索引与模板。28 个文件均已匿名 HTTP 读取为 200；该检查不等同于所有交互、下载或实验的验收。

### 门户

| 页面                                                 | 用途                 | 路径         |
| ---------------------------------------------------- | -------------------- | ------------ |
| [官网首页](https://vllm-hust.sage.org.ai/index.html) | 三项主产品和全站导航 | `index.html` |

### 产品与组件

| 页面                                                                            | 用途                          | 路径                      |
| ------------------------------------------------------------------------------- | ----------------------------- | ------------------------- |
| [长期记忆](https://vllm-hust.sage.org.ai/continuum.html)                        | 产品说明与当前规划            | `continuum.html`          |
| [服务控制](https://vllm-hust.sage.org.ai/control-plane.html)                    | 产品范围、组件与证据          | `control-plane.html`      |
| [请求限流与程序调度组件](https://vllm-hust.sage.org.ai/controlplane/index.html) | 服务控制下的交互结果页        | `controlplane/index.html` |
| [推理引擎](https://vllm-hust.sage.org.ai/engine.html)                           | 当前冻结版本、安装与 MOD 入口 | `engine.html`             |

### MOD 与评测

| 页面                                                                        | 用途                                 | 路径                         |
| --------------------------------------------------------------------------- | ------------------------------------ | ---------------------------- |
| [B0/B1 对比](https://vllm-hust.sage.org.ai/b0-b1.html)                      | 按版本看固定五项、上下文、时延和成本 | `b0-b1.html`                 |
| [指定数据集](https://vllm-hust.sage.org.ai/dataset-introductions.html)      | 了解五项标准与公开轨迹范围           | `dataset-introductions.html` |
| [标准测试指南](https://vllm-hust.sage.org.ai/dataset-standard.html)         | 执行标准测试和获取数据               | `dataset-standard.html`      |
| [数据集评测](https://vllm-hust.sage.org.ai/dataset-validation.html)         | 质量与验证记录                       | `dataset-validation.html`    |
| [r8 开发对照证据](https://vllm-hust.sage.org.ai/engine-r8-development.html) | 开发阶段对照，区别于冻结 B0          | `engine-r8-development.html` |
| [性能与运行记录](https://vllm-hust.sage.org.ai/leaderboard-runs.html)       | 当前与历史轮次的实测入口             | `leaderboard-runs.html`      |
| [MOD 目录](https://vllm-hust.sage.org.ai/plugins.html)                      | 查找插件、适用条件和成果入口         | `plugins.html`               |
| [服务产能与成本](https://vllm-hust.sage.org.ai/serving-plan.html)           | 服务方案和成本计算                   | `serving-plan.html`          |

### 生态与资料

| 页面                                                             | 用途                                     | 路径                     |
| ---------------------------------------------------------------- | ---------------------------------------- | ------------------------ |
| [研究成果](https://vllm-hust.sage.org.ai/achievements.html)      | 论文和成果资料                           | `achievements.html`      |
| [会议](https://vllm-hust.sage.org.ai/conferences.html)           | 会议信息                                 | `conferences.html`       |
| [课程](https://vllm-hust.sage.org.ai/courses.html)               | 课程及项目材料                           | `courses.html`           |
| [生态应用](https://vllm-hust.sage.org.ai/ecosystem-archive.html) | Workstation、Sage Mate 与研究日报等入口  | `ecosystem-archive.html` |
| [精选议题档案](https://vllm-hust.sage.org.ai/issues.html)        | 精选历史议题，非全组织实时看板           | `issues.html`            |
| [新闻](https://vllm-hust.sage.org.ai/news.html)                  | 动态和更新                               | `news.html`              |
| [算力资源](https://vllm-hust.sage.org.ai/resources.html)         | 公开资源与环境说明                       | `resources.html`         |
| [版本快照](https://vllm-hust.sage.org.ai/versions.html)          | 源码及注册表快照，不表示生产组合已获批准 | `versions.html`          |

### 社区

| 页面                                                      | 用途               | 路径                |
| --------------------------------------------------------- | ------------------ | ------------------- |
| [贡献者](https://vllm-hust.sage.org.ai/contributors.html) | 公开贡献记录       | `contributors.html` |
| [组织成员](https://vllm-hust.sage.org.ai/members.html)    | 公开成员与职责资料 | `members.html`      |

### 历史与兼容

| 页面                                                               | 用途                         | 路径                  |
| ------------------------------------------------------------------ | ---------------------------- | --------------------- |
| [历史 B0/B1 资料](https://vllm-hust.sage.org.ai/b0-b1-legacy.html) | 旧资料，不能作为当前版本验收依据 | `b0-b1-legacy.html`   |
| [旧 MOD 结果入口](https://vllm-hust.sage.org.ai/mod-results.html)  | 指向当前 MOD 目录的兼容入口  | `mod-results.html`    |
| [历史报告](https://vllm-hust.sage.org.ai/report-history.html)      | 按日期和版本查历史材料       | `report-history.html` |

### 技术资源

| 页面                                                                       | 用途                               | 路径                         |
| -------------------------------------------------------------------------- | ---------------------------------- | ---------------------------- |
| [演示播放器模板](https://vllm-hust.sage.org.ai/demos/player-template.html) | 模板资源，无独立标题，非主导航入口 | `demos/player-template.html` |
| [r8 wheel 索引](https://vllm-hust.sage.org.ai/wheels/r8.html)              | 安装包索引，非介绍页               | `wheels/r8.html`             |

## 关联项目外站

下列地址来自组织内 Fork 仓库的登记字段或 README，是关联项目入口，不据此认定组织拥有或运维该域名。

| 关联仓库                                                          | 地址                                                  | 核对结果                                                                          |
| ----------------------------------------------------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------- |
| [EvoScientist](https://github.com/vLLM-HUST/EvoScientist)         | [evoscientist.ai](https://evoscientist.ai/)           | 可达；README 的 evoscientist.github.io 跳到同一站                                 |
| [claude-code-hust](https://github.com/vLLM-HUST/claude-code-hust) | [登记主页](https://claudecode-haha.relakkesyang.org/) | 可达；README 使用的 claudecode-hust.relakkesyang.org DNS 无法解析，两个字段不一致 |

## 上游及第三方参考

这些是仓库登记的上游/参考主页，不属于本组织官网目录，也不代表本组织为这些服务提供运维。

| 仓库                                                                        | 登记入口                                               |
| --------------------------------------------------------------------------- | ------------------------------------------------------ |
| [triton-ascend-hust](https://github.com/vLLM-HUST/triton-ascend-hust)       | [主页](https://triton-ascend.readthedocs.io)           |
| [vllm-ascend-hust](https://github.com/vLLM-HUST/vllm-ascend-hust)           | [主页](https://docs.vllm.ai/projects/ascend)           |
| [sglang-hust](https://github.com/vLLM-HUST/sglang-hust)                     | [主页](https://sglang.io)                              |
| [vllm-hust](https://github.com/vLLM-HUST/vllm-hust)                         | [主页](https://vllm.ai)                                |
| [production-stack-hust](https://github.com/vLLM-HUST/production-stack-hust) | [主页](https://docs.vllm.ai/projects/production-stack) |
| [mooncake-hust](https://github.com/vLLM-HUST/mooncake-hust)                 | [主页](https://kvcache-ai.github.io/Mooncake/)         |
| [hust-agentperf](https://github.com/vLLM-HUST/hust-agentperf)               | [主页](https://artificialanalysis.ai)                  |

## 服务接口与示例地址

公开 README 中的 api.sage.org.ai、ws.sage.org.ai 是接口/实时连接相关地址，不作为普通内容网页；本轮没有发送业务请求或验证鉴权。
vllm-hust.example.com 是文档示例域名，不列为上线网站。仓库 Wiki 的 has_wiki 标志只表示功能可用，不能证明 Wiki 已初始化。

## 当前维护清单

| 优先级 | 项目                  | 已确认事实                                                         | 建议后续处理                                           |
| ------ | --------------------- | ------------------------------------------------------------------ | ------------------------------------------------------ |
| P2     | 官网强制 HTTPS        | Pages API 的 https_enforced 为 false；HTTP 响应 200 且未升级 HTTPS | 配置 HTTPS 强制跳转，并复核下载、旧地址和路径兼容      |
| P2     | Claude 项目入口不一致 | 登记主页可达；README 另一域名 DNS 失败                             | 由仓库维护者确认主域名后统一 README 和主页字段         |
| P3     | 历史及模板入口        | 历史 B0/B1、兼容页和播放器模板仍在部署产物内                       | 按用途保留；不要把旧资料、模板和当前产品页混为一个入口 |

本轮整理的是目录和归属，未调整域名、HTTPS、转向或应用服务配置。旧 github.io 的前端跳转已经确认正常，不计为重复内容问题。

## 来源和更新方式

- 公开仓库元数据与 README：GitHub 仓库 API；全量分页后按 public 筛选。仓库主页字段只是登记信息，不证明站点权属或可达性。
- 官网清单：Website 提交 `8e1895afe5c1c3403220752d6d4904cac827011a` 的
  [成功部署](https://github.com/vLLM-HUST/vllm-hust-website/actions/runs/44341568109)，从 Pages 产物列出 HTML
  文件并逐项读取。
- 网站数据来自 Benchmark
  固定提交；[数据来源清单](https://vllm-hust.sage.org.ai/data/benchmark-source-manifest.json)与[部署来源回执](https://vllm-hust.sage.org.ai/deployment-provenance.json)分别记录数据和页面身份。
- 变更后重新核对 Pages
  产物、仓库可见性、README/主页字段及最终跳转；同步本页、公开仓库入口和[机器可读清单](../web-inventory/public-web-inventory.json)，再同步原生
  Wiki。私有资料继续保留在内部清单。
