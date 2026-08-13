from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sqlite3
import sys
import unicodedata
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from .constants import CHAPTERS, DOC_FILES, GLOBAL_FILES, ROOT_DIRS, SCHEMA_FILES, TEMPLATES, VECTORS
from .master_paper import build_master_paper
from .book import build_site, export_book, generate_book_assets, seed_book
from .book_print import build_book_print, export_book_print, review_book_print
from .papers import export_papers, seed_papers
from .publication_review import review_publication
from .website import build_website
from .fs import append_jsonl, dump_json, ensure_dir, list_markdown_files, load_jsonl, overwrite, write_if_missing

EVIDENCE_LABEL_MAP = {
    "Documented fact": "Documented Fact",
    "Documented Fact": "Documented Fact",
    "Disputed fact": "Disputed Fact",
    "Disputed Fact": "Disputed Fact",
    "Hypothesis / interpretation": "Hypothesis / Interpretation",
    "Hypothesis / Interpretation": "Hypothesis / Interpretation",
    "Speculative narrative risk": "Speculative Narrative Risk",
    "Speculative Narrative Risk": "Speculative Narrative Risk",
}

EVIDENCE_LEVELS = [
    "Documented Fact",
    "Disputed Fact",
    "Hypothesis / Interpretation",
    "Speculative Narrative Risk",
]


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self) -> str:
        return "\n".join(self.parts)


def now_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def vector_by_id(vector_id: str) -> dict:
    for vector in VECTORS:
        if vector["id"] == vector_id:
            return vector
    raise KeyError(f"Unknown vector id: {vector_id}")


def chapter_by_id(chapter_id: str) -> dict:
    for chapter in CHAPTERS:
        if chapter["id"] == chapter_id:
            return chapter
    raise KeyError(f"Unknown chapter id: {chapter_id}")


def chapter_ids_for_vectors(vector_ids: list[str]) -> list[str]:
    chapter_ids: list[str] = []
    for vector_id in vector_ids:
        for chapter_id in vector_by_id(vector_id)["chapter_ids"]:
            if chapter_id not in chapter_ids:
                chapter_ids.append(chapter_id)
    return chapter_ids


def format_bullet_list(values: list[str]) -> str:
    return "\n".join(f"- `{value}`" for value in values) if values else "- No items are registered yet."


def normalize_evidence_level(value: str | None) -> str:
    if value is None:
        return "Documented Fact"
    return EVIDENCE_LABEL_MAP.get(value, value)


def filter_claims_by_level(claim_records: list[dict], evidence_level: str) -> list[dict]:
    return [record for record in claim_records if normalize_evidence_level(record.get("evidence_level")) == evidence_level]


def load_template(root: Path, template_name: str) -> str:
    path = root / template_name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return TEMPLATES[template_name]


def init_repo(root: Path) -> None:
    for directory in ROOT_DIRS:
        ensure_dir(root / directory)

    for path, content in DOC_FILES.items():
        write_if_missing(root / path, content)

    for path, content in SCHEMA_FILES.items():
        write_if_missing(root / path, content)

    for path, content in TEMPLATES.items():
        write_if_missing(root / path, content)

    for file_path in GLOBAL_FILES:
        write_if_missing(root / file_path, "")

    chapter_map = {
        "chapters": [
            {
                "chapter_id": chapter["id"],
                "title": chapter["title"],
                "core_thesis": chapter["core_thesis"],
                "vector_ids": chapter["vector_ids"],
            }
            for chapter in CHAPTERS
        ]
    }
    dump_json(root / "chapters/chapter_map.json", chapter_map)

    vector_template = load_template(root, "apps/templates/vector_readme.md.tmpl")
    queue_template = load_template(root, "apps/templates/queue.md.tmpl")
    bridge_template = load_template(root, "apps/templates/chapter_bridge.md.tmpl")
    chapter_template = load_template(root, "apps/templates/chapter_brief.md.tmpl")
    dossier_template = load_template(root, "apps/templates/dossier_master.md.tmpl")

    for vector in VECTORS:
        vector_root = root / "vectors" / vector["id"]
        for subdir in ["raw", "notes", "summaries", "claims", "entities", "timeline"]:
            ensure_dir(vector_root / subdir)
        write_if_missing(
            vector_root / "README.md",
            vector_template.format(
                id=vector["id"],
                title=vector["title"],
                chapter_list=format_bullet_list(vector["chapter_ids"]),
                summary=vector["summary"],
            ),
        )
        write_if_missing(vector_root / "queue.md", queue_template)
        write_if_missing(
            vector_root / "chapter_bridge.md",
            bridge_template.format(
                id=vector["id"],
                chapter_list=format_bullet_list(vector["chapter_ids"]),
            ),
        )

    for chapter in CHAPTERS:
        filename = f"{chapter['id']}_{slugify(chapter['title'])}.md"
        write_if_missing(
            root / "chapters" / filename,
            chapter_template.format(
                id=chapter["id"],
                title=chapter["title"],
                core_thesis=chapter["core_thesis"],
                vector_list=format_bullet_list(chapter["vector_ids"]),
            ),
        )

    chapter_outline = "\n".join(f"- Chapter {chapter['id']}: {chapter['title']}" for chapter in CHAPTERS)
    write_if_missing(root / "drafts/dossier_master.md", dossier_template.format(chapter_outline=chapter_outline))

    write_if_missing(root / "apps/browser_worker/README.md", BROWSER_README)
    write_if_missing(root / "apps/browser_worker/capture_page.mjs", BROWSER_WORKER)


def slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower())
    return normalized.strip("-")


def add_source(args: argparse.Namespace) -> None:
    root = Path(args.root)
    vector_ids = split_csv(args.vectors)
    chapter_ids = split_csv(args.chapter_ids) or chapter_ids_for_vectors(vector_ids)
    record = {
        "source_id": args.source_id,
        "title": args.title,
        "author": args.author,
        "publisher": args.publisher,
        "published_at": args.published_at,
        "captured_at": now_iso(),
        "url": args.url,
        "source_tier": args.source_tier,
        "source_type": args.source_type,
        "vector_ids": vector_ids,
        "chapter_ids": chapter_ids,
        "language": args.language,
        "reliability_notes": args.reliability_notes,
        "local_paths": [],
    }
    append_jsonl(root / "sources/catalog.jsonl", record)

    note_template = load_template(root, "apps/templates/source_note.md.tmpl")
    primary_vector = vector_ids[0]
    note_path = root / "vectors" / primary_vector / "notes" / f"{args.source_id}.md"
    write_if_missing(
        note_path,
        note_template.format(
            source_id=args.source_id,
            vector_ids=json.dumps(vector_ids, ensure_ascii=False),
            chapter_ids=json.dumps(chapter_ids, ensure_ascii=False),
            source_tier=args.source_tier,
            source_type=args.source_type,
            url=args.url,
            published_at=args.published_at or "",
            captured_at=now_iso(),
            title=args.title,
        ),
    )


def save_jsonl(path: Path, records: list[dict]) -> None:
    content = "\n".join(json.dumps(record, ensure_ascii=False) for record in records)
    overwrite(path, content + ("\n" if content else ""))


def update_source_local_paths(root: Path, source_id: str, local_paths: list[str]) -> None:
    catalog_path = root / "sources/catalog.jsonl"
    records = load_jsonl(catalog_path)
    for record in records:
        if record.get("source_id") == source_id:
            existing = record.get("local_paths", [])
            merged = list(dict.fromkeys(existing + local_paths))
            record["local_paths"] = merged
            break
    save_jsonl(catalog_path, records)


