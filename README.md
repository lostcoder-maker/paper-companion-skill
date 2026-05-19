# Paper Companion Skill

Paper Companion 是一个用于“找论文、下载开放论文、建立本地论文库、辅助阅读论文”的 Codex Skill。

它适合这些场景：

- 按主题搜索论文。
- 下载合法开放的 PDF。
- 把论文保存到本地论文库。
- 从 PDF、TXT、Markdown 中抽取文本并切块索引。
- 基于索引内容做有依据的问答。
- 生成论文笔记、方法拆解、局限性检查、相关工作表格和 Mermaid 概念图。

## 当前支持的论文来源

当前脚本已经实现：

- **arXiv**：通过官方 arXiv API 搜索论文，并下载官方 PDF。
- **用户提供的合法 PDF 直链**：例如出版社开放获取 PDF、机构仓储 PDF、作者公开页面 PDF 等。
- **用户本地文件**：支持索引用户已有的 PDF、TXT、Markdown 文件。

Skill 文档中也预留了后续可扩展的安全来源：

- PubMed Central 开放全文。
- DOI 出版商页面中明确开放的 PDF。
- 大学或研究机构仓储。
- OpenAlex / Semantic Scholar 的元数据与开放获取位置发现。

这个 Skill 不支持，也不会支持：

- 绕过付费墙。
- Sci-Hub 类镜像。
- DRM 移除。
- 复用私人凭证批量抓取。
- 未授权论文下载。

## 仓库结构

```text
.
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── reading.md
│   └── sources.md
└── scripts/
    └── paper_companion.py
```

## 本地论文库结构

默认论文库位置：

```text
~/Papers/PaperCompanion/
  downloads/   # 下载或导入的论文文件
  metadata/    # 搜索结果和论文元数据
  indexes/     # 论文切块索引 JSONL
  notes/       # 生成的笔记、摘要、图谱
```

在 Codex 沙盒环境里，如果 `~/Papers` 不可写，脚本会自动退回当前目录下的：

```text
.paper-companion-library/
```

也可以用 `--library` 手动指定论文库位置。

## 常用命令

搜索 arXiv：

```bash
scripts/paper_companion.py search-arxiv "Bayesian network structure learning"
```

下载某条 arXiv 搜索结果：

```bash
scripts/paper_companion.py download-arxiv \
  --result-file ~/Papers/PaperCompanion/metadata/arxiv-bayesian-network-structure-learning.json \
  --index 1
```

下载合法 PDF 直链：

```bash
scripts/paper_companion.py download-url \
  "https://arxiv.org/pdf/1706.03762" \
  --title "Attention Is All You Need"
```

索引本地论文：

```bash
scripts/paper_companion.py ingest "~/Papers/PaperCompanion/downloads/attention-is-all-you-need.pdf"
```

从索引中检索上下文：

```bash
scripts/paper_companion.py context \
  "~/Papers/PaperCompanion/indexes/attention-is-all-you-need.jsonl" \
  --query "positional encoding"
```

生成第一版论文结构图：

```bash
scripts/paper_companion.py map \
  "~/Papers/PaperCompanion/indexes/attention-is-all-you-need.jsonl" \
  --title "Attention Is All You Need"
```

## 阅读辅助能力

这个 Skill 会引导 Codex 按论文阅读流程工作：

- 快速判断论文是否值得读。
- 提炼问题、贡献、方法、证据和局限。
- 拆解实验设计和核心假设。
- 抽取关键 claim，并区分证据与推测。
- 对多篇论文做相关工作对比。
- 生成结构化读书笔记和概念图。

## 依赖说明

PDF 文本抽取需要 `pypdf`。如果没有安装 `pypdf`，仍然可以索引 TXT 和 Markdown 文件。

搜索和下载层故意保持保守：如果某篇论文没有合法开放 PDF，Skill 会只保留元数据，并要求用户提供授权获得的本地文件后再索引阅读。
