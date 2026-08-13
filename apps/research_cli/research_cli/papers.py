from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
from html import escape
from pathlib import Path
from typing import Callable

from .constants import CHAPTERS, VECTORS
from .doctrine import (
    AI_EMPIRE_REPO_URL,
    WAKENAI_LABEL,
    WAKENAI_URL,
    copy_brand_logo,
    render_public_document_header,
    render_patimony_html_card,
    render_public_logo_header,
    render_vimeo_hero_block,
)
from .fs import ensure_dir, load_jsonl, overwrite

SERIES_RELATIONS = {
    "00": ["01", "04", "10"],
    "01": ["02", "04", "10"],
    "02": ["01", "03", "10"],
    "03": ["01", "02", "04"],
    "04": ["00", "05", "06", "10"],
    "05": ["04", "06", "09"],
    "06": ["04", "05", "07", "10"],
    "07": ["06", "08", "10"],
    "08": ["07", "09", "10"],
    "09": ["05", "07", "08", "10"],
    "10": ["00", "01", "02", "04", "07", "08", "09"],
}

REFORM_ALIGNMENT = {
    "00": "frames the civilizational ownership question and announces the three-reform destination",
    "01": "builds the structural case for refactoring Section 230 by documenting recommendation, extraction, and design power",
    "02": "deepens the Section 230 case by connecting amplification systems to youth harm, civic erosion, and moral reconfiguration",
    "03": "shows how crisis conditions accelerated digital dependence and normalized the infrastructure later challenged by the reform agenda",
    "04": "provides the central evidentiary basis for treating frontier weights as a patrimony and governance problem rather than a neutral market outcome",
    "05": "connects the enclosure story to labor correction, balance-sheet pressure, and the financial narratives that stabilized layoffs",
    "06": "shows how danger rhetoric, cheapness rhetoric, and reasoning rhetoric together normalize frontier enclosure and strategic dependence",
    "07": "establishes chokepoints, strategic access, and state-company interfaces that justify anti-capture obligations",
    "08": "shows how access is legitimized, stabilized, and normalized through governance, lobbying, elite networks, and institutional prestige",
    "09": "explains why inaction would compound dependency, hierarchy, and cognitive enclosure across the whole system",
    "10": "synthesizes the entire dossier into the direct three-reform program",
}

EVIDENCE_ORDER = {
    "Documented Fact": 0,
    "Disputed Fact": 1,
    "Hypothesis / Interpretation": 2,
    "Speculative Narrative Risk": 3,
}


def inject_paper_navigation(html: str) -> str:
    if "public-doc-header" in html or "public-brand-header" in html:
        return html
    header_block = render_public_document_header(
        "../assets/brand/waken-ai-black.webp",
        home_href="../../index.html",
        home_label="Return to paper index",
    )
    return html.replace("<body>", "<body>\n" + header_block, 1)


def slugify(value: str) -> str:
    ascii_value = (
        value.encode("ascii", "ignore").decode("ascii")
        if value.isascii()
        else re.sub(r"[^\w\s-]", "", value)
    )
    normalized = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower())
    return normalized.strip("-")


def discover_playwright_runtime(env: dict[str, str]) -> tuple[str, str] | None:
    node_cmd = shutil.which("node")
    if not node_cmd:
        return None

    candidates: list[Path] = []
    node_path_env = env.get("NODE_PATH")
    if node_path_env:
        for segment in node_path_env.split(os.pathsep):
            if segment:
                candidates.append(Path(segment))

    playwright_bin = shutil.which("playwright")
    if playwright_bin:
        bin_path = Path(playwright_bin).resolve()
        candidates.extend(
            [
                bin_path.parent.parent / "lib" / "node_modules",
                bin_path.parent.parent / "node_modules",
            ]
        )

    bundled_modules = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "node_modules"
    candidates.append(bundled_modules)

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "playwright" / "package.json").exists():
            return node_cmd, str(candidate)
    return None


def render_pdf_with_playwright(
    html_path: Path,
    pdf_path: Path,
    env: dict[str, str],
    format_name: str = "Letter",
) -> None:
    runtime = discover_playwright_runtime(env)
    if runtime is None:
        raise RuntimeError("Playwright runtime is not installed or could not be resolved")

    node_cmd, node_modules = runtime
    ensure_dir(pdf_path.parent)

    script = textwrap.dedent(
        """
        const { chromium } = require("playwright");

        async function main() {
          const htmlUrl = process.argv[2];
          const pdfPath = process.argv[3];
          const formatName = process.argv[4] || "Letter";
          const browser = await chromium.launch({ headless: true });
          const page = await browser.newPage();
          await page.goto(htmlUrl, { waitUntil: "networkidle" });
          await page.pdf({
            path: pdfPath,
            format: formatName,
            printBackground: true,
            margin: {
              top: "0.55in",
              right: "0.55in",
              bottom: "0.65in",
              left: "0.55in",
            },
          });
          await browser.close();
        }

        main().catch((error) => {
          console.error(error);
          process.exit(1);
        });
        """
    ).strip()

    child_env = env.copy()
    if child_env.get("NODE_PATH"):
        child_env["NODE_PATH"] = os.pathsep.join([node_modules, child_env["NODE_PATH"]])
    else:
        child_env["NODE_PATH"] = node_modules

    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False, encoding="utf-8") as handle:
        handle.write(script)
        script_path = Path(handle.name)

    try:
        subprocess.run(
            [
                node_cmd,
                str(script_path),
                html_path.resolve().as_uri(),
                str(pdf_path),
                format_name,
            ],
            check=True,
            env=child_env,
        )
    finally:
        script_path.unlink(missing_ok=True)


def chapter_by_id(chapter_id: str) -> dict:
    for chapter in CHAPTERS:
        if chapter["id"] == chapter_id:
            return chapter
    raise KeyError(f"Unknown chapter id: {chapter_id}")


def vector_by_id(vector_id: str) -> dict:
    for vector in VECTORS:
        if vector["id"] == vector_id:
            return vector
    raise KeyError(f"Unknown vector id: {vector_id}")


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


def strip_frontmatter(content: str) -> str:
    if not content.startswith("---\n"):
        return content
    _, remainder = content.split("---\n", 1)
    _, _, body = remainder.partition("\n---\n")
    return body.lstrip()


def extract_section(content: str, heading: str) -> str:
    pattern = rf"{re.escape(heading)}\n\n(.*?)(?:\n## |\Z)"
    match = re.search(pattern, content, re.S)
    return match.group(1).strip() if match else ""


def first_available_section(content: str, headings: list[str]) -> str:
    for heading in headings:
        section = extract_section(content, heading)
        if section:
            return section
    return ""


def extract_title(content: str, chapter_id: str) -> str:
    frontmatter = parse_frontmatter(content)
    title_value = str(frontmatter.get("title", "")).strip()
    if title_value and title_value.lower() != "title":
        return title_value
    headings = re.findall(r"^#\s+(.+)$", content, re.M)
    for heading in headings:
        candidate = heading.strip()
        if candidate.lower() != "title":
            return candidate
    return chapter_by_id(chapter_id)["title"]


def split_paragraphs(text: str) -> list[str]:
    return [chunk.strip() for chunk in re.split(r"\n\s*\n", text.strip()) if chunk.strip()]


def paragraph_block(paragraphs: list[str]) -> str:
    return "\n\n".join(paragraphs).strip()


def existing_paper_path(root: Path, chapter_id: str) -> Path | None:
    papers_root = root / "papers"
    if not papers_root.exists():
        return None
    matches = sorted(papers_root.glob(f"{chapter_id}_*_paper.md"))
    return matches[0] if matches else None


def chapter_corpus_path(root: Path, chapter_id: str) -> Path:
    chapter = chapter_by_id(chapter_id)
    return root / "chapters" / f"{chapter['id']}_{slugify(chapter['title'])}.md"


def paper_stem_for_chapter(root: Path, chapter_id: str) -> str:
    current = existing_paper_path(root, chapter_id)
    if current is not None:
        return current.stem
    chapter = chapter_by_id(chapter_id)
    return f"{chapter['id']}_{slugify(chapter['title'])}_paper"


def paper_path_for_chapter(root: Path, chapter_id: str) -> Path:
    return root / "papers" / f"{paper_stem_for_chapter(root, chapter_id)}.md"


def source_catalog(root: Path) -> dict[str, dict]:
    return {record["source_id"]: record for record in load_jsonl(root / "sources" / "catalog.jsonl")}


def first_bullet_text(section: str) -> str:
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            return stripped[2:].strip()
    compact = re.sub(r"\s+", " ", section.strip())
    return compact


def note_records(root: Path) -> list[dict]:
    records: list[dict] = []
    for note_path in sorted((root / "vectors").glob("*/notes/*.md")):
        content = note_path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        factual_summary = first_available_section(content, ["## Factual Summary"])
        proves = first_available_section(content, ["## What It Proves"])
        suggests = first_available_section(content, ["## What It Suggests"])
        records.append(
            {
                "note_id": slugify(str(note_path.relative_to(root))),
                "note_path": str(note_path.relative_to(root)),
                "source_id": frontmatter.get("source_id"),
                "vector_ids": frontmatter.get("vector_ids", []),
                "chapter_ids": frontmatter.get("chapter_ids", []),
                "source_tier": frontmatter.get("source_tier"),
                "source_type": frontmatter.get("source_type"),
                "url": frontmatter.get("url"),
                "published_at": frontmatter.get("published_at"),
                "captured_at": frontmatter.get("captured_at"),
                "risk_level": frontmatter.get("risk_level"),
                "factual_summary": first_bullet_text(factual_summary),
                "what_it_proves": first_bullet_text(proves),
                "what_it_suggests": first_bullet_text(suggests),
            }
        )
    return records


