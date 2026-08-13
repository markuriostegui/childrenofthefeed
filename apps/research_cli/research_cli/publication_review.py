from __future__ import annotations

import json
import sys
import re
from pathlib import Path
from html.parser import HTMLParser

from .fs import dump_json, ensure_dir, overwrite

REPO_PATH_PATTERN = re.compile(r"/Users/hassan/repos/AI-Empire")
URL_PATTERN = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")
ANCHOR_PATTERN = re.compile(r"\{#([^}]+)\}")
HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+)$", re.M)
PENDING_PATTERN = re.compile(r"\bpending\b", re.I)
FOOTNOTE_PATTERN = re.compile(r"\^\[Sources:\s")
BIBLIO_ENTRY_PATTERN = re.compile(r"^\d+\.\s", re.M)
APPENDIX_REF_PATTERN = re.compile(r"\bAppendix\s+[A-E][0-9]*\b")
FORBIDDEN_SITE_SEGMENTS = {
    ".DS_Store",
    "cache",
    "config",
    "processed",
    "previews",
    "tectonic-home",
}

PAPER_REQUIRED_HEADINGS = [
    "Abstract",
    "Keywords",
    "Research Question",
    "Scope and Framing Note",
    "Central Thesis",
    "Evidence and Method Note",
    "Introduction",
    "Historical or Institutional Context",
    "Main Analysis",
    "Position Within the Series",
    "Counterarguments",
    "Limits of the Evidence",
    "Reform Relevance",
    "Conclusion",
    "Notes",
    "References / Bibliography",
    "Appendix A. Source Register for This Paper",
    "Appendix B. Claims Used in This Paper",
    "Appendix C. Timeline Slice",
    "Appendix D. Relevant Entities",
    "Appendix E. Evidence Boundaries",
]

OMNIBUS_REQUIRED_HEADINGS = [
    "Editorial Preface",
    "How to Use This Volume",
    "Shared Citation and Evidence Rules",
]

COMPANION_REQUIRED_HEADINGS = [
    "How to Use This Companion",
    "Evidence Labels",
    "Corpus Totals",
    "Chapter-to-Corpus Crosswalk",
    "Vector-to-Chapter Crosswalk",
    "Source Register",
    "Claim Register",
    "Entity Register",
    "Event Register",
    "Note Register",
]

BOOK_REQUIRED_HEADINGS = [
    "Deck",
    "Opening",
    "Main Narrative",
    "Research Basis",
    "Next",
]

FULL_BOOK_REQUIRED_HEADINGS = [
    "Preface",
    "Method and Evidence Note",
    "Chapter-to-Paper Reading Map",
]


def load_pdf_reader(pdf_path: Path):
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        runtime_roots = sorted(
            Path.home().glob(".cache/codex-runtimes/*/dependencies/python/lib/python*/site-packages")
        )
        for candidate in runtime_roots:
            if (candidate / "pypdf").exists():
                sys.path.append(str(candidate))
                from pypdf import PdfReader  # type: ignore

                break
        else:
            raise RuntimeError(
                "pypdf is required for publication QA. Install it in the active environment or use a Codex bundled runtime."
            )

    return PdfReader(str(pdf_path))


def markdown_headings(content: str) -> list[str]:
    return [match.group(1).strip() for match in HEADING_PATTERN.finditer(content)]


def duplicate_anchors(content: str) -> list[str]:
    counts: dict[str, int] = {}
    for match in ANCHOR_PATTERN.finditer(content):
        anchor = match.group(1)
        counts[anchor] = counts.get(anchor, 0) + 1
    return sorted(anchor for anchor, count in counts.items() if count > 1)


def pdf_link_stats(pdf_path: Path) -> dict:
    reader = load_pdf_reader(pdf_path)
    external_links = 0
    internal_links = 0
    external_targets: list[str] = []
    for page in reader.pages:
        annotations = page.get("/Annots") or []
        for annotation_ref in annotations:
            try:
                annotation = annotation_ref.get_object()
            except Exception:
                continue
            if annotation.get("/Subtype") != "/Link":
                continue
            action = annotation.get("/A")
            if action and action.get("/URI"):
                external_links += 1
                uri = str(action.get("/URI"))
                if uri not in external_targets:
                    external_targets.append(uri)
                continue
            if action and action.get("/S") == "/GoTo":
                internal_links += 1
                continue
            if annotation.get("/Dest") is not None:
                internal_links += 1
    return {
        "page_count": len(reader.pages),
        "external_link_annotations": external_links,
        "internal_link_annotations": internal_links,
        "external_link_samples": external_targets[:12],
    }