def capture_web(args: argparse.Namespace) -> None:
    root = Path(args.root)
    vector_root = root / "vectors" / args.vector_id / "raw"
    ensure_dir(vector_root)
    request = urllib.request.Request(
        args.url,
        headers={"User-Agent": "AI-Empire-Research-OS/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
        html = body.decode("utf-8", errors="replace")
    html_path = vector_root / f"{args.source_id}.html"
    text_path = vector_root / f"{args.source_id}.txt"
    metadata_path = vector_root / f"{args.source_id}.meta.json"
    overwrite(html_path, html)
    parser = TextExtractor()
    parser.feed(html)
    overwrite(text_path, parser.get_text())
    dump_json(
        metadata_path,
        {
            "source_id": args.source_id,
            "url": args.url,
            "captured_at": now_iso(),
            "mode": "capture-web",
            "vector_id": args.vector_id,
            "paths": [str(html_path), str(text_path)],
        },
    )
    update_source_local_paths(root, args.source_id, [str(html_path), str(text_path), str(metadata_path)])


def capture_browser(args: argparse.Namespace) -> None:
    root = Path(args.root)
    job_path = root / "sources/browser_jobs" / f"{args.source_id}.json"
    payload = {
        "source_id": args.source_id,
        "url": args.url,
        "vector_id": args.vector_id,
        "output_dir": str(root / "vectors" / args.vector_id / "raw"),
        "capture_screenshot": bool(args.capture_screenshot),
        "created_at": now_iso(),
    }
    dump_json(job_path, payload)
    print(f"Browser job created: {job_path}")
    print("Use apps/browser_worker/capture_page.mjs from the in-app browser runtime to execute the capture.")


def ingest_pdf(args: argparse.Namespace) -> None:
    root = Path(args.root)
    source_path = Path(args.path)
    vector_root = root / "vectors" / args.vector_id / "raw"
    ensure_dir(vector_root)
    target_pdf = vector_root / f"{args.source_id}{source_path.suffix or '.pdf'}"
    shutil.copyfile(source_path, target_pdf)
    extracted_text = ""
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(target_pdf))
        extracted_text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:  # pragma: no cover - best effort extraction
        extracted_text = f"[PDF extraction failed] {exc}"
    overwrite(vector_root / f"{args.source_id}.txt", extracted_text)
    dump_json(
        vector_root / f"{args.source_id}.meta.json",
        {
            "source_id": args.source_id,
            "vector_id": args.vector_id,
            "captured_at": now_iso(),
            "mode": "ingest-pdf",
            "paths": [str(target_pdf), str(vector_root / f"{args.source_id}.txt")],
        },
    )
    update_source_local_paths(
        root,
        args.source_id,
        [
            str(target_pdf),
            str(vector_root / f"{args.source_id}.txt"),
            str(vector_root / f"{args.source_id}.meta.json"),
        ],
    )


def ingest_transcript(args: argparse.Namespace) -> None:
    root = Path(args.root)
    source_path = Path(args.path)
    vector_root = root / "vectors" / args.vector_id / "raw"
    ensure_dir(vector_root)
    content = source_path.read_text(encoding="utf-8")
    target_path = vector_root / f"{args.source_id}.transcript.txt"
    overwrite(target_path, content)
    dump_json(
        vector_root / f"{args.source_id}.meta.json",
        {
            "source_id": args.source_id,
            "vector_id": args.vector_id,
            "captured_at": now_iso(),
            "mode": "ingest-transcript",
            "paths": [str(target_path)],
        },
    )
    update_source_local_paths(root, args.source_id, [str(target_path), str(vector_root / f"{args.source_id}.meta.json")])


def sync_source_artifacts(args: argparse.Namespace) -> None:
    root = Path(args.root)
    vector_raw = root / "vectors" / args.vector_id / "raw"
    local_paths = [str(path) for path in sorted(vector_raw.glob(f"{args.source_id}*")) if path.is_file()]
    update_source_local_paths(root, args.source_id, local_paths)


def summarize_source(args: argparse.Namespace) -> None:
    root = Path(args.root)
    note_path = root / "vectors" / args.vector_id / "notes" / f"{args.source_id}.md"
    raw_dir = root / "vectors" / args.vector_id / "raw"
    candidate_text = ""
    for suffix in [".txt", ".dom.txt", ".transcript.txt"]:
        path = raw_dir / f"{args.source_id}{suffix}"
        if path.exists():
            candidate_text = path.read_text(encoding="utf-8")
            break
    summary_lines = [line.strip() for line in candidate_text.splitlines() if line.strip()][:12]
    preview = "\n".join(f"- {line}" for line in summary_lines[:5]) or "- No normalized text is available yet."
    content = note_path.read_text(encoding="utf-8")
    content = re.sub(r"## Factual Summary\n\n- Complete\.", f"## Factual Summary\n\n{preview}", content)
    content = re.sub(
        r"## What It Suggests\n\n- Complete\.",
        "## What It Suggests\n\n- Review causal relationships carefully before elevating them into a thesis.",
        content,
    )
    overwrite(note_path, content)


def extract_claims(args: argparse.Namespace) -> None:
    root = Path(args.root)
    note_path = root / "vectors" / args.vector_id / "notes" / f"{args.source_id}.md"
    content = note_path.read_text(encoding="utf-8")
    section = extract_section(content, "## What It Proves")
    claims = [line[2:].strip() for line in section.splitlines() if line.startswith("- ")]
    frontmatter = parse_frontmatter(content)
    chapter_ids = frontmatter.get("chapter_ids") or chapter_ids_for_vectors([args.vector_id])
    vector_slug = slugify(args.vector_id)
    for index, claim in enumerate(claims, start=1):
        record = {
            "claim_id": f"{args.source_id}-{vector_slug}-claim-{index:02d}",
            "claim_text": claim,
            "claim_type": "source-derived",
            "evidence_level": normalize_evidence_level(args.evidence_level),
            "vector_id": args.vector_id,
            "source_ids": [args.source_id],
            "counterevidence_ids": [],
            "chapter_ids": chapter_ids,
            "legal_risk": args.legal_risk,
            "editorial_note": "Generated from the note section 'What It Proves'.",
        }
        append_jsonl(root / "claims/master_claims.jsonl", record)


def build_index(args: argparse.Namespace) -> None:
    root = Path(args.root)
    db_path = root / "sources" / "research_index.sqlite"
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE sources(source_id TEXT PRIMARY KEY, title TEXT, publisher TEXT, source_tier TEXT, source_type TEXT, url TEXT, payload TEXT);
        CREATE TABLE claims(claim_id TEXT PRIMARY KEY, claim_text TEXT, vector_id TEXT, evidence_level TEXT, payload TEXT);
        CREATE TABLE entities(entity_id TEXT PRIMARY KEY, name TEXT, entity_type TEXT, payload TEXT);
        CREATE TABLE timelines(event_id TEXT PRIMARY KEY, label TEXT, date TEXT, payload TEXT);
        CREATE VIRTUAL TABLE notes_fts USING fts5(path, body);
        CREATE VIRTUAL TABLE claims_fts USING fts5(claim_id, claim_text, vector_id, evidence_level);
        """
    )
    for record in load_jsonl(root / "sources/catalog.jsonl"):
        conn.execute(
            "INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                record["source_id"],
                record.get("title"),
                record.get("publisher"),
                record.get("source_tier"),
                record.get("source_type"),
                record.get("url"),
                json.dumps(record, ensure_ascii=False),
            ),
        )
    for record in load_jsonl(root / "claims/master_claims.jsonl"):
        conn.execute(
            "INSERT INTO claims VALUES (?, ?, ?, ?, ?)",
            (
                record["claim_id"],
                record.get("claim_text"),
                record.get("vector_id"),
                record.get("evidence_level"),
                json.dumps(record, ensure_ascii=False),
            ),
        )
        conn.execute(
            "INSERT INTO claims_fts VALUES (?, ?, ?, ?)",
            (
                record["claim_id"],
                record.get("claim_text"),
                record.get("vector_id"),
                record.get("evidence_level"),
            ),
        )
    for record in load_jsonl(root / "profiles/entities.jsonl"):
        conn.execute(
            "INSERT INTO entities VALUES (?, ?, ?, ?)",
            (
                record["entity_id"],
                record.get("name"),
                record.get("entity_type"),
                json.dumps(record, ensure_ascii=False),
            ),
        )
    for record in load_jsonl(root / "timelines/master_timeline.jsonl"):
        conn.execute(
            "INSERT INTO timelines VALUES (?, ?, ?, ?)",
            (
                record["event_id"],
                record.get("label"),
                record.get("date"),
                json.dumps(record, ensure_ascii=False),
            ),
        )
    for note_path in list_markdown_files([root / "vectors"]):
        body = note_path.read_text(encoding="utf-8")
        conn.execute("INSERT INTO notes_fts VALUES (?, ?)", (str(note_path.relative_to(root)), body))
    conn.commit()
    conn.close()


def vector_report(args: argparse.Namespace) -> None:
    root = Path(args.root)
    vector = vector_by_id(args.vector_id)
    source_records = [record for record in load_jsonl(root / "sources/catalog.jsonl") if args.vector_id in record.get("vector_ids", [])]
    claim_records = [record for record in load_jsonl(root / "claims/master_claims.jsonl") if record.get("vector_id") == args.vector_id]
    established = filter_claims_by_level(claim_records, "Documented Fact")
    disputed = filter_claims_by_level(claim_records, "Disputed Fact")
    hypotheses = filter_claims_by_level(claim_records, "Hypothesis / Interpretation")
    speculative = filter_claims_by_level(claim_records, "Speculative Narrative Risk")
    report = [
        f"# Vector Report: {vector['title']}",
        "",
        "## ID",
        "",
        f"`{args.vector_id}`",
        "",
        "## Status",
        "",
        f"- Registered sources: {len(source_records)}",
        f"- Registered claims: {len(claim_records)}",
        f"- Connected chapters: {', '.join(vector['chapter_ids'])}",
        "",
        "## Registered Sources",
        "",
    ]
    if source_records:
        report.extend(f"- `{record['source_id']}`: {record['title']} ({record['source_tier']})" for record in source_records)
    else:
        report.append("- No sources are registered yet. Add backbone material before drafting from this vector.")
    report.extend(["", "## Documented Facts", ""])
    if established:
        report.extend(f"- {record['claim_text']}" for record in established)
    else:
        report.append("- No documented-fact claims are registered yet. Add source-bound claims before relying on this vector.")
    report.extend(["", "## Disputed Facts", ""])
    if disputed:
        report.extend(f"- {record['claim_text']}" for record in disputed)
    else:
        report.append("- No dedicated disputed-fact claims are registered yet; current uncertainty may still appear in limits, hypotheses, or risk boundaries.")
    report.extend(["", "## Hypotheses / Interpretations", ""])
    if hypotheses:
        report.extend(f"- {record['claim_text']}" for record in hypotheses)
    else:
        report.append("- No interpretive synthesis claims are registered yet. Add bounded political readings before prose hardening.")
    report.extend(["", "## Speculative Narrative Risks", ""])
    if speculative:
        report.extend(f"- {record['claim_text']}" for record in speculative)
    else:
        report.append("- No speculative-narrative risk boundaries are registered yet. Add overclaim limits before publication-grade drafting.")
    report.extend(["", "## Gaps", "", "- Review `queue.md` and unresolved evidentiary weak spots before prose hardening."])
    overwrite(root / "vectors" / args.vector_id / "summaries" / "vector-report.md", "\n".join(report) + "\n")


def chapter_brief(args: argparse.Namespace) -> None:
    root = Path(args.root)
    chapter = chapter_by_id(args.chapter_id)
    claims = [
        record for record in load_jsonl(root / "claims/master_claims.jsonl") if args.chapter_id in record.get("chapter_ids", [])
    ]
    documented = filter_claims_by_level(claims, "Documented Fact")
    disputed = filter_claims_by_level(claims, "Disputed Fact")
    interpretive = filter_claims_by_level(claims, "Hypothesis / Interpretation")
    speculative = filter_claims_by_level(claims, "Speculative Narrative Risk")
    sources = [
        record for record in load_jsonl(root / "sources/catalog.jsonl") if set(record.get("chapter_ids", [])) & {args.chapter_id}
    ]
    lines = [
        f"# Chapter {chapter['id']}: {chapter['title']}",
        "",
        "## Core Thesis",
        "",
        chapter["core_thesis"],
        "",
        "## Connected Vectors",
        "",
        format_bullet_list(chapter["vector_ids"]),
        "",
        "## Documented Claims",
        "",
    ]
    if documented:
        lines.extend(f"- {claim['claim_text']}" for claim in documented)
    else:
        lines.append("- No documented-fact claims are registered yet for this chapter.")
    lines.extend(["", "## Disputed Claims", ""])
    if disputed:
        lines.extend(f"- {claim['claim_text']}" for claim in disputed)
    else:
        lines.append("- No dedicated disputed claims are registered yet for this chapter.")
    lines.extend(["", "## Interpretive Claims", ""])
    if interpretive:
        lines.extend(f"- {claim['claim_text']}" for claim in interpretive)
    else:
        lines.append("- No interpretive claims are registered yet for this chapter.")
    lines.extend(["", "## Speculative Narrative Risks", ""])
    if speculative:
        lines.extend(f"- {claim['claim_text']}" for claim in speculative)
    else:
        lines.append("- No speculative-narrative risk boundaries are registered yet for this chapter.")
    lines.extend(
        [
            "",
            "## Backbone Sources",
            "",
        ]
    )
    if sources:
        lines.extend(f"- `{source['source_id']}`: {source['title']}" for source in sources[:10])
    else:
        lines.append("- No backbone sources are registered yet for this chapter.")
    lines.extend(
        [
            "",
            "## Foreseeable Objections",
            "",
            "- Mark causal limits and evidence gaps.",
            "",
            "## Limits of the Evidence",
            "",
            "- Review sensitive claims before moving into continuous prose.",
        ]
    )
    filename = f"{chapter['id']}_{slugify(chapter['title'])}.md"
    overwrite(root / "chapters" / filename, "\n".join(lines) + "\n")


def dossier_outline(args: argparse.Namespace) -> None:
    root = Path(args.root)
    lines = [
        "# Long Dossier: from surveillance capitalism to AI imperialism",
        "",
        "## Status",
        "",
        "Structural master draft. It does not replace the final written dossier.",
        "",
        "## Outline",
        "",
    ]
    for chapter in CHAPTERS:
        lines.append(f"### Chapter {chapter['id']}: {chapter['title']}")
        lines.append("")
        lines.append(f"- Thesis: {chapter['core_thesis']}")
        lines.append(f"- Vectors: {', '.join(chapter['vector_ids'])}")
        lines.append("")
    overwrite(root / "drafts/dossier_master.md", "\n".join(lines) + "\n")


def extract_section(content: str, heading: str) -> str:
    pattern = rf"{re.escape(heading)}\n\n(.*?)(?:\n## |\Z)"
    match = re.search(pattern, content, re.S)
    return match.group(1).strip() if match else ""


def parse_frontmatter(content: str) -> dict:
    if not content.startswith("---\n"):
        return {}
    _, remainder = content.split("---\n", 1)
    frontmatter_text, _, _ = remainder.partition("\n---\n")
    data: dict = {}
    for line in frontmatter_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            try:
                data[key] = json.loads(value)
                continue
            except json.JSONDecodeError:
                pass
        data[key] = value
    return data


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Research OS CLI")
    sub = p.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init-repo")
    init_cmd.add_argument("--root", required=True)

    add_cmd = sub.add_parser("add-source")
    add_cmd.add_argument("--root", required=True)
    add_cmd.add_argument("--source-id", required=True)
    add_cmd.add_argument("--title", required=True)
    add_cmd.add_argument("--url", required=True)
    add_cmd.add_argument("--publisher")
    add_cmd.add_argument("--author")
    add_cmd.add_argument("--published-at")
    add_cmd.add_argument("--source-tier", required=True, choices=["T1", "T2", "T3"])
    add_cmd.add_argument("--source-type", required=True)
    add_cmd.add_argument("--vectors", required=True)
    add_cmd.add_argument("--chapter-ids")
    add_cmd.add_argument("--language", default="en")
    add_cmd.add_argument("--reliability-notes")

    cap_web = sub.add_parser("capture-web")
    cap_web.add_argument("--root", required=True)
    cap_web.add_argument("--source-id", required=True)
    cap_web.add_argument("--vector-id", required=True)
    cap_web.add_argument("--url", required=True)

    cap_browser = sub.add_parser("capture-browser")
    cap_browser.add_argument("--root", required=True)
    cap_browser.add_argument("--source-id", required=True)
    cap_browser.add_argument("--vector-id", required=True)
    cap_browser.add_argument("--url", required=True)
    cap_browser.add_argument("--capture-screenshot", action="store_true")

    ingest_pdf_cmd = sub.add_parser("ingest-pdf")
    ingest_pdf_cmd.add_argument("--root", required=True)
    ingest_pdf_cmd.add_argument("--source-id", required=True)
    ingest_pdf_cmd.add_argument("--vector-id", required=True)
    ingest_pdf_cmd.add_argument("--path", required=True)

    ingest_tr_cmd = sub.add_parser("ingest-transcript")
    ingest_tr_cmd.add_argument("--root", required=True)
    ingest_tr_cmd.add_argument("--source-id", required=True)
    ingest_tr_cmd.add_argument("--vector-id", required=True)
    ingest_tr_cmd.add_argument("--path", required=True)

    sum_cmd = sub.add_parser("summarize-source")
    sum_cmd.add_argument("--root", required=True)
    sum_cmd.add_argument("--source-id", required=True)
    sum_cmd.add_argument("--vector-id", required=True)

    claim_cmd = sub.add_parser("extract-claims")
    claim_cmd.add_argument("--root", required=True)
    claim_cmd.add_argument("--source-id", required=True)
    claim_cmd.add_argument("--vector-id", required=True)
    claim_cmd.add_argument("--evidence-level", default="Documented Fact", choices=EVIDENCE_LEVELS)
    claim_cmd.add_argument("--legal-risk", default="review")

    index_cmd = sub.add_parser("build-index")
    index_cmd.add_argument("--root", required=True)

    sync_cmd = sub.add_parser("sync-source-artifacts")
    sync_cmd.add_argument("--root", required=True)
    sync_cmd.add_argument("--source-id", required=True)
    sync_cmd.add_argument("--vector-id", required=True)

    report_cmd = sub.add_parser("vector-report")
    report_cmd.add_argument("--root", required=True)
    report_cmd.add_argument("--vector-id", required=True)

    brief_cmd = sub.add_parser("chapter-brief")
    brief_cmd.add_argument("--root", required=True)
    brief_cmd.add_argument("--chapter-id", required=True)

    outline_cmd = sub.add_parser("dossier-outline")
    outline_cmd.add_argument("--root", required=True)

    seed_papers_cmd = sub.add_parser("seed-papers")
    seed_papers_cmd.add_argument("--root", required=True)
    seed_papers_cmd.add_argument("--overwrite", action="store_true")

    export_papers_cmd = sub.add_parser("export-papers")
    export_papers_cmd.add_argument("--root", required=True)

    build_master_paper_cmd = sub.add_parser("build-master-paper")
    build_master_paper_cmd.add_argument("--root", required=True)

    seed_book_cmd = sub.add_parser("seed-book")
    seed_book_cmd.add_argument("--root", required=True)
    seed_book_cmd.add_argument("--overwrite", action="store_true")

    export_book_cmd = sub.add_parser("export-book")
    export_book_cmd.add_argument("--root", required=True)

    build_book_print_cmd = sub.add_parser("build-book-print")
    build_book_print_cmd.add_argument("--root", required=True)

    export_book_print_cmd = sub.add_parser("export-book-print")
    export_book_print_cmd.add_argument("--root", required=True)

    review_book_print_cmd = sub.add_parser("review-book-print")
    review_book_print_cmd.add_argument("--root", required=True)

    generate_book_assets_cmd = sub.add_parser("generate-book-assets")
    generate_book_assets_cmd.add_argument("--root", required=True)
    generate_book_assets_cmd.add_argument("--kind", required=True, choices=["infographics"])
    generate_book_assets_cmd.add_argument("--chapter")
    generate_book_assets_cmd.add_argument("--asset")

    build_site_cmd = sub.add_parser("build-site")
    build_site_cmd.add_argument("--root", required=True)

    build_website_cmd = sub.add_parser("build-website")
    build_website_cmd.add_argument("--root", required=True)

    review_publication_cmd = sub.add_parser("review-publication")
    review_publication_cmd.add_argument("--root", required=True)

    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    command_map = {
        "init-repo": lambda: init_repo(Path(args.root)),
        "add-source": lambda: add_source(args),
        "capture-web": lambda: capture_web(args),
        "capture-browser": lambda: capture_browser(args),
        "ingest-pdf": lambda: ingest_pdf(args),
        "ingest-transcript": lambda: ingest_transcript(args),
        "summarize-source": lambda: summarize_source(args),
        "extract-claims": lambda: extract_claims(args),
        "build-index": lambda: build_index(args),
        "sync-source-artifacts": lambda: sync_source_artifacts(args),
        "vector-report": lambda: vector_report(args),
        "chapter-brief": lambda: chapter_brief(args),
        "dossier-outline": lambda: dossier_outline(args),
        "seed-papers": lambda: seed_papers(Path(args.root), overwrite_existing=bool(args.overwrite)),
        "export-papers": lambda: export_papers(Path(args.root)),
        "build-master-paper": lambda: build_master_paper(Path(args.root)),
        "seed-book": lambda: seed_book(Path(args.root), overwrite_existing=bool(args.overwrite)),
        "export-book": lambda: export_book(Path(args.root)),
        "build-book-print": lambda: build_book_print(Path(args.root)),
        "export-book-print": lambda: export_book_print(Path(args.root)),
        "review-book-print": lambda: review_book_print(Path(args.root)),
        "generate-book-assets": lambda: generate_book_assets(Path(args.root), kind=args.kind, chapter=args.chapter, asset_id=args.asset),
        "build-site": lambda: build_site(Path(args.root)),
        "build-website": lambda: build_website(Path(args.root)),
        "review-publication": lambda: review_publication(Path(args.root)),
    }
    command_map[args.command]()
    return 0


BROWSER_README = """# Browser Worker

This worker is intended for use from the Codex in-app browser when a page depends on JavaScript.

## Flow

1. Create a job:

```bash
python3 -m apps.research_cli.research_cli.cli capture-browser --root /Users/hassan/repos/AI-Empire --source-id example --vector-id 01_surveillance_capitalism --url https://example.com --capture-screenshot
```

2. Run the worker from the browser runtime:

```js
const { capturePageFromJob } = await import("file:///Users/hassan/repos/AI-Empire/apps/browser_worker/capture_page.mjs");
await capturePageFromJob("/Users/hassan/repos/AI-Empire/sources/browser_jobs/example.json");
```
"""


BROWSER_WORKER = """import fs from "node:fs/promises";\nimport path from "node:path";\n\nconst PLUGIN_ROOT = "file:///Users/hassan/.codex/plugins/cache/openai-bundled/browser/26.623.81905/scripts/browser-client.mjs";\n\nasync function ensureBrowser() {\n  if (globalThis.agent?.browsers == null) {\n    const { setupBrowserRuntime } = await import(PLUGIN_ROOT);\n    await setupBrowserRuntime({ globals: globalThis });\n  }\n  const browser = await globalThis.agent.browsers.get("iab");\n  return browser;\n}\n\nexport async function capturePage({ sourceId, url, outputDir, captureScreenshot = false }) {\n  const browser = await ensureBrowser();\n  const tab = await browser.tabs.new();\n  await tab.goto(url);\n  try {\n    await tab.playwright.waitForLoadState({ state: "networkidle", timeoutMs: 30000 });\n  } catch {}\n  const title = await tab.title();\n  const currentUrl = await tab.url();\n  const dom = await tab.playwright.domSnapshot();\n  await fs.mkdir(outputDir, { recursive: true });\n  const base = path.join(outputDir, sourceId);\n  await fs.writeFile(base + ".dom.txt", dom, "utf8");\n  let screenshotPath = null;\n  if (captureScreenshot) {\n    const screenshot = await tab.screenshot({ fullPage: true });\n    screenshotPath = base + ".png";\n    await fs.writeFile(screenshotPath, Buffer.from(screenshot));\n  }\n  const manifest = {\n    source_id: sourceId,\n    url: currentUrl,\n    requested_url: url,\n    title,\n    captured_at: new Date().toISOString(),\n    output_dir: outputDir,\n    screenshot_path: screenshotPath,\n    dom_path: base + ".dom.txt"\n  };\n  await fs.writeFile(base + ".capture.json", JSON.stringify(manifest, null, 2));\n  return manifest;\n}\n\nexport async function capturePageFromJob(jobPath) {\n  const job = JSON.parse(await fs.readFile(jobPath, "utf8"));\n  return capturePage({\n    sourceId: job.source_id,\n    url: job.url,\n    outputDir: job.output_dir,\n    captureScreenshot: Boolean(job.capture_screenshot)\n  });\n}\n"""


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