def chapter_slice(root: Path, chapter_id: str) -> dict:
    chapter = chapter_by_id(chapter_id)
    sources = [record for record in load_jsonl(root / "sources" / "catalog.jsonl") if chapter_id in record.get("chapter_ids", [])]
    claims = [record for record in load_jsonl(root / "claims" / "master_claims.jsonl") if chapter_id in record.get("chapter_ids", [])]
    events = [record for record in load_jsonl(root / "timelines" / "master_timeline.jsonl") if chapter_id in record.get("chapter_ids", [])]
    notes = [record for record in note_records(root) if chapter_id in record.get("chapter_ids", [])]
    entities = [
        record
        for record in load_jsonl(root / "profiles" / "entities.jsonl")
        if set(record.get("connected_vectors", [])) & set(chapter["vector_ids"])
    ]
    return {
        "chapter": chapter,
        "sources": sources,
        "claims": claims,
        "events": events,
        "notes": notes,
        "entities": entities,
    }


def corpus_stats(root: Path) -> dict:
    sources = load_jsonl(root / "sources" / "catalog.jsonl")
    claims = load_jsonl(root / "claims" / "master_claims.jsonl")
    entities = load_jsonl(root / "profiles" / "entities.jsonl")
    events = load_jsonl(root / "timelines" / "master_timeline.jsonl")
    notes = note_records(root)
    by_chapter = {chapter["id"]: chapter_slice(root, chapter["id"]) for chapter in CHAPTERS}
    return {
        "sources": sources,
        "claims": claims,
        "entities": entities,
        "events": events,
        "notes": notes,
        "by_chapter": by_chapter,
        "totals": {
            "sources": len(sources),
            "claims": len(claims),
            "entities": len(entities),
            "events": len(events),
            "notes": len(notes),
        },
    }


def parse_reference_ids(content: str) -> list[str]:
    references = first_available_section(content, ["## References / Bibliography", "## References"])
    reference_ids: list[str] = []
    for line in references.splitlines():
        match = re.match(r"(?:\[\d+\]|\d+\.)\s+(?:`([^`]+)`|.*Audit ID:\s*`?([A-Za-z0-9._-]+)`?)", line.strip())
        if match:
            reference_ids.append(match.group(1) or match.group(2))
    return reference_ids