def critique_lines(result: dict) -> list[str]:
    lines: list[str] = []
    if result["missing_headings"]:
        lines.append(
            "Missing required sections: " + ", ".join(result["missing_headings"])
        )
    else:
        lines.append("Required scholarly sections are present.")
    if result["placeholder_hits"]:
        lines.append("Placeholder language is still present and needs cleanup.")
    else:
        lines.append("No obvious placeholder leakage remains.")
    if result.get("require_external_links", True) and result["external_link_annotations"] == 0:
        lines.append("No clickable external PDF links were detected.")
    elif result["external_link_annotations"] > 0:
        lines.append(
            f"Clickable external links are present in the PDF ({result['external_link_annotations']} annotations)."
        )
    else:
        lines.append("This document does not require external-link density because it is a literary derivative rather than the primary documentary layer.")
    if result["appendix_reference_count"] > 0 and result["internal_link_annotations"] == 0:
        lines.append("Appendix references exist, but no internal PDF navigation was detected.")
    elif result["internal_link_annotations"] > 0:
        lines.append(
            f"Internal PDF navigation is present ({result['internal_link_annotations']} annotations)."
        )
    if result["raw_repo_path_hits"]:
        lines.append("Reader-facing content still leaks raw repo paths.")
    if result["duplicate_anchors"]:
        lines.append("Duplicate internal anchors were detected in the Markdown source.")
    if result.get("pdf_is_stale"):
        lines.append(
            "The PDF is older than its Markdown source and should be rebuilt before publication."
        )
    if result.get("expect_bibliography", True) and result["bibliography_entry_count"] == 0:
        lines.append("No bibliography entries were detected.")
    return lines


def evaluate_status(result: dict) -> str:
    if result["missing_headings"] or result["placeholder_hits"]:
        return "fail"
    if result.get("pdf_is_stale"):
        return "fail"
    if result.get("require_external_links", True) and result["external_link_annotations"] == 0:
        return "fail"
    if result["raw_repo_path_hits"] or result["duplicate_anchors"]:
        return "warn"
    if result["appendix_reference_count"] > 0 and result["internal_link_annotations"] == 0:
        return "warn"
    return "pass"


def analyze_markdown_pdf_pair(
    markdown_path: Path,
    pdf_path: Path,
    required_headings: list[str],
    expect_bibliography: bool = True,
    require_external_links: bool = True,
) -> dict:
    content = markdown_path.read_text(encoding="utf-8")
    headings = markdown_headings(content)
    missing_headings = [heading for heading in required_headings if heading not in headings]
    urls = URL_PATTERN.findall(content)
    unique_urls = list(dict.fromkeys(urls))
    pdf_stats = pdf_link_stats(pdf_path)
    markdown_mtime = markdown_path.stat().st_mtime
    pdf_mtime = pdf_path.stat().st_mtime
    result = {
        "document": markdown_path.stem,
        "markdown_path": str(markdown_path),
        "pdf_path": str(pdf_path),
        "page_count": pdf_stats["page_count"],
        "heading_count": len(headings),
        "missing_headings": missing_headings,
        "placeholder_hits": len(PENDING_PATTERN.findall(content)),
        "raw_repo_path_hits": len(REPO_PATH_PATTERN.findall(content)),
        "duplicate_anchors": duplicate_anchors(content),
        "bibliography_entry_count": len(BIBLIO_ENTRY_PATTERN.findall(content)),
        "appendix_reference_count": len(APPENDIX_REF_PATTERN.findall(content)),
        "footnote_source_markers": len(FOOTNOTE_PATTERN.findall(content)),
        "external_links_in_markdown": len(unique_urls),
        "expect_bibliography": expect_bibliography,
        "require_external_links": require_external_links,
        "external_link_annotations": pdf_stats["external_link_annotations"],
        "internal_link_annotations": pdf_stats["internal_link_annotations"],
        "external_link_samples": pdf_stats["external_link_samples"],
        "markdown_mtime": markdown_mtime,
        "pdf_mtime": pdf_mtime,
        "pdf_is_stale": pdf_mtime + 1 < markdown_mtime,
    }
    result["status"] = evaluate_status(result)
    result["critique"] = critique_lines(result)
    return result


