# vLLM-HUST Introduction Slides

这是一套长期复用的 vLLM-HUST 介绍性质 slides，适合项目概览、技术宣讲、合作交流和阶段汇报时复用。

## 文件

- `vllm-hust-introduction.tex`：主 slides 源文件
- `Makefile`：基于 `tectonic` 的构建入口
- `sources/`：归档的历史申报材料源文件，仅用于内容追溯，不参与构建

## 构建

```bash
cd /home/shuhao/vllm-hust-docs/presentations/vllm-hust-introduction
make
```

生成的 PDF 位于：

```bash
build/vllm-hust-introduction.pdf
```

## 依赖

- `tectonic`
- `make`

## 字体

- 该目录内置 `fonts/NotoSansCJKsc-Regular.otf` 与 `fonts/NotoSansCJKsc-Bold.otf`，用于保证 `tectonic` 在不同机器上都能稳定渲染完整中文字符集。
- 字体许可证随仓库保存于 `fonts/LICENSE.notofonts-noto-cjk.txt`。

## 内容来源

- `vllm-hust` README 与代码结构
- `vllm-hust-docs/architecture/*`
- `sources/课题4-课题实施方案_0319.pptx/.md`
- `vllm-hust-workstation` README 与阶段汇报 deck
- `vllm-hust-website` README
- `ascend-runtime-manager` README
- `vllm-hust-benchmark` README
- `EvoScientist` README

## 使用建议

- 如需对外汇报，可修改封面作者、单位、日期和页尾文案。
- 如需更正式的项目申报风格，可在此基础上增加“研究背景”“项目映射”“考核指标”几页。