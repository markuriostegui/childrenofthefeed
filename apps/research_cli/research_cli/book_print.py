from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from .book import (
    BOOK_AUTHOR,
    BOOK_COPYRIGHT,
    BOOK_PUBLISHER,
    BOOK_PRINT_ADAPTATION_LINE,
    BOOK_SUBTITLE,
    BOOK_TITLE,
    BOOK_CHAPTERS,
    DEDICATION_HEADING,
    DEDICATION_INTRO,
    DEDICATION_LINES,
    chapter_markdown_path,
    chapter_output_stem,
    parse_frontmatter,
    strip_frontmatter,
)
from .doctrine import (
    PATRIMONY_BRIDGE_SENTENCE,
    PATRIMONY_PRINT_FOUNDATION_LINE,
    PATRIMONY_PRINCIPLES,
    PATRIMONY_SLOGAN,
)
from .fs import dump_json, ensure_dir, overwrite, write_if_missing
from .papers import paper_stem_for_chapter

PRINT_FORMAT_ID = "trade-6x9"
PRINT_PAGE_WIDTH_IN = 6.0
PRINT_PAGE_HEIGHT_IN = 9.0
PRINT_MAX_IMAGE_WIDTH_PX = 1500
PRINT_MAX_IMAGE_HEIGHT_PX = 2250
PUBLICATION_BASE_URL = "https://markuriostegui.github.io/childrenofthefeed/"
FULL_BOOK_TARGET_PAGE_MIN = 96
FULL_BOOK_TARGET_PAGE_MAX = 104
MAIN_NARRATIVE_PAGEBREAK_CHAPTERS = {"00", "04", "07", "10"}
INFOGRAPHIC_PLATE_CHAPTERS = {"07"}

PRINT_ROOT = Path("book") / "print"
PRINT_MANUSCRIPTS_ROOT = PRINT_ROOT / "manuscripts"
PRINT_CHAPTER_MANUSCRIPTS_ROOT = PRINT_MANUSCRIPTS_ROOT / "chapters"
PRINT_ASSETS_ROOT = PRINT_ROOT / "assets"
PRINT_QR_ROOT = PRINT_ASSETS_ROOT / "qrcodes"
PRINT_IMAGE_ROOT = PRINT_ASSETS_ROOT / "images"
PRINT_TYPST_ROOT = PRINT_ROOT / "typst"
PRINT_FONT_ROOT = PRINT_ROOT / "fonts"

PRINT_FONT_FILES = {
    "Source Serif 4 Regular": "SourceSerif4.ttf",
    "Source Serif 4 Italic": "SourceSerif4-Italic.ttf",
    "Source Sans 3 Regular": "SourceSans3.ttf",
    "Source Sans 3 Italic": "SourceSans3-Italic.ttf",
    "Oswald Regular": "Oswald.ttf",
}

FULL_BOOK_PDF_NAME = "full_book.pdf"
PRINT_TEMPLATE_IMPORT = "../../../apps/templates/book_print_template.typ"


@dataclass
class ChapterPrintRecord:
    chapter_id: str
    title: str
    deck: str
    document_stem: str
    paper_title: str
    paper_stem: str
    public_html_url: str
    public_pdf_url: str
    chapter_markdown_path: Path
    manuscript_markdown_path: Path
    manuscript_typst_path: Path
    qr_svg_path: Path
    cover_image_path: Path
    body_image_paths: list[Path]
    research_note_summary: str


def ensure_print_fonts(root: Path) -> dict[str, Path]:
    font_paths = {label: root / PRINT_FONT_ROOT / file_name for label, file_name in PRINT_FONT_FILES.items()}
    missing = [label for label, path in font_paths.items() if not path.exists()]
    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(
            f"Missing vendored print fonts: {missing_list}. "
            "Place the expected font files under book/print/fonts before building the print pipeline."
        )
    return font_paths