def parse_inline_source_ids(content: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for match in re.finditer(r"\[Sources:\s*([^\]]+)\]", content):
        payload = match.group(1)
        ids = re.findall(r"`([^`]+)`", payload)
        for source_id in ids:
            if source_id not in seen:
                seen.add(source_id)
                ordered.append(source_id)
    return ordered


def parse_backbone_source_ids(content: str) -> list[str]:
    section = first_available_section(content, ["## Backbone Sources"])
    ids: list[str] = []
    seen: set[str] = set()
    for line in section.splitlines():
        stripped = line.strip()
        match = re.match(r"-\s+`([^`]+)`", stripped)
        if not match:
            continue
        source_id = match.group(1)
        if source_id not in seen:
            seen.add(source_id)
            ids.append(source_id)
    return ids


def truncate_sentence(value: str, limit: int = 180) -> str:
    compact = re.sub(r"\s+", " ", value.strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def humanize_claim_title(claim_text: str, limit: int = 84) -> str:
    cleaned = claim_text.strip()
    cleaned = re.sub(r"^That\s+", "", cleaned)
    cleaned = cleaned.replace("`", "")
    cleaned = cleaned.rstrip(".")
    return sentence_case_title(truncate_sentence(cleaned, limit=limit))


def sentence_case_title(value: str) -> str:
    compact = re.sub(r"\s+", " ", value.strip())
    if not compact:
        return compact
    return compact[0].upper() + compact[1:]


def keywords_for_chapter(chapter: dict, reference_ids: list[str]) -> str:
    seed_terms = [
        chapter["title"],
        "surveillance capitalism",
        "AI imperialism",
    ]
    if chapter["id"] in {"01", "02", "10"}:
        seed_terms.append("Section 230 reform")
    if chapter["id"] in {"00", "04", "10"}:
        seed_terms.append("AI weights")
        seed_terms.append("patrimony of humanity")
    if chapter["id"] in {"07", "08", "10"}:
        seed_terms.append("government capture")
    if reference_ids:
        seed_terms.append("evidence-based dossier")
    seen: set[str] = set()
    ordered: list[str] = []
    for term in seed_terms:
        normalized = term.strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            ordered.append(normalized)
    return "; ".join(ordered[:8])


def build_abstract(central_thesis: str, main_analysis: str, reform_relevance: str) -> str:
    thesis_sentence = first_sentence(summary_ready_text(central_thesis))
    analysis_paragraphs = split_paragraphs(main_analysis)
    analysis_sentence = first_sentence(summary_ready_text(analysis_paragraphs[0] if analysis_paragraphs else main_analysis))
    reform_sentence = first_sentence(summary_ready_text(reform_relevance))
    parts = [part for part in [thesis_sentence, analysis_sentence, reform_sentence] if part]
    return " ".join(parts) if parts else "Abstract pending."


def build_research_question(chapter: dict, central_thesis: str) -> str:
    if chapter["id"] == "00":
        return "How should the dossier's opening framework connect surveillance capitalism, ownership of AI weights, and the three-reform program?"
    if chapter["id"] == "10":
        return "What reform doctrine follows from the dossier's evidence on platform power, frontier-model enclosure, and state-company entanglement?"
    stem = chapter["title"].lower()
    return f"How does {stem} function within the dossier's larger argument, and what does the documentary record allow this chapter to establish?"


def build_evidence_method(chapter_id: str) -> str:
    return (
        f"This paper is derived from the chapter corpus for Chapter {chapter_id} and is grounded in the project's structured research OS. "
        "It relies on source notes, extracted claims, entity profiles, and timeline events already normalized under the dossier's evidence hierarchy. "
        "Documented facts are asserted directly where the record supports them; disputed matters are marked as such; interpretive claims are bounded explicitly; and speculative overreach is isolated in the evidence-boundary appendix."
    )


def build_conclusion(transition: str, reform_relevance: str, chapter_id: str) -> str:
    pieces = [first_sentence(summary_ready_text(reform_relevance))]
    if transition.strip():
        pieces.append(first_sentence(summary_ready_text(transition)))
    pieces.append(
        f"In the architecture of this series, Chapter {chapter_id} therefore functions as a self-contained argument while also advancing the cumulative path toward the dossier's three reforms."
    )
    return " ".join(piece for piece in pieces if piece)


def summary_ready_text(value: str) -> str:
    text = value.strip()
    text = re.sub(r"\[Sources:\s*[^\]]+\]", "", text)
    text = text.replace("`", "")
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        lines.append(stripped)
    compact = re.sub(r"\s+", " ", " ".join(lines)).strip()
    return compact


def first_sentence(value: str) -> str:
    compact = value.strip()
    if not compact:
        return ""
    match = re.search(r"(.+?[.!?])(?:\s|$)", compact)
    if match:
        return match.group(1).strip()
    return truncate_sentence(compact, 220)


def format_blocks(blocks: list[str]) -> str:
    cleaned = [block.strip() for block in blocks if block.strip()]
    return "\n\n".join(cleaned) if cleaned else "_None registered for this paper._"


def markdown_link(label: str, url: str | None) -> str:
    if not url:
        return label
    return f"[{label}]({url})"


def internal_link(label: str, anchor: str) -> str:
    return f"[{label}](#{anchor})"


def chapter_scope_note(chapter_id: str) -> str:
    chapter = chapter_by_id(chapter_id)
    relation_ids = SERIES_RELATIONS.get(chapter_id, [])
    related = ", ".join(f"Chapter {cid}" for cid in relation_ids)
    return (
        f"This paper examines {chapter['title'].lower()} within the broader dossier *From Surveillance Capitalism to AI Imperialism*. "
        "It is intentionally written to circulate on its own: necessary context is restated, evidence boundaries are made explicit, "
        "and cited material is reproduced in paper-local form rather than delegated to repo navigation. "
        f"It contributes to the series as a paper that {REFORM_ALIGNMENT.get(chapter_id, 'advances the reform-oriented thesis of the dossier')}. "
        f"Adjacent reinforcement appears in {related}, but those cross-references are supportive rather than required for basic comprehension."
    )


def chapter_position_within_series(chapter_id: str) -> str:
    related_ids = SERIES_RELATIONS.get(chapter_id, [])
    related_titles = [f"Chapter {cid} ({chapter_by_id(cid)['title']})" for cid in related_ids]
    return (
        f"This paper sits inside a coordinated 11-paper architecture. Its nearest companions are {', '.join(related_titles)}. "
        f"In that series logic, Chapter {chapter_id} {REFORM_ALIGNMENT.get(chapter_id, 'advances the cumulative reform case')}."
    )


def generated_introduction(research_question: str, central_thesis: str) -> str:
    return (
        f"This paper asks: {research_question} "
        f"Its working answer is clear from the start: {central_thesis} "
        "The objective is not only to recount developments, but to show why the subject of this chapter belongs inside a structural argument about extraction, enclosure, legitimacy, and reform."
    )


def generated_context(chapter_id: str) -> str:
    chapter = chapter_by_id(chapter_id)
    return (
        f"The institutional context for {chapter['title'].lower()} cannot be treated as an isolated debate. "
        "Each chapter in this series is part of a longer sequence in which platform design, data capture, labor correction, model governance, and state access accumulate into a single political structure. "
        "This section therefore identifies the historical or institutional setting needed for a standalone reader before moving deeper into the paper's own evidentiary claims."
    )


def referenced_claims(chapter_claims: list[dict], reference_ids: set[str]) -> list[dict]:
    claims = [claim for claim in chapter_claims if set(claim.get("source_ids", [])) & reference_ids]
    return sorted(claims, key=lambda item: (EVIDENCE_ORDER.get(item.get("evidence_level"), 99), item.get("claim_id", "")))


def referenced_events(chapter_events: list[dict], reference_ids: set[str]) -> list[dict]:
    events = [event for event in chapter_events if set(event.get("source_ids", [])) & reference_ids]
    return sorted(events, key=lambda item: (item.get("date", ""), item.get("event_id", "")))


def referenced_notes(chapter_notes: list[dict], reference_ids: set[str]) -> list[dict]:
    return [note for note in chapter_notes if note.get("source_id") in reference_ids]


def referenced_entities(chapter_entities: list[dict], reference_ids: set[str], paper_body: str) -> list[dict]:
    body_lower = paper_body.lower()
    filtered = []
    for entity in chapter_entities:
        source_ids = set(entity.get("source_ids", []))
        name = str(entity.get("name", ""))
        if source_ids & reference_ids or (name and name.lower() in body_lower):
            filtered.append(entity)
    return sorted(filtered, key=lambda item: (item.get("entity_type", ""), item.get("name", "")))


def entity_role_text(entity: dict) -> str:
    vectors = entity.get("connected_vectors", [])
    if not vectors:
        return "Background actor referenced in this paper's argument."
    preview = ", ".join(vectors[:4])
    suffix = " and others" if len(vectors) > 4 else ""
    return f"Actor relevant to {preview}{suffix}."


def build_companion_label_maps(stats: dict) -> dict:
    source_map: dict[str, dict] = {}
    for index, record in enumerate(sorted(stats["sources"], key=lambda item: item.get("source_id", "")), start=1):
        code = f"S-{index:03d}"
        title = record.get("title") or record.get("source_id", "")
        source_map[record["source_id"]] = {
            "code": code,
            "label": f"Source {code}",
            "anchor": f"source-{code.lower()}-{slugify(title) or record['source_id']}",
        }

    claim_map: dict[str, dict] = {}
    for index, record in enumerate(sorted(stats["claims"], key=lambda item: item.get("claim_id", "")), start=1):
        code = f"C-{index:03d}"
        claim_map[record["claim_id"]] = {
            "code": code,
            "label": f"Claim {code}",
            "anchor": f"claim-{code.lower()}-{slugify(humanize_claim_title(record.get('claim_text', '')))}",
        }

    entity_map: dict[str, dict] = {}
    for index, record in enumerate(sorted(stats["entities"], key=lambda item: item.get("entity_id", "")), start=1):
        code = f"E-{index:03d}"
        entity_map[record["entity_id"]] = {
            "code": code,
            "label": f"Entity {code}",
            "anchor": f"entity-{code.lower()}-{slugify(record.get('name', '') or record['entity_id'])}",
        }

    event_map: dict[str, dict] = {}
    for index, record in enumerate(
        sorted(stats["events"], key=lambda item: (item.get("date", ""), item.get("event_id", ""))),
        start=1,
    ):
        code = f"T-{index:03d}"
        event_map[record["event_id"]] = {
            "code": code,
            "label": f"Event {code}",
            "anchor": f"event-{code.lower()}-{slugify(record.get('label', '') or record['event_id'])}",
        }

    note_map: dict[str, dict] = {}
    for index, record in enumerate(sorted(stats["notes"], key=lambda item: item.get("note_id", "")), start=1):
        code = f"N-{index:03d}"
        note_id = record.get("note_id", f"note-{index}")
        note_map[note_id] = {
            "code": code,
            "label": f"Note {code}",
            "anchor": f"note-{code.lower()}-{slugify(note_id)}",
        }

    return {
        "sources": source_map,
        "claims": claim_map,
        "entities": entity_map,
        "events": event_map,
        "notes": note_map,
    }


def build_paper_registry(
    reference_ids: list[str],
    chapter_claims: list[dict],
    chapter_events: list[dict],
    chapter_entities: list[dict],
    chapter_notes: list[dict],
    catalog: dict[str, dict],
    companion_maps: dict,
) -> dict:
    source_entries: list[dict] = []
    source_map: dict[str, dict] = {}
    for index, source_id in enumerate(reference_ids, start=1):
        record = catalog.get(source_id, {})
        title = record.get("title") or source_id
        anchor = f"appendix-a{index}-{slugify(title) or source_id}"
        entry = {
            "source_id": source_id,
            "label": f"A{index}",
            "public_label": f"Appendix A{index}",
            "title": title,
            "anchor": anchor,
            "record": record,
            "companion": companion_maps["sources"].get(source_id, {}),
        }
        source_entries.append(entry)
        source_map[source_id] = entry

    claim_entries: list[dict] = []
    claim_map: dict[str, dict] = {}
    for index, claim in enumerate(chapter_claims, start=1):
        title = humanize_claim_title(claim.get("claim_text", "Claim"))
        anchor = f"appendix-b{index}-{slugify(title) or claim.get('claim_id', f'claim-{index}')}"
        entry = {
            "claim_id": claim["claim_id"],
            "label": f"B{index}",
            "public_label": f"Appendix B{index}",
            "title": title,
            "anchor": anchor,
            "record": claim,
            "companion": companion_maps["claims"].get(claim["claim_id"], {}),
            "source_entries": [source_map[source_id] for source_id in claim.get("source_ids", []) if source_id in source_map],
        }
        claim_entries.append(entry)
        claim_map[claim["claim_id"]] = entry

    event_entries: list[dict] = []
    event_map: dict[str, dict] = {}
    for index, event in enumerate(chapter_events, start=1):
        title = f"{event.get('date', 'Unknown')}: {event.get('label', 'Event')}"
        anchor = f"appendix-c{index}-{slugify(title) or event.get('event_id', f'event-{index}')}"
        entry = {
            "event_id": event["event_id"],
            "label": f"C{index}",
            "public_label": f"Appendix C{index}",
            "title": truncate_sentence(title, 100),
            "anchor": anchor,
            "record": event,
            "companion": companion_maps["events"].get(event["event_id"], {}),
            "source_entries": [source_map[source_id] for source_id in event.get("source_ids", []) if source_id in source_map],
        }
        event_entries.append(entry)
        event_map[event["event_id"]] = entry

    entity_entries: list[dict] = []
    entity_map: dict[str, dict] = {}
    for index, entity in enumerate(chapter_entities, start=1):
        title = entity.get("name", entity.get("entity_id", f"entity-{index}"))
        anchor = f"appendix-d{index}-{slugify(title) or entity.get('entity_id', f'entity-{index}')}"
        relevant_sources = [source_map[source_id] for source_id in entity.get("source_ids", []) if source_id in source_map]
        entry = {
            "entity_id": entity["entity_id"],
            "label": f"D{index}",
            "public_label": f"Appendix D{index}",
            "title": title,
            "anchor": anchor,
            "record": entity,
            "companion": companion_maps["entities"].get(entity["entity_id"], {}),
            "source_entries": relevant_sources,
        }
        entity_entries.append(entry)
        entity_map[entity["entity_id"]] = entry

    note_entries = []
    for note in chapter_notes:
        note_id = note.get("note_id")
        if note_id not in companion_maps["notes"]:
            continue
        note_entries.append(
            {
                "note_id": note_id,
                "source_id": note.get("source_id"),
                "record": note,
                "companion": companion_maps["notes"][note_id],
                "source_entry": source_map.get(note["source_id"]),
            }
        )

    return {
        "sources": source_entries,
        "source_map": source_map,
        "claims": claim_entries,
        "claim_map": claim_map,
        "events": event_entries,
        "event_map": event_map,
        "entities": entity_entries,
        "entity_map": entity_map,
        "notes": note_entries,
    }


def source_relevance_text(source_id: str, chapter_claims: list[dict]) -> str:
    for claim in chapter_claims:
        if source_id in claim.get("source_ids", []):
            return truncate_sentence(claim.get("claim_text", "Supports a key claim in this paper."))
    return "Supports a key factual or interpretive move inside this paper."


def render_reference_entry(index: int, source_entry: dict, chapter_claims: list[dict]) -> str:
    record = source_entry["record"]
    author = record.get("author") or record.get("publisher") or "Unknown source"
    title = record.get("title") or source_entry["source_id"]
    published = record.get("published_at") or "n.d."
    linked_title = markdown_link(title, record.get("url"))
    tier = record.get("source_tier") or "Unknown"
    source_type = record.get("source_type") or "unknown"
    appendix_link = internal_link(source_entry["public_label"], source_entry["anchor"])
    companion_label = source_entry["companion"].get("label", "Companion source unavailable")
    why = source_relevance_text(source_entry["source_id"], chapter_claims)
    return (
        f"{index}. {author}. {linked_title}. {published}. {tier} {source_type}. "
        f"Paper appendix: {appendix_link}. Corpus companion entry: {companion_label}. "
        f"Audit ID: `{source_entry['source_id']}`. Relevance: {why}"
    )


def footnote_source_citation(source_entry: dict) -> str:
    record = source_entry["record"]
    author = record.get("author") or record.get("publisher") or source_entry["source_id"]
    title = record.get("title") or source_entry["source_id"]
    published = record.get("published_at") or "n.d."
    linked_title = markdown_link(truncate_sentence(title, 40), record.get("url"))
    appendix_link = internal_link(source_entry["public_label"], source_entry["anchor"])
    return f"{author}, {linked_title} ({published}; see {appendix_link})"


def render_source_register(source_entries: list[dict], chapter_claims: list[dict]) -> str:
    blocks = []
    for entry in source_entries:
        record = entry["record"]
        title = record.get("title") or entry["source_id"]
        linked_title = markdown_link(title, record.get("url"))
        author = record.get("author") or record.get("publisher") or "Unknown source"
        published = record.get("published_at") or "n.d."
        tier = record.get("source_tier") or "Unknown"
        source_type = record.get("source_type") or "unknown"
        companion_label = entry["companion"].get("label", "Companion source unavailable")
        why = source_relevance_text(entry["source_id"], chapter_claims)
        blocks.append(
            "\n".join(
                [
                    f"### {entry['public_label']}. {title} {{#{entry['anchor']}}}",
                    f"**Source citation:** {linked_title}",
                    f"**Institution / author:** {author}",
                    f"**Date:** {published}",
                    f"**Tier / type:** {tier} / {source_type}",
                    f"**Why it matters in this paper:** {why}",
                    f"**Corpus companion entry:** {companion_label}",
                    f"**Audit ID:** `{entry['source_id']}`",
                ]
            )
        )
    return format_blocks(blocks)


def render_claim_register(claim_entries: list[dict]) -> str:
    blocks = []
    for entry in claim_entries:
        claim = entry["record"]
        support_links = ", ".join(
            internal_link(source_entry["public_label"], source_entry["anchor"]) for source_entry in entry["source_entries"]
        ) or "No paper-local source register entry is attached."
        blocks.append(
            "\n".join(
                [
                    f"### {entry['public_label']}. {entry['title']} {{#{entry['anchor']}}}",
                    f"**Claim statement:** {claim.get('claim_text', '')}",
                    f"**Evidence status:** {claim.get('evidence_level', 'Unknown')}",
                    f"**Source support:** {support_links}",
                    f"**Corpus companion entry:** {entry['companion'].get('label', 'Companion claim unavailable')}",
                    f"**Audit Claim ID:** `{entry['claim_id']}`",
                ]
            )
        )
    return format_blocks(blocks)


def render_timeline_slice(event_entries: list[dict]) -> str:
    blocks = []
    for entry in event_entries:
        event = entry["record"]
        support_links = ", ".join(
            internal_link(source_entry["public_label"], source_entry["anchor"]) for source_entry in entry["source_entries"]
        ) or "No paper-local source register entry is attached."
        blocks.append(
            "\n".join(
                [
                    f"### {entry['public_label']}. {entry['title']} {{#{entry['anchor']}}}",
                    f"**Event summary:** {event.get('label', '')}",
                    f"**Event date:** {event.get('date', 'Unknown')}",
                    f"**Source support:** {support_links}",
                    f"**Corpus companion entry:** {entry['companion'].get('label', 'Companion event unavailable')}",
                    f"**Audit Event ID:** `{entry['event_id']}`",
                ]
            )
        )
    return format_blocks(blocks)


def render_entity_slice(entity_entries: list[dict]) -> str:
    blocks = []
    for entry in entity_entries:
        entity = entry["record"]
        source_links = ", ".join(
            internal_link(source_entry["public_label"], source_entry["anchor"]) for source_entry in entry["source_entries"]
        ) or "This entity is contextual in this paper rather than source-leading."
        blocks.append(
            "\n".join(
                [
                    f"### {entry['public_label']}. {entry['title']} {{#{entry['anchor']}}}",
                    f"**Entity type:** {entity.get('entity_type', 'Unknown')}",
                    f"**Role in this paper:** {entity_role_text(entity)}",
                    f"**Relevant sources in this paper:** {source_links}",
                    f"**Corpus companion entry:** {entry['companion'].get('label', 'Companion entity unavailable')}",
                    f"**Audit Entity ID:** `{entry['entity_id']}`",
                ]
            )
        )
    return format_blocks(blocks)


def render_evidence_boundaries(claim_entries: list[dict], note_entries: list[dict]) -> str:
    disputed = [entry for entry in claim_entries if entry["record"].get("evidence_level") == "Disputed Fact"]
    hypotheses = [entry for entry in claim_entries if entry["record"].get("evidence_level") == "Hypothesis / Interpretation"]
    speculative = [entry for entry in claim_entries if entry["record"].get("evidence_level") == "Speculative Narrative Risk"]

    def claim_links(entries: list[dict]) -> str:
        if not entries:
            return "- None registered for this paper."
        return "\n".join(
            f"- {internal_link(entry['public_label'], entry['anchor'])}: {entry['record'].get('claim_text', '')}"
            for entry in entries
        )

    note_lines = []
    for note_entry in note_entries:
        source_entry = note_entry.get("source_entry")
        public_source = internal_link(source_entry["public_label"], source_entry["anchor"]) if source_entry else note_entry["source_id"]
        note_lines.append(
            f"- {public_source}. Companion note: {note_entry['companion'].get('label', 'Unavailable')}. "
            f"Risk flag: {note_entry['record'].get('risk_level', 'unspecified')}. "
            f"Note focus: {note_entry['record'].get('what_it_proves') or note_entry['record'].get('factual_summary') or 'No summary registered.'}"
        )

    blocks = [
        "### Appendix E1. Disputed Matters {#appendix-e1-disputed-matters}",
        "",
        claim_links(disputed),
        "",
        "### Appendix E2. Interpretive Boundaries {#appendix-e2-interpretive-boundaries}",
        "",
        claim_links(hypotheses),
        "",
        "### Appendix E3. Speculative Narrative Risks {#appendix-e3-speculative-narrative-risks}",
        "",
        claim_links(speculative),
        "",
        "### Appendix E4. Sensitive or Review-Worthy Note Flags {#appendix-e4-sensitive-or-review-worthy-note-flags}",
        "",
        "\n".join(note_lines) if note_lines else "- No elevated note flags are registered for this paper.",
    ]
    return "\n".join(blocks)


def notes_section_text(chapter_id: str) -> str:
    return (
        "This paper is designed to circulate independently. Public notes point readers to the real external documents first, then to the paper-local appendix entry that explains why each source matters.\n\n"
        "The underlying research OS distinguishes among `Documented Fact`, `Disputed Fact`, `Hypothesis / Interpretation`, and `Speculative Narrative Risk`. "
        f"In Chapter {chapter_id}, those boundaries remain visible in the prose, in the bibliography, and in the appendix sections that summarize claims and caution points."
    )


def bibliography_block(source_entries: list[dict], chapter_claims: list[dict]) -> str:
    lines = [render_reference_entry(index, entry, chapter_claims) for index, entry in enumerate(source_entries, start=1)]
    return "\n".join(lines) if lines else "- No references are registered yet."


def paper_yaml_frontmatter(title: str, chapter_id: str) -> str:
    chapter = chapter_by_id(chapter_id)
    subtitle = f"From Surveillance Capitalism to AI Imperialism | Chapter {chapter_id}: {chapter['title']}"
    return "\n".join(
        [
            "---",
            f'title: "{title}"',
            f'subtitle: "{subtitle}"',
            'author: ""',
            'date: ""',
            "lang: en-US",
            "---",
            "",
        ]
    )


def replace_numeric_citations(content: str, reference_ids: list[str], source_map: dict[str, dict]) -> str:
    number_map = {str(index): source_id for index, source_id in enumerate(reference_ids, start=1)}
    split_pattern = re.compile(r"\n## References / Bibliography\n|\n## References\n")
    parts = split_pattern.split(content, maxsplit=1)
    if len(parts) != 2:
        return content
    body, tail = parts[0], parts[1]

    def replace_cluster(match: re.Match[str]) -> str:
        numbers = re.findall(r"\[(\d+)\]", match.group(0))
        citations = []
        for number in numbers:
            source_id = number_map.get(number)
            if source_id is None or source_id not in source_map:
                continue
            citations.append(footnote_source_citation(source_map[source_id]))
        if not citations:
            return match.group(0)
        return f"^[Sources: {'; '.join(citations)}]"

    converted_body = re.sub(r"(?:\[\d+\]){1,12}", replace_cluster, body)
    return converted_body + "\n## References / Bibliography\n" + tail


def replace_inline_source_markers(content: str, source_map: dict[str, dict]) -> str:
    split_pattern = re.compile(r"\n## References / Bibliography\n|\n## References\n")
    parts = split_pattern.split(content, maxsplit=1)
    if len(parts) != 2:
        return content
    body, tail = parts[0], parts[1]

    def replace_sources(match: re.Match[str]) -> str:
        payload = match.group(1)
        ids = re.findall(r"`([^`]+)`", payload)
        citations: list[str] = []
        for source_id in ids:
            if source_id in source_map:
                citations.append(footnote_source_citation(source_map[source_id]))
            else:
                citations.append(source_id)
        if not citations:
            return match.group(0)
        return f"^[Sources: {'; '.join(citations)}]"

    converted_body = re.sub(r"\[Sources:\s*([^\]]+)\]", replace_sources, body)
    return converted_body + "\n## References / Bibliography\n" + tail


def normalize_paper_markdown(content: str, chapter_id: str, root: Path, stats: dict, companion_maps: dict) -> str:
    catalog = source_catalog(root)
    chapter = chapter_by_id(chapter_id)
    chapter_data = stats["by_chapter"][chapter_id]

    title = extract_title(content, chapter_id)
    central_thesis = first_available_section(content, ["## Central Thesis", "## Core Thesis"]) or chapter["core_thesis"]
    main_analysis = first_available_section(content, ["## Main Analysis", "## Main Evidence"]) or "Main analysis pending."
    counterarguments = first_available_section(content, ["## Counterarguments", "## Counterargument", "## Counterargument or Limit"]) or "Counterarguments pending."
    limits = first_available_section(content, ["## Limits of the Evidence", "## Counterargument or Limit"]) or "Limits section pending."
    reform_relevance = first_available_section(content, ["## Reform Relevance", "## Political and Social Implication"]) or "Reform relevance pending."
    transition = first_available_section(content, ["## Transition"])
    abstract = first_available_section(content, ["## Abstract"]) or build_abstract(central_thesis, main_analysis, reform_relevance)
    reference_ids = parse_reference_ids(content)
    if not reference_ids:
        reference_ids = parse_inline_source_ids(content)
    if not reference_ids:
        reference_ids = parse_backbone_source_ids(content)
    if not reference_ids:
        reference_ids = [record["source_id"] for record in chapter_data["sources"]]
    keywords = first_available_section(content, ["## Keywords"]) or keywords_for_chapter(chapter, reference_ids)
    research_question = first_available_section(content, ["## Research Question"]) or build_research_question(chapter, central_thesis)
    evidence_method = first_available_section(content, ["## Evidence and Method Note"]) or build_evidence_method(chapter_id)
    conclusion = first_available_section(content, ["## Conclusion"]) or build_conclusion(transition, reform_relevance, chapter_id)
    reference_id_set = set(reference_ids)

    analysis_paragraphs = split_paragraphs(main_analysis)
    if "### " in main_analysis:
        context_block = generated_context(chapter_id)
        main_analysis_block = main_analysis
    elif len(analysis_paragraphs) >= 2:
        context_block = analysis_paragraphs[0]
        main_analysis_block = paragraph_block(analysis_paragraphs[1:])
    else:
        context_block = generated_context(chapter_id)
        main_analysis_block = main_analysis

    chapter_claims = referenced_claims(chapter_data["claims"], reference_id_set)
    chapter_events = referenced_events(chapter_data["events"], reference_id_set)
    chapter_notes = referenced_notes(chapter_data["notes"], reference_id_set)

    preliminary_body = "\n\n".join(
        [
            abstract,
            central_thesis,
            evidence_method,
            generated_introduction(research_question, central_thesis),
            context_block,
            main_analysis_block,
            chapter_position_within_series(chapter_id),
            counterarguments,
            limits,
            reform_relevance,
            conclusion,
        ]
    )
    chapter_entities = referenced_entities(chapter_data["entities"], reference_id_set, preliminary_body)
    registry = build_paper_registry(
        reference_ids,
        chapter_claims,
        chapter_events,
        chapter_entities,
        chapter_notes,
        catalog,
        companion_maps,
    )

    blocks = [
        paper_yaml_frontmatter(title, chapter_id),
        "## Abstract",
        "",
        abstract,
        "",
        "## Keywords",
        "",
        keywords,
        "",
        "## Research Question",
        "",
        research_question,
        "",
        "## Scope and Framing Note",
        "",
        chapter_scope_note(chapter_id),
        "",
        "## Central Thesis",
        "",
        central_thesis,
        "",
        "## Evidence and Method Note",
        "",
        evidence_method,
        "",
        "## Introduction",
        "",
        generated_introduction(research_question, central_thesis),
        "",
        "## Historical or Institutional Context",
        "",
        context_block,
        "",
        "## Main Analysis",
        "",
        main_analysis_block,
        "",
        "## Position Within the Series",
        "",
        chapter_position_within_series(chapter_id),
        "",
        "## Counterarguments",
        "",
        counterarguments,
        "",
        "## Limits of the Evidence",
        "",
        limits,
        "",
        "## Reform Relevance",
        "",
        reform_relevance,
        "",
        "## Conclusion",
        "",
        conclusion,
        "",
        "## Notes",
        "",
        notes_section_text(chapter_id),
        "",
        "## References / Bibliography",
        "",
        bibliography_block(registry["sources"], chapter_claims),
        "",
        "## Appendix A. Source Register for This Paper",
        "",
        render_source_register(registry["sources"], chapter_claims),
        "",
        "## Appendix B. Claims Used in This Paper",
        "",
        render_claim_register(registry["claims"]),
        "",
        "## Appendix C. Timeline Slice",
        "",
        render_timeline_slice(registry["events"]),
        "",
        "## Appendix D. Relevant Entities",
        "",
        render_entity_slice(registry["entities"]),
        "",
        "## Appendix E. Evidence Boundaries",
        "",
        render_evidence_boundaries(registry["claims"], registry["notes"]),
        "",
    ]
    joined = "\n".join(blocks).rstrip() + "\n"
    with_inline = replace_inline_source_markers(joined, registry["source_map"])
    return replace_numeric_citations(with_inline, reference_ids, registry["source_map"])


def render_internal_registry(root: Path, stats: dict) -> str:
    return "\n".join(
        [
            "# Internal Corpus Registry",
            "",
            "This registry remains internal generation support. Public-facing readers should use the standalone papers, the omnibus dossier, and the corpus companion volume.",
            "",
            "## Corpus Totals",
            "",
            f"- Sources: {stats['totals']['sources']}",
            f"- Claims: {stats['totals']['claims']}",
            f"- Entities: {stats['totals']['entities']}",
            f"- Events: {stats['totals']['events']}",
            f"- Notes: {stats['totals']['notes']}",
            "",
            f"- Reader-facing omnibus: [volumes/dossier_omnibus.md]({(root / 'volumes' / 'dossier_omnibus.md').as_posix()})",
            f"- Reader-facing companion: [volumes/corpus_companion.md]({(root / 'volumes' / 'corpus_companion.md').as_posix()})",
            "",
        ]
    )


def write_internal_appendix(root: Path, stats: dict) -> None:
    appendix_root = root / "papers" / "appendix"
    ensure_dir(appendix_root / "chapters")
    overwrite(appendix_root / "README.md", render_internal_registry(root, stats) + "\n")

    source_lines = [
        f"- `{record['source_id']}`. *{record.get('title', '')}*. Tier: {record.get('source_tier', '')}. "
        f"Chapters: {', '.join(record.get('chapter_ids', []))}. Vectors: {', '.join(record.get('vector_ids', []))}."
        for record in stats["sources"]
    ]
    overwrite(appendix_root / "sources.md", "# Internal Source Index\n\n" + "\n".join(source_lines) + "\n")

    claim_lines = [
        f"- `{record['claim_id']}` [{record.get('evidence_level', '')}]. Chapters: {', '.join(record.get('chapter_ids', []))}. "
        f"Sources: {', '.join(record.get('source_ids', []))}. {record.get('claim_text', '')}"
        for record in stats["claims"]
    ]
    overwrite(appendix_root / "claims.md", "# Internal Claim Index\n\n" + "\n".join(claim_lines) + "\n")

    entity_lines = [
        f"- `{record['entity_id']}`. {record.get('name', '')} ({record.get('entity_type', '')}). "
        f"Vectors: {', '.join(record.get('connected_vectors', []))}. Sources: {', '.join(record.get('source_ids', []))}."
        for record in stats["entities"]
    ]
    overwrite(appendix_root / "entities.md", "# Internal Entity Index\n\n" + "\n".join(entity_lines) + "\n")

    event_lines = [
        f"- `{record['event_id']}`. Date: {record.get('date', '')}. Event: {record.get('label', '')}. "
        f"Chapters: {', '.join(record.get('chapter_ids', []))}. Sources: {', '.join(record.get('source_ids', []))}."
        for record in stats["events"]
    ]
    overwrite(appendix_root / "events.md", "# Internal Event Index\n\n" + "\n".join(event_lines) + "\n")

    note_lines = [
        f"- `{record.get('source_id', '')}`. Chapters: {', '.join(record.get('chapter_ids', []))}. "
        f"Risk: {record.get('risk_level', '')}. Primary prove-text: {record.get('what_it_proves') or record.get('factual_summary') or 'No summary registered.'}"
        for record in stats["notes"]
    ]
    overwrite(appendix_root / "notes.md", "# Internal Note Index\n\n" + "\n".join(note_lines) + "\n")

    crosswalk_lines = []
    for chapter_id, slice_ in stats["by_chapter"].items():
        chapter = slice_["chapter"]
        crosswalk_lines.append(
            f"- Chapter {chapter_id} ({chapter['title']}): {len(slice_['sources'])} sources, {len(slice_['claims'])} claims, "
            f"{len(slice_['entities'])} entities, {len(slice_['events'])} events, {len(slice_['notes'])} notes."
        )
    overwrite(appendix_root / "crosswalk.md", "# Internal Chapter Crosswalk\n\n" + "\n".join(crosswalk_lines) + "\n")

    for chapter_id, slice_ in stats["by_chapter"].items():
        chapter = slice_["chapter"]
        stem = paper_stem_for_chapter(root, chapter_id)
        chapter_lines = [
            f"# Chapter {chapter_id} Internal Appendix",
            "",
            f"- Title: {chapter['title']}",
            f"- Core thesis: {chapter['core_thesis']}",
            f"- Sources: {len(slice_['sources'])}",
            f"- Claims: {len(slice_['claims'])}",
            f"- Entities: {len(slice_['entities'])}",
            f"- Events: {len(slice_['events'])}",
            f"- Notes: {len(slice_['notes'])}",
            "",
        ]
        overwrite(appendix_root / "chapters" / f"{stem}.md", "\n".join(chapter_lines))


def render_dossier_omnibus(root: Path) -> str:
    chapter_sections = []
    for chapter in CHAPTERS:
        paper_path = paper_path_for_chapter(root, chapter["id"])
        paper_body = strip_frontmatter(paper_path.read_text(encoding="utf-8")).strip()
        prefixed = prefix_internal_anchors(paper_body, f"ch-{chapter['id']}")
        chapter_sections.append(
            "\n".join(
                [
                    f"# Chapter {chapter['id']}. {chapter['title']}",
                    "",
                    prefixed,
                    "",
                    "\\newpage" if chapter["id"] != CHAPTERS[-1]["id"] else "",
                ]
            ).strip()
        )

    return "\n".join(
        [
            "---",
            'title: "From Surveillance Capitalism to AI Imperialism"',
            'subtitle: "Omnibus Dossier Volume"',
            'author: ""',
            'date: ""',
            "lang: en-US",
            "---",
            "",
            "# Editorial Preface",
            "",
            "This omnibus volume joins the full chapter sequence into a single dossier-length publication. It preserves the chapter-level evidence apparatus so the reader can move continuously through the argument while still inspecting the bounded evidence surface for each chapter.",
            "",
            "## How to Use This Volume",
            "",
            "- Read each chapter as a standalone paper if needed; chapter-local appendices remain attached.",
            "- Use the corpus companion for the full-source, full-claim, full-entity, full-event, and full-note audit surfaces.",
            "- Treat `Documented Fact`, `Disputed Fact`, `Hypothesis / Interpretation`, and `Speculative Narrative Risk` as distinct evidentiary states throughout the volume.",
            "",
            "## Shared Citation and Evidence Rules",
            "",
            "Body notes point to the real external documents first, then to the chapter-local appendix entries that explain why those sources matter in context. Chapter bibliographies remain local so each chapter still works when extracted from the omnibus.",
            "",
            "\n\n".join(chapter_sections),
            "",
        ]
    ).rstrip() + "\n"


def render_source_companion_entry(record: dict, maps: dict) -> str:
    entry = maps["sources"][record["source_id"]]
    linked_title = markdown_link(record.get("title", record["source_id"]), record.get("url"))
    author = record.get("author") or record.get("publisher") or "Unknown source"
    published = record.get("published_at") or "n.d."
    chapters = ", ".join(f"Chapter {chapter_id}" for chapter_id in record.get("chapter_ids", [])) or "None recorded"
    vectors = ", ".join(vector_by_id(vector_id)["title"] for vector_id in record.get("vector_ids", [])) or "None recorded"
    return "\n".join(
        [
            f"### {entry['label']}. {record.get('title', record['source_id'])} {{#{entry['anchor']}}}",
            f"**External record:** {linked_title}",
            f"**Institution / author:** {author}",
            f"**Date:** {published}",
            f"**Tier / type:** {record.get('source_tier', 'Unknown')} / {record.get('source_type', 'unknown')}",
            f"**Appears in chapters:** {chapters}",
            f"**Connected vectors:** {vectors}",
            f"**Audit ID:** `{record['source_id']}`",
        ]
    )


def render_claim_companion_entry(record: dict, maps: dict) -> str:
    entry = maps["claims"][record["claim_id"]]
    support = ", ".join(
        internal_link(maps["sources"][source_id]["label"], maps["sources"][source_id]["anchor"])
        for source_id in record.get("source_ids", [])
        if source_id in maps["sources"]
    ) or "No source links recorded."
    chapters = ", ".join(f"Chapter {chapter_id}" for chapter_id in record.get("chapter_ids", [])) or "None recorded"
    return "\n".join(
        [
            f"### {entry['label']}. {humanize_claim_title(record.get('claim_text', 'Claim'))} {{#{entry['anchor']}}}",
            f"**Claim statement:** {record.get('claim_text', '')}",
            f"**Evidence status:** {record.get('evidence_level', 'Unknown')}",
            f"**Source support:** {support}",
            f"**Appears in chapters:** {chapters}",
            f"**Audit Claim ID:** `{record['claim_id']}`",
        ]
    )


def render_entity_companion_entry(record: dict, maps: dict) -> str:
    entry = maps["entities"][record["entity_id"]]
    source_links = ", ".join(
        internal_link(maps["sources"][source_id]["label"], maps["sources"][source_id]["anchor"])
        for source_id in record.get("source_ids", [])
        if source_id in maps["sources"]
    ) or "No linked sources recorded."
    vectors = ", ".join(vector_by_id(vector_id)["title"] for vector_id in record.get("connected_vectors", [])) or "None recorded"
    return "\n".join(
        [
            f"### {entry['label']}. {record.get('name', record['entity_id'])} {{#{entry['anchor']}}}",
            f"**Entity type:** {record.get('entity_type', 'Unknown')}",
            f"**Relevance:** {record.get('relevance', 'No relevance note registered.')}",
            f"**Connected vectors:** {vectors}",
            f"**Source support:** {source_links}",
            f"**Audit Entity ID:** `{record['entity_id']}`",
        ]
    )


def render_event_companion_entry(record: dict, maps: dict) -> str:
    entry = maps["events"][record["event_id"]]
    source_links = ", ".join(
        internal_link(maps["sources"][source_id]["label"], maps["sources"][source_id]["anchor"])
        for source_id in record.get("source_ids", [])
        if source_id in maps["sources"]
    ) or "No linked sources recorded."
    chapters = ", ".join(f"Chapter {chapter_id}" for chapter_id in record.get("chapter_ids", [])) or "None recorded"
    return "\n".join(
        [
            f"### {entry['label']}. {record.get('label', record['event_id'])} {{#{entry['anchor']}}}",
            f"**Date:** {record.get('date', 'Unknown')}",
            f"**Description:** {record.get('description', record.get('label', 'No description registered.'))}",
            f"**Source support:** {source_links}",
            f"**Appears in chapters:** {chapters}",
            f"**Audit Event ID:** `{record['event_id']}`",
        ]
    )


def render_note_companion_entry(record: dict, maps: dict, catalog: dict[str, dict]) -> str:
    source_id = record.get("source_id", "")
    note_id = record.get("note_id", "")
    entry = maps["notes"][note_id]
    source_label = maps["sources"].get(source_id, {}).get("label", source_id)
    source_anchor = maps["sources"].get(source_id, {}).get("anchor", "")
    source_link = internal_link(source_label, source_anchor) if source_anchor else source_label
    source_title = catalog.get(source_id, {}).get("title", source_id)
    chapters = ", ".join(f"Chapter {chapter_id}" for chapter_id in record.get("chapter_ids", [])) or "None recorded"
    vectors = ", ".join(vector_by_id(vector_id)["title"] for vector_id in record.get("vector_ids", [])) or "None recorded"
    return "\n".join(
        [
            f"### {entry['label']}. Source note for {source_title} {{#{entry['anchor']}}}",
            f"**Related source:** {source_link}",
            f"**Risk label:** {record.get('risk_level', 'unspecified')}",
            f"**Appears in chapters:** {chapters}",
            f"**Connected vectors:** {vectors}",
            f"**What the note primarily proves:** {record.get('what_it_proves') or record.get('factual_summary') or 'No prove-text registered.'}",
            f"**What the note additionally suggests:** {record.get('what_it_suggests') or 'No suggestion text registered.'}",
            f"**Audit Note ID:** `{note_id}`",
            f"**Audit Source ID:** `{source_id}`",
        ]
    )


def render_companion_crosswalks(stats: dict) -> str:
    chapter_lines = []
    for chapter_id, slice_ in stats["by_chapter"].items():
        chapter = slice_["chapter"]
        chapter_lines.append(
            f"- Chapter {chapter_id} ({chapter['title']}): {len(slice_['sources'])} sources, {len(slice_['claims'])} claims, "
            f"{len(slice_['entities'])} entities, {len(slice_['events'])} events, {len(slice_['notes'])} notes."
        )

    vector_lines = []
    for vector in VECTORS:
        chapter_refs = ", ".join(f"Chapter {chapter_id}" for chapter_id in vector["chapter_ids"])
        vector_lines.append(f"- {vector['title']}: {chapter_refs}.")

    return "\n".join(
        [
            "## Chapter-to-Corpus Crosswalk",
            "",
            "\n".join(chapter_lines),
            "",
            "## Vector-to-Chapter Crosswalk",
            "",
            "\n".join(vector_lines),
            "",
        ]
    )


def render_corpus_companion(root: Path, stats: dict, companion_maps: dict) -> str:
    catalog = source_catalog(root)
    blocks = [
        "---",
        'title: "Corpus Companion: Sources, Claims, Entities, Events, and Notes"',
        'subtitle: "Audit volume for From Surveillance Capitalism to AI Imperialism"',
        'author: ""',
        'date: ""',
        "lang: en-US",
        "---",
        "",
        "# How to Use This Companion",
        "",
        "This companion is the project-wide audit surface. Use it when you want to inspect the full corpus behind the standalone papers and the omnibus dossier without reading repo internals.",
        "",
        "## Navigation Guide",
        "",
        "- If a paper footnote sends you to an external report, article, court order, filing, or technical paper, open that live link first.",
        "- If a paper then points you to `Appendix A`, `B`, `C`, `D`, or `E`, stay inside that paper to see why the source, claim, event, entity, or evidence boundary matters in that chapter.",
        "- If a paper mentions a corpus label such as `Source S-066`, `Claim C-212`, `Event T-014`, or `Note N-097`, use this companion to inspect the project-wide audit record for that item.",
        "- `Source` entries identify the real underlying document and where it appears across the dossier.",
        "- `Claim` entries tell you exactly what proposition the project extracted from the record and how it is labeled evidentially.",
        "- `Event` entries reconstruct dated turning points used across chapters.",
        "- `Note` entries summarize what a source proves, what it suggests, and where caution is required.",
        "",
        "## Evidence Labels",
        "",
        "- `Documented Fact`: a claim the project treats as directly supported by the documentary record at the required threshold.",
        "- `Disputed Fact`: a claim with serious documented disagreement or unresolved institutional conflict.",
        "- `Hypothesis / Interpretation`: a bounded political or analytical reading built from cited facts, not a settled fact in itself.",
        "- `Speculative Narrative Risk`: a claim shape the dossier explicitly warns against because it outruns the record.",
        "",
        "## Corpus Totals",
        "",
        f"- Sources: {stats['totals']['sources']}",
        f"- Claims: {stats['totals']['claims']}",
        f"- Entities: {stats['totals']['entities']}",
        f"- Events: {stats['totals']['events']}",
        f"- Notes: {stats['totals']['notes']}",
        "",
        render_companion_crosswalks(stats),
        "## Source Register",
        "",
        format_blocks([render_source_companion_entry(record, companion_maps) for record in sorted(stats["sources"], key=lambda item: item.get("source_id", ""))]),
        "",
        "## Claim Register",
        "",
        format_blocks([render_claim_companion_entry(record, companion_maps) for record in sorted(stats["claims"], key=lambda item: item.get("claim_id", ""))]),
        "",
        "## Entity Register",
        "",
        format_blocks([render_entity_companion_entry(record, companion_maps) for record in sorted(stats["entities"], key=lambda item: item.get("entity_id", ""))]),
        "",
        "## Event Register",
        "",
        format_blocks(
            [render_event_companion_entry(record, companion_maps) for record in sorted(stats["events"], key=lambda item: (item.get("date", ""), item.get("event_id", "")))]
        ),
        "",
        "## Note Register",
        "",
        format_blocks([render_note_companion_entry(record, companion_maps, catalog) for record in sorted(stats["notes"], key=lambda item: item.get("note_id", ""))]),
        "",
    ]
    return "\n".join(blocks).rstrip() + "\n"


def render_publication_index(root: Path, base_prefix: str = "../", book_index_rel: str | None = None) -> str:
    paper_paths = sorted((root / "papers").glob("*.md"))
    volume_paths = sorted((root / "volumes").glob("*.md"))
    totals = corpus_stats(root)["totals"]

    paper_items = []
    for paper_path in paper_paths:
        stem = paper_path.stem
        title = extract_title(paper_path.read_text(encoding="utf-8"), stem[:2]).strip('"')
        pdf_rel = f"{base_prefix}papers/pdf/{stem}/{stem}.pdf"
        html_rel = f"{base_prefix}papers/html/{stem}.html"
        paper_items.append(
            f"<li><strong>{escape(title)}</strong><br>"
            f"<a href=\"{escape(html_rel)}\">HTML</a> | "
            f"<a href=\"{escape(pdf_rel)}\">PDF</a></li>"
        )

    volume_items = []
    for volume_path in volume_paths:
        stem = volume_path.stem
        frontmatter = parse_frontmatter(volume_path.read_text(encoding='utf-8'))
        title = str(frontmatter.get("title", stem)).strip('"')
        pdf_rel = f"{base_prefix}volumes/pdf/{stem}/{stem}.pdf"
        html_rel = f"{base_prefix}volumes/html/{stem}.html"
        volume_items.append(
            f"<li><strong>{escape(title)}</strong><br>"
            f"<a href=\"{escape(html_rel)}\">HTML</a> | "
            f"<a href=\"{escape(pdf_rel)}\">PDF</a></li>"
        )

    literary_card = ""
    literary_section = ""
    if book_index_rel is not None:
        literary_card = (
            "    <div class=\"card featured\"><h2>Children of the Feed</h2>"
            "<p>A public literary edition of the dossier: magazine-style reading, chapter cards, visuals, lighter notes, and a full-book HTML/PDF experience for general readers.</p>"
            f"<p><a href=\"{escape(book_index_rel)}\">Open the literary edition</a></p></div>"
        )
        literary_section = "\n".join(
            [
                "  <h2>Literary Edition</h2>",
                "  <ul>",
                f"    <li><strong>Children of the Feed. Servants of the AI God</strong><br><a href=\"{escape(book_index_rel)}\">Literary landing page</a></li>",
                "  </ul>",
            ]
        )
    repo_card = (
        "    <div class=\"card\"><h2>Clone and contribute</h2>"
        "<p>This research program is open to inspection, extension, and republication. Clone the repository to review the corpus, papers, volumes, and build pipeline, then contribute improvements or new evidence.</p>"
        f"<p><a href=\"{escape(AI_EMPIRE_REPO_URL)}\">Open the GitHub repository</a></p></div>"
    )

    return "\n".join(
        [
            "<!DOCTYPE html>",
            "<html lang=\"en\">",
            "<head>",
            "  <meta charset=\"utf-8\">",
            "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            "  <title>AI Empire Publication Index</title>",
            "  <style>",
            "    body { font-family: Georgia, 'Times New Roman', serif; margin: 2rem auto; max-width: 980px; line-height: 1.6; color: #111; padding: 0 1.2rem; }",
            "    h1, h2 { line-height: 1.2; }",
            "    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin: 1.5rem 0; }",
            "    .card { border: 1px solid #d7d7d7; border-radius: 10px; padding: 1rem; background: #fafafa; }",
            "    .featured { background: linear-gradient(135deg, #111822, #1c1313); color: #f3ecdd; border-color: #6e4c32; }",
            "    .featured a { color: #ffd166; }",
            "    .public-brand-header { background: #fffefb; border-bottom: 1px solid #e6dfd2; box-shadow: 0 4px 14px rgba(0,0,0,0.05); }",
            "    .public-brand-header-inner { min-height: 66px; padding: 0.45rem 1.25rem; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; }",
            "    .public-brand-link { display: inline-flex; justify-self: center; align-items: center; padding: 0; background: transparent; border-radius: 0; }",
            "    .public-brand-logo { display: block; width: min(176px, 38vw); max-height: 42px; height: auto; }",
            "    .public-brand-back, .public-brand-back-spacer { display: block; }",
            "    .public-brand-back { justify-self: start; color: #0b57d0; font-family: Arial, sans-serif; font-size: 0.95rem; text-decoration: none; }",
            "    .patrimony-card { border: 1px solid #5d3a26; border-radius: 16px; padding: 1.15rem 1.1rem 1.2rem; background: linear-gradient(135deg, #111822, #21120f); color: #f7eddb; box-shadow: 0 18px 40px rgba(0,0,0,0.12); }",
            "    .patrimony-card h2 { margin: 0; font-size: 1.6rem; line-height: 1.05; text-transform: uppercase; }",
            "    .patrimony-kicker { margin: 0 0 0.45rem; font-family: Arial, sans-serif; letter-spacing: 0.18em; text-transform: uppercase; color: #ffd166; font-size: 0.74rem; }",
            "    .patrimony-deck, .patrimony-bridge, .patrimony-brand, .patrimony-source { color: #efe5d4; }",
            "    .patrimony-principles { margin: 0.8rem 0 0; padding-left: 1.15rem; }",
            "    .patrimony-principles li { margin: 0.4rem 0; }",
            "    .patrimony-card a { color: #ffd166; }",
            "    .video-hero { margin: 1.25rem 0 1.75rem; }",
            "    .video-frame { position: relative; width: 100%; aspect-ratio: 16 / 9; overflow: hidden; border-radius: 12px; border: 1px solid #d7d7d7; background: #f7f7f7; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }",
            "    .video-frame iframe { display: block; width: 100%; height: 100%; border: 0; }",
            "    code { background: #f0f0f0; padding: 0.1rem 0.35rem; border-radius: 4px; }",
            "    a { color: #0b57d0; }",
            "    ul { padding-left: 1.2rem; }",
            "  </style>",
            "</head>",
            "<body>",
            render_public_logo_header("assets/brand/waken-ai-black.webp"),
            render_vimeo_hero_block(),
            "  <h1>AI Empire Research Program</h1>",
            "  <p>This index is the reader-facing entry point for the publication package. The academic papers defend the dossier chapter by chapter, the omnibus carries the full argument continuously, the corpus companion exposes the audit surface, and the literary branch opens a more public-facing reading path.</p>",
            "  <div class=\"grid\">",
            render_patimony_html_card(
                compact=True,
                show_wakenai=True,
                extra_sentence="This publication series exists to empower humanity and place the ownership question in plain view from the first screen.",
            ),
            "    <div class=\"card\"><h2>How to read a paper</h2><p>Use the footnotes to open real external sources. Use the paper-local appendices to understand why each source matters in that paper. Use the corpus companion when a paper mentions a registry code such as <code>Source S-066</code> or <code>Claim C-212</code>.</p></div>",
            f"    <div class=\"card\"><h2>Corpus totals</h2><ul><li>{totals['sources']} sources</li><li>{totals['claims']} claims</li><li>{totals['entities']} entities</li><li>{totals['events']} events</li><li>{totals['notes']} notes</li></ul></div>",
            "    <div class=\"card\"><h2>Publication logic</h2><p>Standalone papers defend each chapter independently. The omnibus supports continuous reading. The corpus companion is the professional audit volume for researchers who want to inspect the full underlying system.</p></div>",
            repo_card,
            literary_card,
            "  </div>",
            literary_section,
            "  <h2>Standalone Papers</h2>",
            "  <ul>",
            *paper_items,
            "  </ul>",
            "  <h2>Shared Volumes</h2>",
            "  <ul>",
            *volume_items,
            "  </ul>",
            "  <h2>Where specific audit labels live</h2>",
            "  <ul>",
            "    <li><code>Source S-###</code>: open the corpus companion and go to the Source Register.</li>",
            "    <li><code>Claim C-###</code>: open the corpus companion and go to the Claim Register.</li>",
            "    <li><code>Event T-###</code>: open the corpus companion and go to the Event Register.</li>",
            "    <li><code>Note N-###</code>: open the corpus companion and go to the Note Register.</li>",
            "    <li><code>Appendix A/B/C/D/E</code>: stay inside the current paper or chapter-local appendix.</li>",
            "  </ul>",
            f"  <p><strong><a href=\"{escape(WAKENAI_URL)}\">{escape(WAKENAI_LABEL)}</a></strong></p>",
            "</body>",
            "</html>",
            "",
        ]
    )


def prefix_internal_anchors(content: str, prefix: str) -> str:
    updated = re.sub(r"\{#([^}]+)\}", lambda match: "{#" + prefix + "-" + match.group(1) + "}", content)
    updated = re.sub(r"\]\(#([^)]+)\)", lambda match: "](#" + prefix + "-" + match.group(1) + ")", updated)
    return updated


def locate_paper_source(root: Path, chapter_id: str) -> Path:
    chapter_path = chapter_corpus_path(root, chapter_id)
    if chapter_path.exists():
        return chapter_path
    current = existing_paper_path(root, chapter_id)
    if current is not None:
        return current
    raise FileNotFoundError(f"No chapter corpus found for chapter {chapter_id}")


def write_public_volumes(root: Path, stats: dict, companion_maps: dict) -> None:
    volumes_root = root / "volumes"
    ensure_dir(volumes_root)
    overwrite(volumes_root / "dossier_omnibus.md", render_dossier_omnibus(root))
    overwrite(volumes_root / "corpus_companion.md", render_corpus_companion(root, stats, companion_maps))


def seed_papers(root: Path, overwrite_existing: bool = False) -> None:
    ensure_dir(root / "papers")
    ensure_dir(root / "papers" / "appendix")
    ensure_dir(root / "volumes")
    stats = corpus_stats(root)
    companion_maps = build_companion_label_maps(stats)
    write_internal_appendix(root, stats)
    for chapter in CHAPTERS:
        source_path = locate_paper_source(root, chapter["id"])
        target_path = paper_path_for_chapter(root, chapter["id"])
        if target_path.exists() and not overwrite_existing:
            continue
        content = source_path.read_text(encoding="utf-8")
        normalized = normalize_paper_markdown(content, chapter["id"], root, stats, companion_maps)
        overwrite(target_path, normalized)

    write_public_volumes(root, stats, companion_maps)


def validate_references(root: Path, document_path: Path) -> None:
    content = document_path.read_text(encoding="utf-8")
    source_ids = {record["source_id"] for record in load_jsonl(root / "sources" / "catalog.jsonl")}
    references = first_available_section(content, ["## References / Bibliography", "## References"])
    for line in references.splitlines():
        match = re.search(r"Audit ID:\s*`?([A-Za-z0-9._-]+)`?", line)
        if match and match.group(1) not in source_ids:
            raise ValueError(f"{document_path.name} references unknown source id: {match.group(1)}")


def export_markdown_document(
    markdown_path: Path,
    tex_root: Path,
    pdf_root: Path,
    processed_root: Path,
    html_root: Path,
    header_path: Path,
    css_path: Path,
    child_env: dict[str, str],
    resource_paths: list[str] | None = None,
    font_size: str = "11pt",
    build_pdf: bool = True,
    html_transform: Callable[[str], str] | None = None,
) -> Path:
    content = markdown_path.read_text(encoding="utf-8")
    processed_path = processed_root / markdown_path.name
    overwrite(processed_path, content)

    tex_path = tex_root / f"{markdown_path.stem}.tex"
    pdf_outdir = pdf_root / markdown_path.stem
    html_path = html_root / f"{markdown_path.stem}.html"
    ensure_dir(pdf_outdir)
    ensure_dir(html_root)
    resource_arg = ":".join(resource_paths or [str(markdown_path.parent)])
    subprocess.run(
        [
            "pandoc",
            "--from",
            "markdown+footnotes",
            "--standalone",
            "--number-sections",
            "--include-in-header",
            str(header_path),
            "--resource-path",
            resource_arg,
            "-V",
            f"fontsize={font_size}",
            "-V",
            "papersize=letter",
            str(processed_path),
            "-o",
            str(tex_path),
        ],
        check=True,
        env=child_env,
    )
    subprocess.run(
        [
            "pandoc",
            "--from",
            "markdown+footnotes",
            "--standalone",
            "--toc",
            "--css",
            css_path.name,
            "--resource-path",
            resource_arg,
            str(processed_path),
            "-o",
            str(html_path),
        ],
        check=True,
        env=child_env,
        cwd=str(html_root),
    )
    if html_transform is not None:
        overwrite(html_path, html_transform(html_path.read_text(encoding="utf-8")))
    if build_pdf:
        subprocess.run(
            [
                "tectonic",
                "--outdir",
                str(pdf_outdir),
                str(tex_path),
            ],
            check=True,
            env=child_env,
        )
    return tex_path


def export_papers(root: Path) -> None:
    pandoc = subprocess.run(["which", "pandoc"], capture_output=True, text=True)
    tectonic = subprocess.run(["which", "tectonic"], capture_output=True, text=True)
    if pandoc.returncode != 0:
        raise RuntimeError("pandoc is required for paper export but is not installed")
    if tectonic.returncode != 0:
        raise RuntimeError("tectonic is required for paper export but is not installed")

    build_papers_root = root / "build" / "papers"
    build_volumes_root = root / "build" / "volumes"
    papers_tex_root = build_papers_root / "tex"
    papers_pdf_root = build_papers_root / "pdf"
    papers_processed_root = build_papers_root / "processed"
    papers_html_root = build_papers_root / "html"
    volumes_tex_root = build_volumes_root / "tex"
    volumes_pdf_root = build_volumes_root / "pdf"
    volumes_processed_root = build_volumes_root / "processed"
    volumes_html_root = build_volumes_root / "html"

    for path in [
        papers_tex_root,
        papers_pdf_root,
        papers_processed_root,
        papers_html_root,
        build_papers_root / "assets",
        volumes_tex_root,
        volumes_pdf_root,
        volumes_processed_root,
        volumes_html_root,
    ]:
        ensure_dir(path)

    copy_brand_logo(root, build_papers_root)

    child_env = os.environ.copy()

    header_path = root / "apps" / "templates" / "paper_export_header.tex"
    css_source_path = root / "apps" / "templates" / "paper_export.css"
    papers_css_path = papers_html_root / css_source_path.name
    volumes_css_path = volumes_html_root / css_source_path.name
    overwrite(papers_css_path, css_source_path.read_text(encoding="utf-8"))
    overwrite(volumes_css_path, css_source_path.read_text(encoding="utf-8"))

    paper_paths = sorted((root / "papers").glob("*.md"))
    pdf_targets: list[tuple[Path, Path, Path]] = []
    for paper_path in paper_paths:
        validate_references(root, paper_path)
        tex_path = export_markdown_document(
            paper_path,
            papers_tex_root,
            papers_pdf_root,
            papers_processed_root,
            papers_html_root,
            header_path,
            papers_css_path,
            child_env,
            resource_paths=[str(root), str(root / "papers"), str(root / "chapters")],
            font_size="11pt",
            build_pdf=False,
            html_transform=inject_paper_navigation,
        )
        html_path = papers_html_root / f"{paper_path.stem}.html"
        pdf_targets.append((tex_path, html_path, papers_pdf_root / paper_path.stem / f"{paper_path.stem}.pdf"))

    volume_paths = sorted((root / "volumes").glob("*.md"))
    volume_pdf_targets: list[tuple[Path, Path, Path]] = []
    for volume_path in volume_paths:
        tex_path = export_markdown_document(
            volume_path,
            volumes_tex_root,
            volumes_pdf_root,
            volumes_processed_root,
            volumes_html_root,
            header_path,
            volumes_css_path,
            child_env,
            resource_paths=[str(root), str(root / "volumes"), str(root / "papers")],
            font_size="11pt",
            build_pdf=False,
        )
        html_path = volumes_html_root / f"{volume_path.stem}.html"
        volume_pdf_targets.append((tex_path, html_path, volumes_pdf_root / volume_path.stem / f"{volume_path.stem}.pdf"))

    pdf_failures: list[str] = []
    for tex_path, html_path, pdf_path in [*pdf_targets, *volume_pdf_targets]:
        ensure_dir(pdf_path.parent)
        try:
            render_pdf_with_playwright(html_path, pdf_path, os.environ.copy())
            continue
        except Exception as playwright_exc:
            try:
                subprocess.run(
                    [
                        "tectonic",
                        "--outdir",
                        str(pdf_path.parent),
                        str(tex_path),
                    ],
                    check=True,
                    env=child_env,
                )
            except subprocess.CalledProcessError as exc:
                pdf_failures.append(
                    f"{tex_path.name}: playwright failed ({playwright_exc}); tectonic failed ({exc})"
                )

    publication_index_root = root / "build" / "publication"
    ensure_dir(publication_index_root)
    overwrite(publication_index_root / "index.html", render_publication_index(root))
    if pdf_failures:
        details = "\n".join(pdf_failures)
        raise RuntimeError(
            "Paper/volume HTML and TeX exports completed, but one or more PDF builds failed.\n"
            f"{details}"
        )
