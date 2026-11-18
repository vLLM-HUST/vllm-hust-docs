# Wiki 维护

## 更新依据

| 信息 | 来源 | 更新时机 |
| --- | --- | --- |
| 仓库存在、可见性、Fork、归档 | [组织仓库 API](https://api.github.com/orgs/vLLM-HUST/repos?type=public&per_page=100) 和各仓库页面 | 创建、改名、迁移、归档或可见性变化 |
| 架构和兼容性 | [运行环境矩阵](https://github.com/vLLM-HUST/vllm-hust-dev-hub/blob/main/docs/ascend-official-runtime-support-matrix.zh-CN.md)、[组织文档](https://github.com/vLLM-HUST/vllm-hust-docs)、实现仓和发布记录 | 核心基线或扩展协议变动 |
| 公开贡献与维护 | [贡献者站点](https://vllm-hust.sage.org.ai/contributors.html)、项目 README、Issue 和仓库级规则 | 公开职责或联系入口调整 |
| 工作状态 | [开放 Issues](https://github.com/issues?q=org%3AvLLM-HUST+is%3Aopen+is%3Aissue+is%3Apublic) 和 [开放 PRs](https://github.com/pulls?q=org%3AvLLM-HUST+is%3Aopen+is%3Apr+is%3Apublic) | 每轮工作盘点更新精选入口和盘点日期 |
| 实测与官网来源 | [Benchmark 数据索引](https://github.com/vLLM-HUST/vllm-hust-benchmark/blob/main/DATA_INDEX.md)、固定提交和官网来源面板 | 新结果、订正、报告口径或发布版本变化 |

API 分页以响应的 `Link` 为准。更新目录时逐项核对新增和缺失的仓库，保留仍用于引用的归档条目。发版前用未登录身份检查所有发布页和导航链接。具体版本、部署参数和实验数值通过源仓链接引用，以便后续跟随维护。

## 发布到 GitHub Wiki

GitHub Wiki 挂在仓库下。可使用公开组织资料仓库 `vLLM-HUST/.github` 的 Wiki 作为组织入口。

1. 由有写权限的维护者打开 [资料仓库的 Wiki](https://github.com/vLLM-HUST/.github/wiki)。如果入口还没有首篇页面，从仓库 Wiki 标签创建 `Home`。
2. 首篇页面存在后，克隆独立 Wiki 仓库 `https://github.com/vLLM-HUST/.github.wiki.git`。先获取现有页面，按页面合并本目录的正文和 `_Sidebar.md`。
3. GitHub Wiki 使用省略 `.md` 的页面链接。发布副本把正文中的 `(Architecture.md)`、`(Home.md)` 等内部链接转为 `(Architecture)`、`(Home)`，外部链接原样保留。
4. 检查首页和侧边栏中的中文链接，提交后用无需登录的浏览器访问 [Wiki 首页](https://github.com/vLLM-HUST/.github/wiki/Home)，再将入口加到 [组织主页 README](https://github.com/vLLM-HUST/.github/blob/main/profile/README.md)。

[GitHub Wiki 文档](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages)


## 网站目录更新

新增或调整网站入口时同步[网站与网页总索引](Websites.md)、[公开仓库网页入口](Web-Repositories.md)和机器清单。公开版本按当前可见性筛选；私有仓库资料只进入内部清单。Pages 标志、Wiki 功能标志、登记主页、真实浏览器跳转和运行状态分别核对，不能彼此替代。