def volume_checks(content: str, required_headings: list[str]) -> dict:
    headings = markdown_headings(content)
    return {
        "heading_count": len(headings),
        "missing_headings": [heading for heading in required_headings if heading not in headings],
        "placeholder_hits": len(PENDING_PATTERN.findall(content)),
        "raw_repo_path_hits": len(REPO_PATH_PATTERN.findall(content)),
        "duplicate_anchors": duplicate_anchors(content),
        "bibliography_entry_count": len(BIBLIO_ENTRY_PATTERN.findall(content)),
        "appendix_reference_count": len(APPENDIX_REF_PATTERN.findall(content)),
        "footnote_source_markers": len(FOOTNOTE_PATTERN.findall(content)),
        "external_links_in_markdown": len(dict.fromkeys(URL_PATTERN.findall(content))),
    }


def analyze_volume(
    markdown_path: Path,
    pdf_path: Path,
    required_headings: list[str],
    expected_counts: dict | None = None,
    expect_bibliography: bool = True,
) -> dict:
    content = markdown_path.read_text(encoding="utf-8")
    checks = volume_checks(content, required_headings)
    pdf_stats = pdf_link_stats(pdf_path)
    markdown_mtime = markdown_path.stat().st_mtime
    pdf_mtime = pdf_path.stat().st_mtime
    result = {
        "document": markdown_path.stem,
        "markdown_path": str(markdown_path),
        "pdf_path": str(pdf_path),
        "page_count": pdf_stats["page_count"],
        **checks,
        "expect_bibliography": expect_bibliography,
        "external_link_annotations": pdf_stats["external_link_annotations"],
        "internal_link_annotations": pdf_stats["internal_link_annotations"],
        "external_link_samples": pdf_stats["external_link_samples"],
        "markdown_mtime": markdown_mtime,
        "pdf_mtime": pdf_mtime,
        "pdf_is_stale": pdf_mtime + 1 < markdown_mtime,
    }
    if expected_counts:
        text = content
        count_findings = {}
        for label, value in expected_counts.items():
            count_findings[label] = str(value) in text
        result["expected_counts_present"] = count_findings
    result["status"] = evaluate_status(result)
    result["critique"] = critique_lines(result)
    return result


