---
name: paper-companion
description: Find open-access research papers, download lawful PDFs, maintain a local paper library, index PDF/TXT files, and help read papers through grounded summaries, contribution/method/evidence/limitation analysis, related-work maps, claim extraction, and study notes. Use when the user asks to search arXiv/open-access papers, download papers, understand a paper, compare papers, create paper notes, or build a literature review from local or open papers.
---

# Paper Companion

## Core Rule

Use official or lawful paper sources only: arXiv, PubMed Central, DOI publisher pages with open PDFs, institutional repositories, OpenAlex/Semantic Scholar metadata, and user-provided files. Do not bypass paywalls, remove DRM, use Sci-Hub-style mirrors, or retrieve copyrighted PDFs from unauthorized sources.

## Default Library

Use `~/Papers/PaperCompanion` unless the user specifies another path. In sandboxed Codex sessions where that path is not writable, the helper script falls back to `.paper-companion-library` in the current working directory.

```
~/Papers/PaperCompanion/
  downloads/   # PDF/TXT files
  metadata/    # search results and paper metadata JSON
  indexes/     # extracted chunk JSONL
  notes/       # generated notes, summaries, maps
```

## Workflow

1. **Search**: Use `scripts/paper_companion.py search-arxiv "<query>"`. Show numbered results with title, authors, year, arXiv id, categories, and PDF URL.
2. **Download**: Use `download-arxiv --result-file <json> --index N` or `download-url <lawful-pdf-url> --title ...`.
3. **Ingest**: Use `ingest <file>` to extract and chunk PDF/TXT/Markdown into an index.
4. **Read**: Use `context` to retrieve relevant chunks before answering. Ground answers in chunk ids, section names, or quoted short snippets.
5. **Produce paper artifacts**: Save durable outputs in `notes/` when requested: structured paper note, method breakdown, limitations, related-work table, or Mermaid concept map.

## Common Commands

Search arXiv:

```bash
scripts/paper_companion.py search-arxiv "retrieval augmented generation evaluation"
```

Download a search result:

```bash
scripts/paper_companion.py download-arxiv --result-file ~/Papers/PaperCompanion/metadata/arxiv-retrieval-augmented-generation-evaluation.json --index 1
```

Download a lawful direct PDF URL:

```bash
scripts/paper_companion.py download-url "https://arxiv.org/pdf/1706.03762" --title "Attention Is All You Need"
```

Index a paper:

```bash
scripts/paper_companion.py ingest "~/Papers/PaperCompanion/downloads/attention-is-all-you-need.pdf"
```

Find relevant passages:

```bash
scripts/paper_companion.py context "~/Papers/PaperCompanion/indexes/attention-is-all-you-need.jsonl" --query "positional encoding"
```

Create a first-pass paper map:

```bash
scripts/paper_companion.py map "~/Papers/PaperCompanion/indexes/attention-is-all-you-need.jsonl" --title "Attention Is All You Need"
```

## Reading Patterns

- **Fast triage**: problem, contribution, method, evidence, limitations, should-read sections.
- **Deep read**: define terms, reconstruct assumptions, trace method pipeline, inspect experiments, identify threats to validity.
- **Literature review**: compare papers by problem, method, data, metrics, claims, limitations, and reusable ideas.
- **Claim extraction**: separate claims, evidence, caveats, and unsupported leaps.
- **Implementation notes**: identify algorithm steps, inputs/outputs, hyperparameters, and missing details.

## References

- Load `references/sources.md` when choosing paper sources or explaining access rules.
- Load `references/reading.md` when creating paper notes, literature reviews, or concept maps.
