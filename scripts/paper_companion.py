#!/usr/bin/env python3
"""Utilities for lawful paper search, download, ingestion, and reading context."""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


DEFAULT_LIBRARY = Path.home() / "Papers" / "PaperCompanion"
USER_AGENT = "PaperCompanion/0.1 (+https://codex.local)"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}


def library_path(path: str | None) -> Path:
    base = Path(path).expanduser() if path else DEFAULT_LIBRARY
    try:
        for child in ("downloads", "metadata", "indexes", "notes"):
            (base / child).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        if path:
            raise
        base = Path.cwd() / ".paper-companion-library"
        for child in ("downloads", "metadata", "indexes", "notes"):
            (base / child).mkdir(parents=True, exist_ok=True)
        print(f"Default library is not writable; using {base}", file=sys.stderr)
    return base


def slugify(value: str, fallback: str = "paper") -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower()).strip("-")
    return value[:90] or fallback


def request_bytes(url: str, timeout: int = 45) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(), resp.headers.get("content-type", "")
    except (TimeoutError, urllib.error.URLError) as exc:
        raise SystemExit(f"Network request failed for {url}: {exc}") from exc


def command_search_arxiv(args: argparse.Namespace) -> None:
    base = library_path(args.library)
    params = {
        "search_query": f"all:{args.query}",
        "start": args.start,
        "max_results": args.count,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
    data, _ = request_bytes(url)
    root = ET.fromstring(data)
    results = []
    for entry in root.findall("atom:entry", ATOM_NS):
        arxiv_id_url = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
        arxiv_id = arxiv_id_url.rsplit("/", 1)[-1]
        title = " ".join(entry.findtext("atom:title", default="", namespaces=ATOM_NS).split())
        summary = " ".join(entry.findtext("atom:summary", default="", namespaces=ATOM_NS).split())
        authors = [
            node.findtext("atom:name", default="", namespaces=ATOM_NS)
            for node in entry.findall("atom:author", ATOM_NS)
        ]
        categories = [node.attrib.get("term", "") for node in entry.findall("atom:category", ATOM_NS)]
        published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
        pdf_url = ""
        for link in entry.findall("atom:link", ATOM_NS):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href", "")
                break
        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        results.append(
            {
                "source": "arXiv",
                "id": arxiv_id,
                "title": title,
                "authors": authors,
                "published": published,
                "categories": categories,
                "abstract": summary,
                "page_url": arxiv_id_url,
                "pdf_url": pdf_url,
            }
        )
    out = {"query": args.query, "source": "arxiv", "created_at": int(time.time()), "results": results}
    out_path = base / "metadata" / f"arxiv-{slugify(args.query)}.json"
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {out_path}")
    for idx, item in enumerate(results, 1):
        year = item["published"][:4] if item["published"] else "unknown"
        authors = ", ".join(item["authors"][:4])
        if len(item["authors"]) > 4:
            authors += ", et al."
        print(f"{idx}. {item['title']}")
        print(f"   {authors} ({year}) arXiv:{item['id']} categories={','.join(item['categories'][:4])}")
        print(f"   pdf={item['pdf_url']}")


def save_download(base: Path, url: str, title: str) -> Path:
    data, content_type = request_bytes(url, timeout=90)
    suffix = Path(urllib.parse.urlparse(url).path).suffix
    if "arxiv.org/pdf" in url or "pdf" in content_type.lower():
        suffix = ".pdf"
    elif not suffix or len(suffix) > 8:
        suffix = ".pdf" if "pdf" in content_type.lower() or "arxiv.org/pdf" in url else ".dat"
    path = base / "downloads" / f"{slugify(title)}{suffix}"
    path.write_bytes(data)
    print(f"Downloaded: {path}")
    return path


def command_download_arxiv(args: argparse.Namespace) -> None:
    base = library_path(args.library)
    data = json.loads(Path(args.result_file).expanduser().read_text(encoding="utf-8"))
    results = data.get("results", [])
    if args.index < 1 or args.index > len(results):
        raise SystemExit(f"--index must be between 1 and {len(results)}")
    item = results[args.index - 1]
    path = save_download(base, item["pdf_url"], item["title"])
    meta_path = base / "metadata" / f"{path.stem}.json"
    meta_path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Metadata: {meta_path}")


def command_download_url(args: argparse.Namespace) -> None:
    base = library_path(args.library)
    title = args.title or Path(urllib.parse.urlparse(args.url).path).stem or "paper"
    save_download(base, args.url, title)


def clean_text(text: str) -> str:
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:
        raise SystemExit("PDF ingestion requires pypdf. Install it or provide TXT/Markdown.") from exc
    reader = PdfReader(str(path))
    return clean_text("\n\n".join(page.extract_text() or "" for page in reader.pages))


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return extract_pdf(path)
    return clean_text(path.read_text(encoding="utf-8", errors="ignore"))


def split_chunks(text: str, size: int = 2200, overlap: int = 250) -> list[str]:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paras:
        if len(current) + len(para) + 2 <= size:
            current = f"{current}\n\n{para}".strip()
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    out = []
    tail = ""
    for chunk in chunks:
        out.append(f"{tail}\n\n{chunk}".strip() if tail else chunk)
        tail = chunk[-overlap:] if overlap > 0 else ""
    return out


def command_ingest(args: argparse.Namespace) -> None:
    base = library_path(args.library)
    path = Path(args.file).expanduser()
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    text = extract_text(path)
    chunks = split_chunks(text, args.chunk_size, args.overlap)
    out_path = base / "indexes" / f"{slugify(path.stem)}.jsonl"
    with out_path.open("w", encoding="utf-8") as out:
        for idx, chunk in enumerate(chunks, 1):
            out.write(json.dumps({"id": idx, "source_file": str(path), "text": chunk}, ensure_ascii=False) + "\n")
    print(f"Indexed {len(chunks)} chunks: {out_path}")


def load_index(path: Path) -> list[dict]:
    rows = []
    with path.expanduser().open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def command_context(args: argparse.Namespace) -> None:
    rows = load_index(Path(args.index_file))
    terms = [t.lower() for t in re.findall(r"\w+", args.query)]
    scored = []
    for row in rows:
        lowered = row["text"].lower()
        score = sum(lowered.count(term) for term in terms)
        if score:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    for score, row in scored[: args.limit]:
        excerpt = textwrap.shorten(" ".join(row["text"].split()), width=args.width)
        print(f"[chunk {row['id']} score={score}] {excerpt}")


def command_map(args: argparse.Namespace) -> None:
    rows = load_index(Path(args.index_file))
    title = args.title or Path(args.index_file).stem
    print("```mermaid")
    print("mindmap")
    print(f"  root(({title}))")
    print("    Problem")
    print("    Contribution")
    print("    Method")
    for row in rows[: args.chunks]:
        first = re.split(r"(?<=[.!?。！？])\s+", row["text"].strip())[0]
        label = textwrap.shorten(re.sub(r"[:()]", " ", first), width=70, placeholder="...")
        if label:
            print(f"      Chunk {row['id']}: {label}")
    print("    Evidence")
    print("    Limitations")
    print("    Follow-up questions")
    print("```")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", help="Library root. Defaults to ~/Papers/PaperCompanion.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search-arxiv", help="Search arXiv through the official API.")
    p.add_argument("query")
    p.add_argument("--count", type=int, default=10)
    p.add_argument("--start", type=int, default=0)
    p.set_defaults(func=command_search_arxiv)

    p = sub.add_parser("download-arxiv", help="Download a selected arXiv result PDF.")
    p.add_argument("--result-file", required=True)
    p.add_argument("--index", type=int, required=True)
    p.set_defaults(func=command_download_arxiv)

    p = sub.add_parser("download-url", help="Download a lawful direct paper URL.")
    p.add_argument("url")
    p.add_argument("--title")
    p.set_defaults(func=command_download_url)

    p = sub.add_parser("ingest", help="Extract and index PDF/TXT/Markdown.")
    p.add_argument("file")
    p.add_argument("--chunk-size", type=int, default=2200)
    p.add_argument("--overlap", type=int, default=250)
    p.set_defaults(func=command_ingest)

    p = sub.add_parser("context", help="Retrieve keyword context from an index.")
    p.add_argument("index_file")
    p.add_argument("--query", required=True)
    p.add_argument("--limit", type=int, default=8)
    p.add_argument("--width", type=int, default=300)
    p.set_defaults(func=command_context)

    p = sub.add_parser("map", help="Create a first-pass Mermaid paper map.")
    p.add_argument("index_file")
    p.add_argument("--title")
    p.add_argument("--chunks", type=int, default=8)
    p.set_defaults(func=command_map)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