def render_report(results: dict) -> str:
    paper_results = results["papers"]
    volume_results = results["volumes"]
    book_results = results.get("books", [])
    site_result = results.get("site", {})
    site_tree_result = results.get("site_tree", {})
    website_result = results.get("website", {})
    lines = [
        "# Publication QA Report",
        "",
        "## Summary",
        "",
        f"- Standalone papers reviewed: {len(paper_results)}",
        f"- Shared volumes reviewed: {len(volume_results)}",
        f"- Paper passes: {sum(1 for item in paper_results if item['status'] == 'pass')}",
        f"- Paper warnings: {sum(1 for item in paper_results if item['status'] == 'warn')}",
        f"- Paper failures: {sum(1 for item in paper_results if item['status'] == 'fail')}",
        f"- Literary book passes: {sum(1 for item in book_results if item['status'] == 'pass')}",
        f"- Literary book warnings: {sum(1 for item in book_results if item['status'] == 'warn')}",
        f"- Literary book failures: {sum(1 for item in book_results if item['status'] == 'fail')}",
        f"- Volume passes: {sum(1 for item in volume_results if item['status'] == 'pass')}",
        f"- Volume warnings: {sum(1 for item in volume_results if item['status'] == 'warn')}",
        f"- Volume failures: {sum(1 for item in volume_results if item['status'] == 'fail')}",
        f"- Site index status: {site_result.get('status', 'not-run')}",
        f"- Site tree status: {site_tree_result.get('status', 'not-run')}",
        f"- Website bundle status: {website_result.get('status', 'not-run')}",
        "",
        "## Standalone Papers",
        "",
    ]
    for item in paper_results:
        lines.extend(
            [
                f"### {item['document']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Pages: {item['page_count']}",
                f"- Missing required headings: {len(item['missing_headings'])}",
                f"- Placeholder hits: {item['placeholder_hits']}",
                f"- Bibliography entries: {item['bibliography_entry_count']}",
                f"- Appendix references: {item['appendix_reference_count']}",
                f"- External Markdown links: {item['external_links_in_markdown']}",
                f"- External PDF link annotations: {item['external_link_annotations']}",
                f"- Internal PDF link annotations: {item['internal_link_annotations']}",
                "",
                "Researcher critique:",
            ]
        )
        lines.extend(f"- {line}" for line in item["critique"])
        if item["missing_headings"]:
            lines.append("- Missing headings detail: " + ", ".join(item["missing_headings"]))
        if item["duplicate_anchors"]:
            lines.append("- Duplicate anchors: " + ", ".join(item["duplicate_anchors"][:8]))
        lines.append("")

    lines.extend(["## Shared Volumes", ""])
    for item in volume_results:
        lines.extend(
            [
                f"### {item['document']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Pages: {item['page_count']}",
                f"- Missing required headings: {len(item['missing_headings'])}",
                f"- Placeholder hits: {item['placeholder_hits']}",
                f"- External Markdown links: {item['external_links_in_markdown']}",
                f"- External PDF link annotations: {item['external_link_annotations']}",
                f"- Internal PDF link annotations: {item['internal_link_annotations']}",
                "",
                "Researcher critique:",
            ]
        )
        lines.extend(f"- {line}" for line in item["critique"])
        if item.get("expected_counts_present"):
            missing = [label for label, present in item["expected_counts_present"].items() if not present]
            if missing:
                lines.append("- Expected count labels missing: " + ", ".join(missing))
            else:
                lines.append("- Expected corpus totals are present.")
        lines.append("")

    lines.extend(["## Literary Book Outputs", ""])
    for item in book_results:
        lines.extend(
            [
                f"### {item['document']}",
                "",
                f"- Status: `{item['status']}`",
                f"- Pages: {item['page_count']}",
                f"- Missing required headings: {len(item['missing_headings'])}",
                f"- Placeholder hits: {item['placeholder_hits']}",
                f"- External Markdown links: {item['external_links_in_markdown']}",
                f"- External PDF link annotations: {item['external_link_annotations']}",
                f"- Internal PDF link annotations: {item['internal_link_annotations']}",
                "",
                "Researcher critique:",
            ]
        )
        lines.extend(f"- {line}" for line in item["critique"])
        if item["missing_headings"]:
            lines.append("- Missing headings detail: " + ", ".join(item["missing_headings"]))
        lines.append("")

    if site_result:
        lines.extend(
            [
                "## Public Site",
                "",
                f"- Status: `{site_result.get('status', 'unknown')}`",
                f"- Literary card present: {site_result.get('literary_card_present', False)}",
                f"- Book link present: {site_result.get('book_link_present', False)}",
                f"- Raw repo path hits: {site_result.get('raw_repo_path_hits', 0)}",
                "",
            ]
        )
    if site_tree_result:
        lines.extend(
            [
                "## Site Tree Integrity",
                "",
                f"- Status: `{site_tree_result.get('status', 'unknown')}`",
                f"- HTML files checked: {site_tree_result.get('html_file_count', 0)}",
                f"- Local references checked: {site_tree_result.get('checked_reference_count', 0)}",
                f"- Missing local targets: {site_tree_result.get('missing_local_target_count', 0)}",
                f"- Forbidden public artifacts: {site_tree_result.get('forbidden_artifact_count', 0)}",
                "",
            ]
        )
        if site_tree_result.get("missing_local_targets"):
            lines.append("Missing targets detail:")
            for item in site_tree_result["missing_local_targets"]:
                lines.append(
                    f"- {item['document']} -> {item['attribute']} `{item['reference']}`"
                )
            lines.append("")
        if site_tree_result.get("forbidden_artifacts"):
            lines.append("Forbidden public artifacts detail:")
            for item in site_tree_result["forbidden_artifacts"]:
                lines.append(f"- {item}")
            lines.append("")
    if website_result:
        lines.extend(
            [
                "## Story Reader Website",
                "",
                f"- Status: `{website_result.get('status', 'unknown')}`",
                f"- Index present: {website_result.get('index_present', False)}",
                f"- Chapters JSON present: {website_result.get('chapters_json_present', False)}",
                f"- Chapters parsed: {website_result.get('chapter_count', 0)}",
                f"- Blocks counted: {website_result.get('block_count', 0)}",
                f"- Missing titles or blocks: {website_result.get('chapter_shape_issue_count', 0)}",
                f"- Broken image paths: {website_result.get('broken_image_count', 0)}",
                "",
            ]
        )
        if website_result.get("errors"):
            lines.append("Website bundle issues:")
            for item in website_result["errors"]:
                lines.append(f"- {item}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def analyze_site_index(site_index_path: Path) -> dict:
    content = site_index_path.read_text(encoding="utf-8")
    literary_card_present = "Children of the Feed" in content
    book_link_present = "book/index.html" in content
    raw_repo_path_hits = len(REPO_PATH_PATTERN.findall(content))
    status = "pass"
    if not literary_card_present or not book_link_present:
        status = "fail"
    elif raw_repo_path_hits:
        status = "warn"
    return {
        "status": status,
        "literary_card_present": literary_card_present,
        "book_link_present": book_link_present,
        "raw_repo_path_hits": raw_repo_path_hits,
    }


class SiteReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attr_map = dict(attrs)
        for key in ("href", "src"):
            value = attr_map.get(key)
            if value:
                self.references.append((tag, key, value))


def analyze_site_tree(site_root: Path) -> dict:
    html_files = sorted(site_root.rglob("*.html"))
    missing_local_targets: list[dict[str, str]] = []
    forbidden_artifacts: list[str] = []
    checked_reference_count = 0
    for path in site_root.rglob("*"):
        relative = path.relative_to(site_root)
        parts = set(relative.parts)
        if parts & FORBIDDEN_SITE_SEGMENTS:
            forbidden_artifacts.append(str(relative))
    for html_path in html_files:
        parser = SiteReferenceParser()
        parser.feed(html_path.read_text(encoding="utf-8"))
        for tag, attr, reference in parser.references:
            if reference.startswith(("http://", "https://", "mailto:", "#", "javascript:", "data:")):
                continue
            normalized_reference = reference.split("#", 1)[0].split("?", 1)[0]
            if not normalized_reference:
                continue
            checked_reference_count += 1
            target = (html_path.parent / normalized_reference).resolve()
            if not target.exists():
                missing_local_targets.append(
                    {
                        "document": str(html_path.relative_to(site_root)),
                        "tag": tag,
                        "attribute": attr,
                        "reference": reference,
                    }
                )
    status = "pass"
    if missing_local_targets or forbidden_artifacts:
        status = "fail"
    return {
        "status": status,
        "html_file_count": len(html_files),
        "checked_reference_count": checked_reference_count,
        "missing_local_targets": missing_local_targets[:50],
        "missing_local_target_count": len(missing_local_targets),
        "forbidden_artifacts": forbidden_artifacts[:100],
        "forbidden_artifact_count": len(forbidden_artifacts),
    }


def analyze_website_bundle(website_root: Path) -> dict:
    index_path = website_root / "index.html"
    chapters_path = website_root / "data" / "chapters.json"
    errors: list[str] = []
    broken_images: list[str] = []
    chapter_shape_issues: list[str] = []
    chapter_count = 0
    block_count = 0
    chapters: list[dict] = []

    if not index_path.exists():
        errors.append("Missing website/index.html")
    if not chapters_path.exists():
        errors.append("Missing website/data/chapters.json")
    else:
        try:
            parsed = json.loads(chapters_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid website/data/chapters.json: {exc}")
        else:
            if not isinstance(parsed, list):
                errors.append("website/data/chapters.json is not an array")
            else:
                chapters = parsed

    for chapter_index, chapter in enumerate(chapters):
        if not isinstance(chapter, dict):
            chapter_shape_issues.append(f"Chapter {chapter_index} is not an object")
            continue
        title = chapter.get("title")
        blocks = chapter.get("blocks")
        if not isinstance(title, str) or not title.strip():
            chapter_shape_issues.append(f"Chapter {chapter_index} is missing a title")
        if not isinstance(blocks, list) or not blocks:
            chapter_shape_issues.append(f"Chapter {chapter_index} has no blocks")
            continue
        chapter_count += 1
        for block_index, block in enumerate(blocks):
            if not isinstance(block, dict):
                chapter_shape_issues.append(f"Chapter {chapter_index} block {block_index} is not an object")
                continue
            if not isinstance(block.get("text"), str) or not block["text"].strip():
                chapter_shape_issues.append(f"Chapter {chapter_index} block {block_index} is missing text")
            image = block.get("image")
            if not isinstance(image, str) or not image.strip():
                chapter_shape_issues.append(f"Chapter {chapter_index} block {block_index} is missing image")
            elif not (website_root / image).resolve().exists():
                broken_images.append(f"Chapter {chapter_index} block {block_index} -> {image}")
            block_count += 1

    errors.extend(chapter_shape_issues[:20])
    errors.extend(broken_images[:20])
    status = "pass"
    if errors:
        status = "fail"
    return {
        "status": status,
        "index_present": index_path.exists(),
        "chapters_json_present": chapters_path.exists(),
        "chapter_count": chapter_count,
        "block_count": block_count,
        "chapter_shape_issue_count": len(chapter_shape_issues),
        "broken_image_count": len(broken_images),
        "errors": errors,
    }


def review_publication(root: Path) -> dict:
    papers_root = root / "papers"
    paper_pdf_root = root / "build" / "papers" / "pdf"
    book_root = root / "book"
    book_pdf_root = root / "build" / "book" / "pdf"
    volumes_root = root / "volumes"
    volume_pdf_root = root / "build" / "volumes" / "pdf"

    paper_results = []
    for markdown_path in sorted(papers_root.glob("*.md")):
        pdf_path = paper_pdf_root / markdown_path.stem / f"{markdown_path.stem}.pdf"
        paper_results.append(analyze_markdown_pdf_pair(markdown_path, pdf_path, PAPER_REQUIRED_HEADINGS))

    volume_results = [
        analyze_volume(
            volumes_root / "dossier_omnibus.md",
            volume_pdf_root / "dossier_omnibus" / "dossier_omnibus.pdf",
            OMNIBUS_REQUIRED_HEADINGS,
        ),
        analyze_volume(
            volumes_root / "corpus_companion.md",
            volume_pdf_root / "corpus_companion" / "corpus_companion.pdf",
            COMPANION_REQUIRED_HEADINGS,
            expected_counts={"127 sources": 127, "475 claims": 475, "62 entities": 62, "90 events": 90, "141 notes": 141},
            expect_bibliography=False,
        ),
    ]

    book_results = []
    full_book_path = book_root / "full_book.md"
    if full_book_path.exists():
        full_book_pdf = book_pdf_root / "full_book" / "full_book.pdf"
        book_results.append(
            analyze_markdown_pdf_pair(
                full_book_path,
                full_book_pdf,
                FULL_BOOK_REQUIRED_HEADINGS,
                expect_bibliography=False,
                require_external_links=False,
            )
        )
    for markdown_path in sorted((book_root / "chapters").glob("*.md")):
        stem = markdown_path.stem
        pdf_path = book_pdf_root / stem / f"{stem}.pdf"
        book_results.append(
            analyze_markdown_pdf_pair(
                markdown_path,
                pdf_path,
                BOOK_REQUIRED_HEADINGS,
                expect_bibliography=False,
                require_external_links=False,
            )
        )

    site_index_path = root / "build" / "site" / "index.html"
    site_result = analyze_site_index(site_index_path) if site_index_path.exists() else {"status": "fail", "literary_card_present": False, "book_link_present": False, "raw_repo_path_hits": 0}
    site_tree_result = analyze_site_tree(root / "build" / "site") if (root / "build" / "site").exists() else {"status": "fail", "html_file_count": 0, "checked_reference_count": 0, "missing_local_targets": [], "missing_local_target_count": 0}
    website_root = root / "build" / "site" / "website"
    website_result = analyze_website_bundle(website_root) if website_root.exists() else {"status": "fail", "index_present": False, "chapters_json_present": False, "chapter_count": 0, "block_count": 0, "chapter_shape_issue_count": 0, "broken_image_count": 0, "errors": ["Missing build/site/website/"]}

    results = {
        "papers": paper_results,
        "volumes": volume_results,
        "books": book_results,
        "site": site_result,
        "site_tree": site_tree_result,
        "website": website_result,
    }

    reviews_root = root / "build" / "reviews"
    ensure_dir(reviews_root)
    dump_json(reviews_root / "publication_qc.json", results)
    overwrite(reviews_root / "publication_qc.md", render_report(results))
    return results