def load_publication_config(root: Path) -> dict[str, Any]:
    config_path = root / PRINT_ROOT / "publication_config.json"
    if not config_path.exists():
        config = {
            "base_url": PUBLICATION_BASE_URL,
            "print_format": PRINT_FORMAT_ID,
            "page_size": {"width_in": PRINT_PAGE_WIDTH_IN, "height_in": PRINT_PAGE_HEIGHT_IN},
            "fonts": {
                "body": "Source Serif 4",
                "display": "Oswald",
                "sans": "Source Sans 3",
            },
        }
        dump_json(config_path, config)
        return config
    return json.loads(config_path.read_text(encoding="utf-8"))


def sanitize_markdown_links(text: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text).strip()


def strip_markdown_images(text: str) -> str:
    return re.sub(r"!\[[^\]]*]\([^)]+\)", "", text).strip()


def sanitize_research_basis_text(text: str) -> str:
    text = sanitize_markdown_links(text)
    text = strip_markdown_images(text)
    text = re.sub(r"\bThe PDF version is here\.\s*", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def extract_section(content: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\n\n(.*?)(?=^## |\Z)", flags=re.M | re.S)
    match = pattern.search(content)
    return match.group(1).strip() if match else ""


def remove_section(content: str, heading: str) -> str:
    pattern = re.compile(rf"^## {re.escape(heading)}\n\n.*?(?=^## |\Z)", flags=re.M | re.S)
    return pattern.sub("", content)


def remove_first_heading(content: str) -> str:
    return re.sub(r"^# .+\n\n", "", content, count=1, flags=re.M)


def normalize_markdown_spacing(content: str) -> str:
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip() + "\n"


def display_url(url: str) -> str:
    return re.sub(r"^https?://", "", url).rstrip("/")


def extract_image_paths(content: str) -> list[str]:
    return re.findall(r"!\[[^\]]*]\(([^)]+)\)", content)


def classify_image(path: str) -> str:
    if "covers/" in path:
        return "cover"
    if "infographics/" in path:
        return "infographic"
    if "illustrations/" in path:
        return "illustration"
    return "other"


def select_print_visuals(image_paths: list[str]) -> tuple[str | None, list[str]]:
    cover = next((path for path in image_paths if classify_image(path) == "cover"), None)
    first_illustration = next((path for path in image_paths if classify_image(path) == "illustration"), None)
    last_infographic = next((path for path in reversed(image_paths) if classify_image(path) == "infographic"), None)
    selected = []
    if first_illustration:
        selected.append(first_illustration)
    if last_infographic and last_infographic not in selected:
        selected.append(last_infographic)
    return cover, selected


def resolve_markdown_asset_path(markdown_path: Path, rel_path: str) -> Path:
    return (markdown_path.parent / rel_path).resolve()


def render_print_image(root: Path, chapter_id: str, source_path: Path, role: str) -> Path:
    ensure_dir(root / PRINT_IMAGE_ROOT)
    suffix = source_path.suffix.lower()
    image = Image.open(source_path)
    image.thumbnail((PRINT_MAX_IMAGE_WIDTH_PX, PRINT_MAX_IMAGE_HEIGHT_PX), Image.Resampling.LANCZOS)

    base_name = f"{chapter_id}_{role}"
    if role == "infographic":
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")
        target_path = root / PRINT_IMAGE_ROOT / f"{base_name}.png"
        image.save(target_path, format="PNG", optimize=True)
        return target_path

    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, "#f8f5ee")
        background.paste(image, mask=image.getchannel("A"))
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    target_path = root / PRINT_IMAGE_ROOT / f"{base_name}.jpg"
    image.save(target_path, format="JPEG", quality=82, optimize=True, progressive=True)
    return target_path


def generate_qr_svg_local(url: str, output_path: Path) -> None:
    from reportlab.graphics import renderSVG
    from reportlab.graphics.barcode import qr
    from reportlab.graphics.shapes import Drawing

    widget = qr.QrCodeWidget(url)
    bounds = widget.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(144, 144, transform=[144 / width, 0, 0, 144 / height, 0, 0])
    drawing.add(widget)
    renderSVG.drawToFile(drawing, str(output_path))


def generate_qr_svg(root: Path, url: str, output_path: Path) -> None:
    ensure_dir(output_path.parent)
    try:
        generate_qr_svg_local(url, output_path)
        return
    except Exception:
        bundled_python = (
            Path.home()
            / ".cache"
            / "codex-runtimes"
            / "codex-primary-runtime"
            / "dependencies"
            / "python"
            / "bin"
            / "python3"
        )
        if not bundled_python.exists():
            raise
        script = textwrap.dedent(
            """
            from pathlib import Path
            from reportlab.graphics import renderSVG
            from reportlab.graphics.barcode import qr
            from reportlab.graphics.shapes import Drawing
            import sys

            url = sys.argv[1]
            target = Path(sys.argv[2])
            widget = qr.QrCodeWidget(url)
            bounds = widget.getBounds()
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            drawing = Drawing(144, 144, transform=[144 / width, 0, 0, 144 / height, 0, 0])
            drawing.add(widget)
            renderSVG.drawToFile(drawing, str(target))
            """
        ).strip()
        subprocess.run([str(bundled_python), "-c", script, url, str(output_path)], check=True)


def write_markdown_document(path: Path, title: str, body: str, metadata: dict[str, str] | None = None) -> None:
    frontmatter_lines = ["---", f'title: "{title}"']
    for key, value in (metadata or {}).items():
        frontmatter_lines.append(f'{key}: "{value}"')
    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines) + "\n\n"
    overwrite(path, frontmatter + body.strip() + "\n")


def rel_from(path: Path, target: Path) -> str:
    return os.path.relpath(target, path.parent)


def public_urls_for_chapter(root: Path, chapter_id: str) -> tuple[str, str]:
    config = load_publication_config(root)
    base_url = str(config.get("base_url", PUBLICATION_BASE_URL)).rstrip("/") + "/"
    paper_stem = paper_stem_for_chapter(root, chapter_id)
    return (
        f"{base_url}papers/html/{paper_stem}.html",
        f"{base_url}papers/pdf/{paper_stem}/{paper_stem}.pdf",
    )


def build_chapter_manuscript(root: Path, chapter_id: str) -> ChapterPrintRecord:
    source_path = chapter_markdown_path(root, chapter_id)
    frontmatter = parse_frontmatter(source_path.read_text(encoding="utf-8"))
    raw_body = strip_frontmatter(source_path.read_text(encoding="utf-8"))

    title = frontmatter.get("title") or next(ch["title"] for ch in BOOK_CHAPTERS if ch["id"] == chapter_id)
    document_stem = source_path.stem
    paper_title = frontmatter.get("paper_title") or f"Chapter {chapter_id}"
    paper_stem = frontmatter.get("paper_stem") or paper_stem_for_chapter(root, chapter_id)
    deck = strip_markdown_images(extract_section(raw_body, "Deck"))
    deck = normalize_markdown_spacing(deck).replace("\n", " ").strip()
    research_basis_text = sanitize_research_basis_text(extract_section(raw_body, "Research Basis"))
    if not research_basis_text:
        research_basis_text = (
            "This chapter has a full research counterpart with the documentary basis, citations, and supporting links."
        )

    cover_rel, retained_body_rel = select_print_visuals(extract_image_paths(raw_body))
    if not cover_rel:
        raise RuntimeError(f"No cover image found for chapter {chapter_id}")

    source_cover_path = resolve_markdown_asset_path(source_path, cover_rel)
    print_cover_path = render_print_image(root, chapter_output_stem(chapter_id), source_cover_path, "cover")

    body_print_paths: dict[str, Path] = {}
    for rel_path in retained_body_rel:
        role = classify_image(rel_path)
        body_print_paths[rel_path] = render_print_image(
            root,
            chapter_output_stem(chapter_id),
            resolve_markdown_asset_path(source_path, rel_path),
            role,
        )

    public_html_url, public_pdf_url = public_urls_for_chapter(root, chapter_id)
    qr_svg_path = root / PRINT_QR_ROOT / f"{document_stem}_research_qr.svg"
    generate_qr_svg(root, public_html_url, qr_svg_path)

    transformed = raw_body
    transformed = remove_first_heading(transformed)
    transformed = remove_section(transformed, "Deck")
    transformed = remove_section(transformed, "Research Basis")
    transformed = remove_section(transformed, "Next")

    image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

    def replace_image(match: re.Match[str]) -> str:
        rel_path = match.group(2)
        if rel_path == cover_rel:
            return ""
        print_path = body_print_paths.get(rel_path)
        if print_path is None:
            return ""
        rel_print_path = os.path.relpath(print_path, PRINT_CHAPTER_MANUSCRIPTS_ROOT)
        role = "infographic" if "infographic" in rel_path else "illustration"
        width = "100%" if role == "infographic" else "92%"
        image_markdown = f"![]({rel_print_path}){{ width={width} }}"
        if chapter_id in INFOGRAPHIC_PLATE_CHAPTERS and role == "infographic":
            return "```{=typst}\n#pagebreak()\n```\n\n" + image_markdown
        return image_markdown

    transformed = image_pattern.sub(replace_image, transformed)
    if chapter_id in MAIN_NARRATIVE_PAGEBREAK_CHAPTERS:
        transformed = transformed.replace(
            "## Main Narrative",
            "```{=typst}\n#pagebreak()\n```\n\n## Main Narrative",
            1,
        )
    transformed = normalize_markdown_spacing(transformed)

    qr_rel = os.path.relpath(qr_svg_path, PRINT_CHAPTER_MANUSCRIPTS_ROOT)
    html_display = display_url(public_html_url)
    chapter_note = textwrap.dedent(
        f"""
        ## Research Notes

        {research_basis_text}

        Scan this QR code to open the live research paper with the full documentary basis, citations, and supporting links.

        ![]({qr_rel}){{ width=34% }}

        Fallback URL: [{html_display}]({public_html_url})
        """
    ).strip()

    chapter_body = normalize_markdown_spacing(transformed + "\n\n" + chapter_note)
    manuscript_markdown_path = root / PRINT_CHAPTER_MANUSCRIPTS_ROOT / f"{document_stem}.md"
    manuscript_typst_path = root / PRINT_CHAPTER_MANUSCRIPTS_ROOT / f"{document_stem}.typ"
    write_markdown_document(
        manuscript_markdown_path,
        title=title,
        body=chapter_body,
        metadata={
            "chapter_id": chapter_id,
            "paper_title": paper_title,
            "paper_stem": paper_stem,
            "public_html_url": public_html_url,
            "public_pdf_url": public_pdf_url,
            "deck": deck,
        },
    )

    return ChapterPrintRecord(
        chapter_id=chapter_id,
        title=title,
        deck=deck,
        document_stem=document_stem,
        paper_title=paper_title,
        paper_stem=paper_stem,
        public_html_url=public_html_url,
        public_pdf_url=public_pdf_url,
        chapter_markdown_path=source_path,
        manuscript_markdown_path=manuscript_markdown_path,
        manuscript_typst_path=manuscript_typst_path,
        qr_svg_path=qr_svg_path,
        cover_image_path=print_cover_path,
        body_image_paths=list(body_print_paths.values()),
        research_note_summary=research_basis_text,
    )


def build_full_book_print_manuscript(root: Path, chapters: list[ChapterPrintRecord]) -> Path:
    parts = [
        "# Full Book Print Spine",
        "",
        "The dedicated print front matter is composed in Typst and is not stored in this manuscript file.",
        "",
    ]
    for chapter in chapters:
        chapter_text = strip_frontmatter(chapter.manuscript_markdown_path.read_text(encoding="utf-8")).strip()
        parts.extend(
            [
                f"# {chapter.title}",
                "",
                chapter_text,
                "",
            ]
        )

    full_book_path = root / PRINT_MANUSCRIPTS_ROOT / "full_book_print.md"
    write_markdown_document(
        full_book_path,
        title=BOOK_TITLE,
        body="\n".join(parts).strip() + "\n",
        metadata={"subtitle": BOOK_SUBTITLE, "author": BOOK_AUTHOR},
    )
    return full_book_path


def convert_markdown_to_typst(markdown_path: Path, output_path: Path) -> None:
    subprocess.run(
        [
            "pandoc",
            "--from",
            "markdown+footnotes",
            "--to",
            "typst",
            str(markdown_path),
            "-o",
            str(output_path),
        ],
        check=True,
    )
    content = output_path.read_text(encoding="utf-8")
    content = post_process_typst_content(content)
    overwrite(output_path, content)


def post_process_typst_content(content: str) -> str:
    generic_figure_pattern = re.compile(
        r'#figure\((image\([^)]+(?:\)[^)]*)?\)),\s*caption:\s*\[\s*(Chapter\s+\d+\s+(?:narrative illustration [A-Z]|infographic)|QR code to the live research paper)\s*\]\s*\)',
        flags=re.S,
    )
    content = generic_figure_pattern.sub(r"#figure(\1)", content)
    content = re.sub(r"#box\((image\([^)]+\))\)", r"#figure(\1)", content)
    content = re.sub(r"(?m)^== Research Notes\b", "#pagebreak()\n\n== Research Notes", content)
    return content


def escape_typst_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def write_typst_wrappers(root: Path, chapters: list[ChapterPrintRecord]) -> tuple[Path, list[Path]]:
    ensure_dir(root / PRINT_TYPST_ROOT)
    chapter_wrapper_paths: list[Path] = []
    full_wrapper_path = root / PRINT_TYPST_ROOT / "full_book_print.typ"

    for chapter in chapters:
        convert_markdown_to_typst(chapter.manuscript_markdown_path, chapter.manuscript_typst_path)
        wrapper_path = root / PRINT_TYPST_ROOT / f"{chapter.document_stem}_print.typ"
        cover_rel = rel_from(wrapper_path, chapter.cover_image_path)
        wrapper = textwrap.dedent(
            f"""
            #import "{PRINT_TEMPLATE_IMPORT}": *
            #let chapter_meta = (
              id: "{chapter.chapter_id}",
              title: "{escape_typst_string(chapter.title)}",
              deck: "{escape_typst_string(chapter.deck)}",
              cover: image("{cover_rel}", width: 100%, height: 2.7in, fit: "cover"),
              running: "{escape_typst_string(chapter.title)}",
            )

            #set document(title: "{escape_typst_string(chapter.title)}", author: "{escape_typst_string(BOOK_AUTHOR)}")
            #set page(
              width: 6in,
              height: 9in,
              fill: page-paper,
              header: context print-header(chapter_meta.running, visible-from: 5),
              footer: context print-footer(visible-from: 5),
            )
            #chapter-cover-page(chapter_meta)
            #chapter-imprint-page(
              book-title: "{escape_typst_string(BOOK_TITLE)}",
              chapter-label: "Chapter {chapter.chapter_id}",
              chapter-title: "{escape_typst_string(chapter.title)}",
              author: "{escape_typst_string(BOOK_AUTHOR)}",
              publisher: "{escape_typst_string(f"Published by {BOOK_PUBLISHER}.")}",
              copyright: "{escape_typst_string(BOOK_COPYRIGHT)}",
            )
            #dedication-page(
              heading: "{escape_typst_string(DEDICATION_HEADING)}",
              intro: "{escape_typst_string(DEDICATION_INTRO)}",
              lines: (
                {", ".join(f'"{escape_typst_string(line)}"' for line in DEDICATION_LINES)}
              ),
              doctrine: "{escape_typst_string(PATRIMONY_SLOGAN)}",
              doctrine-lines: (
                {", ".join(f'"{escape_typst_string(line)}"' for line in PATRIMONY_PRINCIPLES)}
              ),
              bridge-line: "{escape_typst_string(PATRIMONY_BRIDGE_SENTENCE)}",
              foundation-line: "{escape_typst_string(PATRIMONY_PRINT_FOUNDATION_LINE)}",
            )
            #toc-page(title: "Contents", target: heading.where(level: 2))
            #include "../manuscripts/chapters/{chapter.document_stem}.typ"
            """
        ).strip() + "\n"
        overwrite(wrapper_path, wrapper)
        chapter_wrapper_paths.append(wrapper_path)

    chapter_blocks = []
    for index, chapter in enumerate(chapters):
        cover_rel = rel_from(full_wrapper_path, chapter.cover_image_path)
        trailing_break = "#pagebreak()" if index < len(chapters) - 1 else ""
        chapter_blocks.append(
            textwrap.dedent(
                f"""
                = {escape_typst_string(chapter.title)}
                #let chapter_meta_{chapter.chapter_id} = (
                  id: "{chapter.chapter_id}",
                  title: "{escape_typst_string(chapter.title)}",
                  deck: "{escape_typst_string(chapter.deck)}",
                  cover: image("{cover_rel}", width: 100%, height: 2.7in, fit: "cover"),
                  running: "{escape_typst_string(chapter.title)}",
                )
                #chapter-cover-page(chapter_meta_{chapter.chapter_id})
                #include "../manuscripts/chapters/{chapter.document_stem}.typ"
                {trailing_break}
                """
            ).strip()
        )

    master_cover_rel = rel_from(full_wrapper_path, root / PRINT_IMAGE_ROOT / "book_master_cover.jpg")
    dedication_lines = ", ".join(f'"{escape_typst_string(line)}"' for line in DEDICATION_LINES)
    full_wrapper = textwrap.dedent(
        f"""
        #import "{PRINT_TEMPLATE_IMPORT}": *
        #set document(title: "{escape_typst_string(BOOK_TITLE)}", author: "{escape_typst_string(BOOK_AUTHOR)}")
        #set page(
          width: 6in,
          height: 9in,
          fill: page-paper,
          header: context print-header("{escape_typst_string(BOOK_TITLE)}", visible-from: 5),
          footer: context print-footer(visible-from: 5),
        )
        #full-bleed-cover(image("{master_cover_rel}", width: 100%, height: 100%, fit: "cover"))
        #book-imprint-page(
          title-line-1: "Children of the Feed. Servants",
          title-line-2: "of the AI God",
          subtitle: "{escape_typst_string(BOOK_SUBTITLE)}",
          author: "{escape_typst_string(BOOK_AUTHOR)}",
          adaptation-line: "{escape_typst_string(BOOK_PRINT_ADAPTATION_LINE)}",
          publisher: "{escape_typst_string(f"Published by {BOOK_PUBLISHER}.")}",
          copyright: "{escape_typst_string(BOOK_COPYRIGHT)}",
        )
        #dedication-page(
          heading: "{escape_typst_string(DEDICATION_HEADING)}",
          intro: "{escape_typst_string(DEDICATION_INTRO)}",
          lines: (
            {dedication_lines}
          ),
          doctrine: "{escape_typst_string(PATRIMONY_SLOGAN)}",
          doctrine-lines: (
            {", ".join(f'"{escape_typst_string(line)}"' for line in PATRIMONY_PRINCIPLES)}
          ),
          bridge-line: "{escape_typst_string(PATRIMONY_BRIDGE_SENTENCE)}",
          foundation-line: "{escape_typst_string(PATRIMONY_PRINT_FOUNDATION_LINE)}",
        )
        #toc-page(title: "Contents", target: heading.where(level: 1))
        {"\n\n".join(chapter_blocks)}
        """
    ).strip() + "\n"
    overwrite(full_wrapper_path, full_wrapper)
    return full_wrapper_path, chapter_wrapper_paths


def ensure_master_cover_print_asset(root: Path) -> Path:
    source_cover = root / "book" / "assets" / "generated" / "master_cover.png"
    return render_print_image(root, "book_master", source_cover, "cover")


def build_book_print(root: Path) -> None:
    ensure_print_fonts(root)
    ensure_dir(root / PRINT_CHAPTER_MANUSCRIPTS_ROOT)
    ensure_dir(root / PRINT_QR_ROOT)
    ensure_dir(root / PRINT_IMAGE_ROOT)
    ensure_dir(root / PRINT_TYPST_ROOT)

    load_publication_config(root)
    master_cover = ensure_master_cover_print_asset(root)

    chapter_records = [build_chapter_manuscript(root, chapter["id"]) for chapter in BOOK_CHAPTERS]
    full_book_manuscript_path = build_full_book_print_manuscript(root, chapter_records)
    full_wrapper_path, chapter_wrapper_paths = write_typst_wrappers(root, chapter_records)

    metadata = {
        "base_url": load_publication_config(root).get("base_url", PUBLICATION_BASE_URL),
        "print_format": PRINT_FORMAT_ID,
        "master_cover": master_cover.as_posix(),
        "full_book_manuscript": full_book_manuscript_path.as_posix(),
        "full_book_wrapper": full_wrapper_path.as_posix(),
        "chapters": [
            {
                "chapter_id": chapter.chapter_id,
                "title": chapter.title,
                "deck": chapter.deck,
                "document_stem": chapter.document_stem,
                "paper_title": chapter.paper_title,
                "paper_stem": chapter.paper_stem,
                "public_html_url": chapter.public_html_url,
                "public_pdf_url": chapter.public_pdf_url,
                "manuscript_markdown_path": chapter.manuscript_markdown_path.as_posix(),
                "manuscript_typst_path": chapter.manuscript_typst_path.as_posix(),
                "wrapper_path": wrapper.as_posix(),
                "qr_svg_path": chapter.qr_svg_path.as_posix(),
                "cover_image_path": chapter.cover_image_path.as_posix(),
                "body_image_paths": [path.as_posix() for path in chapter.body_image_paths],
                "research_note_summary": chapter.research_note_summary,
            }
            for chapter, wrapper in zip(chapter_records, chapter_wrapper_paths, strict=True)
        ],
    }
    dump_json(root / PRINT_ROOT / "metadata.json", metadata)
    dump_json(
        root / PRINT_ROOT / "qr_manifest.json",
        {
            "base_url": load_publication_config(root).get("base_url", PUBLICATION_BASE_URL),
            "entries": [
                {
                    "chapter_id": chapter.chapter_id,
                    "document_stem": chapter.document_stem,
                    "public_html_url": chapter.public_html_url,
                    "public_pdf_url": chapter.public_pdf_url,
                    "qr_svg_path": chapter.qr_svg_path.as_posix(),
                }
                for chapter in chapter_records
            ],
        },
    )
    write_if_missing(
        root / PRINT_ROOT / "README.md",
        "# Print Layer\n\nThis directory contains the dedicated source layer for the 6x9 trade-book PDF pipeline.\n",
    )


def typst_font_path_arg(root: Path) -> str:
    return str(root / PRINT_FONT_ROOT)


def export_book_print(root: Path) -> None:
    if shutil.which("typst") is None:
        raise RuntimeError("Typst is required for export-book-print but is not installed")

    build_book_print(root)
    build_pdf_root = root / "build" / "book" / "pdf"
    ensure_dir(build_pdf_root)

    metadata = json.loads((root / PRINT_ROOT / "metadata.json").read_text(encoding="utf-8"))
    full_wrapper_path = Path(metadata["full_book_wrapper"])
    chapter_entries = metadata["chapters"]
    ensure_dir(build_pdf_root / "full_book")

    subprocess.run(
        [
            "typst",
            "compile",
            "--root",
            str(root),
            "--font-path",
            typst_font_path_arg(root),
            str(full_wrapper_path),
            str(build_pdf_root / "full_book" / FULL_BOOK_PDF_NAME),
        ],
        check=True,
    )

    for chapter in chapter_entries:
        chapter_id = chapter["chapter_id"]
        document_stem = chapter["document_stem"]
        output_name = f"{document_stem}.pdf"
        ensure_dir(build_pdf_root / document_stem)
        subprocess.run(
            [
                "typst",
                "compile",
                "--root",
                str(root),
                "--font-path",
                typst_font_path_arg(root),
                chapter["wrapper_path"],
                str(build_pdf_root / document_stem / output_name),
            ],
            check=True,
        )

def review_book_print(root: Path) -> None:
    try:
        import pypdf  # type: ignore
    except ImportError:
        import sys

        runtime_roots = sorted(
            Path.home().glob(".cache/codex-runtimes/*/dependencies/python/lib/python*/site-packages")
        )
        for candidate in runtime_roots:
            if (candidate / "pypdf").exists():
                sys.path.append(str(candidate))
                import pypdf  # type: ignore

                break
        else:
            raise RuntimeError(
                "pypdf is required for review-book-print. Install it locally or use a Codex bundled runtime."
            )

    metadata = json.loads((root / PRINT_ROOT / "metadata.json").read_text(encoding="utf-8"))
    pdf_root = root / "build" / "book" / "pdf"

    failures: list[str] = []
    full_book_pdf = pdf_root / "full_book" / FULL_BOOK_PDF_NAME
    if not full_book_pdf.exists():
        failures.append("Missing full book print PDF")
    else:
        full_reader = pypdf.PdfReader(str(full_book_pdf))
        width = float(full_reader.pages[0].mediabox.width)
        height = float(full_reader.pages[0].mediabox.height)
        if round(width) != 432 or round(height) != 648:
            failures.append(f"Full book PDF is not 6x9: {width}x{height}")
        page_count = len(full_reader.pages)
        if page_count < FULL_BOOK_TARGET_PAGE_MIN or page_count > FULL_BOOK_TARGET_PAGE_MAX:
            failures.append(
                f"Full book PDF page count {page_count} is outside the target range "
                f"{FULL_BOOK_TARGET_PAGE_MIN}-{FULL_BOOK_TARGET_PAGE_MAX}"
            )

    qr_manifest = json.loads((root / PRINT_ROOT / "qr_manifest.json").read_text(encoding="utf-8"))
    if len(qr_manifest.get("entries", [])) != len(BOOK_CHAPTERS):
        failures.append("QR manifest does not cover all chapters")
    expected_base = str(load_publication_config(root).get("base_url", PUBLICATION_BASE_URL)).rstrip("/") + "/"
    for entry in qr_manifest.get("entries", []):
        target = str(entry.get("public_html_url", ""))
        if not target.startswith(expected_base) or "hassanvfx.github.io/ai-empire" in target:
            failures.append(f"QR manifest has an invalid publication URL: {target}")

    for chapter in metadata["chapters"]:
        chapter_id = chapter["chapter_id"]
        document_stem = chapter["document_stem"]
        pdf_path = pdf_root / document_stem / f"{document_stem}.pdf"
        if not pdf_path.exists():
            failures.append(f"Missing chapter print PDF for {chapter_id}")
            continue
        reader = pypdf.PdfReader(str(pdf_path))
        width = float(reader.pages[0].mediabox.width)
        height = float(reader.pages[0].mediabox.height)
        if round(width) != 432 or round(height) != 648:
            failures.append(f"Chapter {chapter_id} PDF is not 6x9: {width}x{height}")
        qr_path = Path(chapter["qr_svg_path"])
        if not qr_path.exists():
            failures.append(f"Missing QR asset for chapter {chapter_id}")
        if not chapter["public_html_url"].startswith(expected_base):
            failures.append(f"Chapter {chapter_id} QR target does not use the GH Pages base URL")

    if full_book_pdf.exists():
        full_text = "\n".join(page.extract_text() or "" for page in pypdf.PdfReader(str(full_book_pdf)).pages)
        if "hassanvfx.github.io/ai-empire" in full_text:
            failures.append("Full book PDF contains the retired publication URL")
        if full_text.count("Research Notes") != len(BOOK_CHAPTERS):
            failures.append("Full book PDF is missing one or more chapter research-note sections")
        if full_text.count("CHAPTER") != len(BOOK_CHAPTERS):
            failures.append("Full book PDF is missing one or more chapter opening pages")

    if failures:
        raise RuntimeError("Book print review failed:\n" + "\n".join(failures))
