"""Isolated, deterministic export for the Spanish literary full-book PDF.

The Spanish manuscript is authored under ``esp/book``. This module never calls
a translation service and never writes to English book or print source trees.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .book import BOOK_CHAPTERS, strip_frontmatter
from .book_print import (
    INFOGRAPHIC_PLATE_CHAPTERS,
    MAIN_NARRATIVE_PAGEBREAK_CHAPTERS,
    classify_image,
    display_url,
    extract_image_paths,
    extract_section,
    generate_qr_svg,
    normalize_markdown_spacing,
    public_urls_for_chapter,
    remove_first_heading,
    remove_section,
    sanitize_research_basis_text,
    select_print_visuals,
    strip_markdown_images,
)
from .fs import ensure_dir, overwrite

LOCALE = "es-419"
BYLINE = "Mark Uriostegui & Paul Lara"
SPANISH_ROOT = Path("esp")
SOURCE_ROOT = SPANISH_ROOT / "book"
BUILD_ROOT = Path("build") / "esp"
PUBLIC_ROOT = Path("build") / "site" / "esp"
REVIEW_MANIFEST = SPANISH_ROOT / "review.json"
PDF_RELATIVE_PATH = Path("book") / "pdf" / "full_book.pdf"
COVER_RELATIVE_PATH = Path("book") / "assets" / "generated" / "master_cover.png"
APPROVED_COVER_RELATIVE_PATH = SPANISH_ROOT / "assets" / "master_cover_es.png"
# Allow a small antialiasing margin around the two intentionally localized
# panels while prohibiting visual changes anywhere else on the source cover.
COVER_BYLINE_BOX = (180, 1485, 846, 1535)
# This is the existing upper-right Snapchat notification.  The Spanish edition
# replaces that notification as a whole, rather than floating a label over it.
COVER_BADGE_BOX = (708, 54, 1000, 177)
PRINT_MAX_IMAGE_WIDTH_PX = 1500
PRINT_MAX_IMAGE_HEIGHT_PX = 2250


@dataclass
class SpanishChapterPrintRecord:
    chapter_id: str
    title: str
    deck: str
    document_stem: str
    paper_title: str
    public_html_url: str
    public_pdf_url: str
    manuscript_typst_path: Path
    qr_svg_path: Path
    cover_image_path: Path
    research_note_summary: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spanish_chapter_paths(root: Path) -> list[Path]:
    return [root / SOURCE_ROOT / "chapters" / entry["source_file"] for entry in BOOK_CHAPTERS]


def _shape(content: str) -> dict[str, list[str]]:
    return {
        "images": re.findall(r"!\[[^]]*\]\(([^)]+)\)", content),
        "urls": re.findall(r"https?://[^)\s]+", content),
        "headings": re.findall(r"^(#{1,6})\s+", content, flags=re.M),
    }


def validate_spanish_sources(root: Path) -> None:
    """Fail closed until every independently authored chapter is present."""
    full_book = root / SOURCE_ROOT / "full_book.md"
    required = [*spanish_chapter_paths(root), full_book]
    missing = [str(path.relative_to(root)) for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Spanish literary sources are incomplete: " + ", ".join(missing))
    if not (root / REVIEW_MANIFEST).exists():
        raise RuntimeError("Spanish literary edition is missing its Codex review manifest")
    review = json.loads((root / REVIEW_MANIFEST).read_text(encoding="utf-8"))
    expected = [path.relative_to(root).as_posix() for path in required]
    if review.get("locale") != LOCALE or review.get("status") != "codex_self_reviewed" or review.get("chapters") != expected:
        raise RuntimeError("Spanish literary edition has not passed its complete Codex review")
    for english, spanish in zip(
        [root / "book" / "chapters" / entry["source_file"] for entry in BOOK_CHAPTERS],
        spanish_chapter_paths(root),
        strict=True,
    ):
        original, adaptation = english.read_text(encoding="utf-8"), spanish.read_text(encoding="utf-8")
        if _shape(original) != _shape(adaptation):
            raise RuntimeError(f"Spanish chapter changed structural links or images: {spanish.relative_to(root)}")
        if "lang: es-419" not in adaptation:
            raise RuntimeError(f"Spanish chapter must declare lang: es-419: {spanish.relative_to(root)}")
    content = full_book.read_text(encoding="utf-8")
    if "lang: es-419" not in content or f'author: "{BYLINE}"' not in content:
        raise RuntimeError("Spanish full book must declare es-419 and the co-author byline")


def compose_spanish_full_book(root: Path) -> Path:
    """Compose the Spanish book only from the individually authored chapters."""
    chapters = spanish_chapter_paths(root)
    missing = [str(path.relative_to(root)) for path in chapters if not path.exists()]
    if missing:
        raise RuntimeError("Cannot compose Spanish full book; missing chapters: " + ", ".join(missing))
    front_matter = '''---
title: "Hijos del Feed. Siervos del Dios de la IA"
subtitle: "Cómo el tecnofeudalismo nos crió como siervos digitales"
author: "Mark Uriostegui & Paul Lara"
date: ""
lang: es-419
---

![Hijos del Feed. Siervos del Dios de la IA](../assets/generated/master_cover.png)

# Prefacio

Esta edición es la rama literaria pública del programa de investigación AI Empire.

Está escrita para quien ya siente la herida pero todavía no cuenta con todo el vocabulario político para nombrarla: quien creció en línea, sospecha que internet dejó de ser libre y se volvió obligatorio, percibe cómo se fragmenta su atención, se desestabiliza su trabajo, se media su vida social y se cosecha su creatividad.

El argumento de este libro es lo bastante simple para recordarlo y lo bastante difícil para resistirlo:

No solo nos entretuvo el feed.

Nos crió dentro de él.

Nos midió dentro de él.
Y los sistemas que hoy se venden como inteligencia artificial fueron entrenados con lo que allí nos quitaron.

Esta edición literaria tiene menos notas que las investigaciones académicas, pero no menos rigor. Cada capítulo cierra señalando la investigación correspondiente, donde descansa toda la carga documental.

Lee este libro de corrido si quieres recorrer el arco completo. Léelo capítulo por capítulo si quieres un mapa de los momentos precisos en que la máquina entró en tu vida.

## La IA es patrimonio de la humanidad

**LA IA ES PATRIMONIO DE LA HUMANIDAD**

Este proyecto existe para ayudar a la humanidad a recuperar soberanía cívica y creativa para las generaciones futuras.

El programa sostiene que el patrimonio es el núcleo civilizatorio, que la reforma de la Sección 230 responde a la fase de extracción por plataformas y que las obligaciones anticaptura responden a la fase de cercamiento entre Estado y empresa.

1. La IA de frontera fue entrenada con el lenguaje, arte, código, trabajo, cultura, ciencia y emoción colectivos de la humanidad.
2. Lo construido con ese archivo colectivo no puede tratarse por defecto como propiedad privada exclusiva ordinaria.
3. Su gobernanza debe avanzar hacia lógica de fideicomiso público, acceso amplio, supervisión democrática y límites antimonopolio.

Ensayo público fundacional: [AI Copyright Weights: A New Frontier in Intellectual Property Law](https://medium.com/twinchat/ai-copyright-weights-a-new-frontier-in-intellectual-property-law-d8ee1b6c55ee)
'''
    parts = [front_matter]
    for chapter in chapters:
        parts.append(strip_frontmatter(chapter.read_text(encoding="utf-8")).strip())
    output = root / SOURCE_ROOT / "full_book.md"
    ensure_dir(output.parent)
    overwrite(output, "\n\n".join(parts).strip() + "\n")
    return output


def _font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in (
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def create_spanish_cover(root: Path, output: Path) -> Path:
    source = root / "book" / "assets" / "generated" / "master_cover.png"
    approved = root / APPROVED_COVER_RELATIVE_PATH
    if not source.exists():
        raise RuntimeError("English master cover is missing")
    if not approved.exists():
        raise RuntimeError("Approved Spanish master cover is missing")
    original_hash = _sha256(source)
    ensure_dir(output.parent)
    shutil.copy2(approved, output)
    provenance = output.with_suffix(".provenance.json")
    overwrite(provenance, json.dumps({"base": str(source), "base_sha256": original_hash, "approved_source": str(approved), "approved_source_sha256": _sha256(approved), "changes": ["approved_spanish_cover"], "byline": BYLINE}, indent=2) + "\n")
    return output


def _stage_print_asset(root: Path, work: Path, source: Path, destination: Path, role: str) -> Path:
    """Create Spanish-local print derivatives with the English print profile."""
    image = Image.open(source)
    image.thumbnail((PRINT_MAX_IMAGE_WIDTH_PX, PRINT_MAX_IMAGE_HEIGHT_PX), Image.Resampling.LANCZOS)
    if role == "infographic":
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")
        target = destination.with_suffix(".png")
        ensure_dir((work / target).parent)
        image.save(work / target, format="PNG", optimize=True)
        return work / target
    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, "#f8f5ee")
        background.paste(image, mask=image.getchannel("A"))
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")
    target = work / destination.with_suffix(".jpg")
    ensure_dir(target.parent)
    image.save(target, format="JPEG", quality=82, optimize=True, progressive=True)
    return target


def _resolve_spanish_asset(root: Path, chapter_path: Path, rel_path: str) -> Path:
    """Spanish chapters preserve English asset paths without duplicating assets."""
    localized = (chapter_path.parent / rel_path).resolve()
    if localized.exists():
        return localized
    marker = "../assets/generated/"
    if rel_path.startswith(marker):
        fallback = root / "book" / "assets" / "generated" / rel_path.removeprefix(marker)
        if fallback.exists():
            return fallback
    raise RuntimeError(f"Spanish chapter asset is missing: {chapter_path}: {rel_path}")


def _localized_section(content: str, heading: str) -> str:
    return extract_section(content, heading)


def _build_spanish_chapter(
    root: Path, work: Path, entry: dict[str, str], chapter_path: Path,
) -> SpanishChapterPrintRecord:
    """Create a chapter print fragment and QR entirely within the Spanish stage."""
    from .book import parse_frontmatter

    frontmatter = parse_frontmatter(chapter_path.read_text(encoding="utf-8"))
    raw_body = strip_frontmatter(chapter_path.read_text(encoding="utf-8"))
    chapter_id = entry["id"]
    title = str(frontmatter.get("title") or entry["title"])
    document_stem = chapter_path.stem
    paper_title = str(frontmatter.get("paper_title") or entry["paper_title"])
    deck = strip_markdown_images(_localized_section(raw_body, "Bajada")).replace("\n", " ").strip()
    research_basis = sanitize_research_basis_text(_localized_section(raw_body, "Base de investigación"))
    if not research_basis:
        raise RuntimeError(f"Spanish chapter has no research basis: {chapter_path.relative_to(root)}")

    image_paths = extract_image_paths(raw_body)
    cover_rel, retained_body_rel = select_print_visuals(image_paths)
    if not cover_rel:
        raise RuntimeError(f"Spanish chapter has no cover visual: {chapter_path.relative_to(root)}")

    source_cover = _resolve_spanish_asset(root, chapter_path, cover_rel)
    cover_staged = _stage_print_asset(
        root, work, source_cover, Path("assets") / "images" / f"{chapter_id}_cover", "cover",
    )
    staged_images: dict[str, Path] = {}
    for ordinal, rel_path in enumerate(retained_body_rel):
        source = _resolve_spanish_asset(root, chapter_path, rel_path)
        staged_images[rel_path] = _stage_print_asset(
            root,
            work,
            source,
            Path("assets") / "images" / f"{chapter_id}_{ordinal}_{source.stem}",
            classify_image(rel_path),
        )

    public_html_url, public_pdf_url = public_urls_for_chapter(root, chapter_id)
    qr_path = work / "assets" / "qrcodes" / f"{document_stem}_research_qr.svg"
    generate_qr_svg(root, public_html_url, qr_path)

    transformed = remove_first_heading(raw_body)
    for heading in ("Bajada", "Apertura", "Base de investigación", "Siguiente"):
        transformed = remove_section(transformed, heading)
    # The cover is rendered on the dedicated chapter-opening page. Remove its
    # Markdown token before Pandoc sees it so it cannot leak into the deck.
    transformed = re.sub(rf"!\[[^\]]*\]\({re.escape(cover_rel)}\)\s*", "", transformed)
    image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

    def replace_image(match: re.Match[str]) -> str:
        rel_path = match.group(2)
        if rel_path == cover_rel:
            return ""
        staged = staged_images.get(rel_path)
        if staged is None:
            return ""
        rel_staged = os.path.relpath(staged, work / "manuscripts")
        role = classify_image(rel_path)
        width = "100%" if role == "infographic" else "92%"
        image_markdown = f"![]({rel_staged}){{ width={width} }}"
        if chapter_id in INFOGRAPHIC_PLATE_CHAPTERS and role == "infographic":
            return "```{=typst}\n#pagebreak()\n```\n\n" + image_markdown
        return image_markdown

    transformed = image_pattern.sub(replace_image, transformed)
    if chapter_id in MAIN_NARRATIVE_PAGEBREAK_CHAPTERS:
        transformed = transformed.replace(
            "## Narrativa principal",
            "```{=typst}\n#pagebreak()\n```\n\n## Narrativa principal",
            1,
        )
    transformed = normalize_markdown_spacing(transformed)

    qr_rel = os.path.relpath(qr_path, work / "manuscripts")
    notes = textwrap.dedent(
        f"""
        ```{{=typst}}
        #pagebreak()
        ```

        ## Notas de investigación

        {research_basis}

        Escanea este código QR para abrir el paper de investigación en inglés con la base documental completa, las citas y los enlaces de respaldo.

        ![]({qr_rel}){{ width=34% }}

        URL de respaldo: [{display_url(public_html_url)}]({public_html_url})
        """
    ).strip()
    chapter_markdown = work / "manuscripts" / f"{document_stem}.md"
    chapter_typst = work / "manuscripts" / f"{document_stem}.typ"
    ensure_dir(chapter_markdown.parent)
    overwrite(chapter_markdown, normalize_markdown_spacing(transformed + "\n\n" + notes))
    subprocess.run(
        ["pandoc", "--from", "markdown+footnotes", "--to", "typst", str(chapter_markdown), "-o", str(chapter_typst)],
        check=True,
    )
    return SpanishChapterPrintRecord(
        chapter_id=chapter_id,
        title=title,
        deck=deck,
        document_stem=document_stem,
        paper_title=paper_title,
        public_html_url=public_html_url,
        public_pdf_url=public_pdf_url,
        manuscript_typst_path=chapter_typst,
        qr_svg_path=qr_path,
        cover_image_path=cover_staged,
        research_note_summary=research_basis,
    )


def validate_spanish_cover(root: Path, cover: Path) -> None:
    """Verify the derivative changes only the approved badge and byline panels."""
    source = root / "book" / "assets" / "generated" / "master_cover.png"
    original = Image.open(source).convert("RGB")
    localized = Image.open(cover).convert("RGB")
    if original.size != localized.size:
        raise RuntimeError("Spanish cover dimensions differ from the English master cover")
    from PIL import ImageChops

    approved = root / APPROVED_COVER_RELATIVE_PATH
    if _sha256(cover) != _sha256(approved):
        raise RuntimeError("Spanish cover does not match the approved Spanish cover source")


def _write_wrapper(root: Path, work: Path, cover: Path, chapters: list[SpanishChapterPrintRecord]) -> Path:
    typst_content = work / "full_book_es.typ"
    template = root / "apps" / "templates" / "book_print_template.typ"
    template_rel = Path("assets") / "book_print_template.typ"
    cover_rel = Path("book") / "assets" / "generated" / "master_cover.png"
    ensure_dir((work / cover_rel).parent)
    ensure_dir((work / template_rel).parent)
    if cover.resolve() != (work / cover_rel).resolve():
        shutil.copy2(cover, work / cover_rel)
    shutil.copy2(template, work / template_rel)
    chapter_blocks = []
    for index, chapter in enumerate(chapters):
        chapter_cover_rel = os.path.relpath(chapter.cover_image_path, typst_content.parent)
        manuscript_rel = os.path.relpath(chapter.manuscript_typst_path, typst_content.parent)
        trailing_break = "#pagebreak()" if index < len(chapters) - 1 else ""
        chapter_blocks.append(
            textwrap.dedent(
                f'''\
                = {chapter.title}
                #let chapter_meta_{chapter.chapter_id} = (
                  id: "{chapter.chapter_id}",
                  title: "{chapter.title}",
                  deck: "{chapter.deck}",
                  cover: image("{chapter_cover_rel}", width: 100%, height: 2.7in, fit: "cover"),
                  running: "{chapter.title}",
                )
                #chapter-cover-page(chapter_meta_{chapter.chapter_id}, label: "CAPÍTULO")
                #include "{manuscript_rel}"
                {trailing_break}
                '''
            ).strip()
        )
    wrapper = f'''#import "{template_rel.as_posix()}": *
#set document(title: "Hijos del Feed. Siervos del Dios de la IA", author: "{BYLINE}")
#set page(width: 6in, height: 9in, fill: page-paper, header: context print-header("Hijos del Feed", visible-from: 5), footer: context print-footer(visible-from: 5))
#full-bleed-cover(image("{cover_rel.as_posix()}", width: 100%, height: 100%, fit: "cover"))
#book-imprint-page(title-line-1: "Hijos del Feed. Siervos", title-line-2: "del Dios de la IA", subtitle: "Cómo el tecnofeudalismo nos crió como siervos digitales", author: "{BYLINE}", adaptation-line: "Edición literaria en español del programa de investigación AI Empire.", publisher: "Publicado por WakenAI Labs.", copyright: "Copyright Mark Uriostegui & Paul Lara 2026")
#toc-page(title: "Contenido", target: heading.where(level: 1))
{"\n\n".join(chapter_blocks)}
'''
    overwrite(typst_content, wrapper)
    return typst_content


def validate_spanish_pdf(pdf: Path) -> None:
    if not pdf.exists() or pdf.stat().st_size == 0:
        raise RuntimeError("Spanish full-book PDF was not created")
    try:
        import pypdf  # type: ignore
    except ImportError:
        return
    reader = pypdf.PdfReader(str(pdf))
    if not reader.pages:
        raise RuntimeError("Spanish full-book PDF has no pages")
    first = reader.pages[0]
    if round(float(first.mediabox.width)) != 432 or round(float(first.mediabox.height)) != 648:
        raise RuntimeError("Spanish full-book PDF is not 6x9")


def _runtime_pypdf():
    try:
        import pypdf  # type: ignore
        return pypdf
    except ImportError:
        import sys

        for candidate in sorted(Path.home().glob(".cache/codex-runtimes/*/dependencies/python/lib/python*/site-packages")):
            if (candidate / "pypdf").exists():
                sys.path.append(str(candidate))
                import pypdf  # type: ignore
                return pypdf
        raise RuntimeError("pypdf is required for Spanish print validation")


def validate_spanish_print_edition(root: Path, work: Path, pdf: Path, chapters: list[SpanishChapterPrintRecord]) -> None:
    """Ensure the isolated edition has one QR research-note page per chapter."""
    manifest_path = work / "qr_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_base = "https://markuriostegui.github.io/childrenofthefeed/"
    entries = manifest.get("entries", [])
    if len(entries) != len(BOOK_CHAPTERS):
        raise RuntimeError("Spanish QR manifest does not cover all chapters")
    for entry in entries:
        url = str(entry.get("public_html_url", ""))
        if not url.startswith(expected_base) or "hassanvfx.github.io/ai-empire" in url:
            raise RuntimeError(f"Spanish QR target has an invalid base URL: {url}")
        if not (work / entry["qr_svg_path"]).exists():
            raise RuntimeError(f"Spanish QR asset is missing: {entry['qr_svg_path']}")
    pypdf = _runtime_pypdf()
    reader = pypdf.PdfReader(str(pdf))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if text.count("Notas de investigación") != len(chapters):
        raise RuntimeError("Spanish PDF is missing one or more research-note sections")
    if text.count("CAPÍTULO") != len(chapters):
        raise RuntimeError("Spanish PDF is missing one or more chapter opening pages")
    if "hassanvfx.github.io/ai-empire" in text:
        raise RuntimeError("Spanish PDF contains the retired publication URL")


def _write_spanish_qr_manifest(work: Path, chapters: list[SpanishChapterPrintRecord]) -> Path:
    entries = []
    for chapter in chapters:
        entries.append(
            {
                "chapter_id": chapter.chapter_id,
                "document_stem": chapter.document_stem,
                "public_html_url": chapter.public_html_url,
                "public_pdf_url": chapter.public_pdf_url,
                "qr_svg_path": str(chapter.qr_svg_path.relative_to(work)),
                "sha256": _sha256(chapter.qr_svg_path),
            }
        )
    path = work / "qr_manifest.json"
    overwrite(path, json.dumps({"locale": LOCALE, "base_url": "https://markuriostegui.github.io/childrenofthefeed/", "entries": entries}, indent=2) + "\n")
    return path


def export_book_print_spanish(root: Path) -> Path:
    """Create and atomically publish only the isolated Spanish full-book PDF."""
    if shutil.which("typst") is None:
        raise RuntimeError("Typst is required for export-book-print-spanish")
    validate_spanish_sources(root)
    destination = root / PUBLIC_ROOT
    stage_parent = root / BUILD_ROOT / ".tmp"
    ensure_dir(stage_parent)
    with tempfile.TemporaryDirectory(prefix="children-feed-es-", dir=stage_parent) as temp:
        work = Path(temp) / "esp"
        ensure_dir(work)
        cover = create_spanish_cover(root, work / COVER_RELATIVE_PATH)
        validate_spanish_cover(root, cover)
        chapters = [
            _build_spanish_chapter(root, work, entry, chapter_path)
            for entry, chapter_path in zip(BOOK_CHAPTERS, spanish_chapter_paths(root), strict=True)
        ]
        _write_spanish_qr_manifest(work, chapters)
        wrapper = _write_wrapper(root, work, cover, chapters)
        candidate = work / PDF_RELATIVE_PATH
        ensure_dir(candidate.parent)
        subprocess.run(["typst", "compile", "--root", str(root), "--font-path", str(root / "book" / "print" / "fonts"), str(wrapper), str(candidate)], check=True)
        validate_spanish_pdf(candidate)
        validate_spanish_print_edition(root, work, candidate, chapters)
        build_pdf = root / BUILD_ROOT / PDF_RELATIVE_PATH
        build_cover = root / BUILD_ROOT / COVER_RELATIVE_PATH
        ensure_dir(build_pdf.parent); ensure_dir(build_cover.parent)
        shutil.copy2(candidate, build_pdf); shutil.copy2(cover, build_cover)
        build_qr_root = root / BUILD_ROOT / "book" / "assets" / "qrcodes"
        shutil.copytree(work / "assets" / "qrcodes", build_qr_root, dirs_exist_ok=True)
        shutil.copy2(work / "qr_manifest.json", root / BUILD_ROOT / "book" / "qr_manifest.json")
        next_destination = destination.with_name("esp.next")
        if next_destination.exists(): shutil.rmtree(next_destination)
        shutil.copytree(work / "book", next_destination / "book")
        shutil.copytree(work / "assets" / "qrcodes", next_destination / "book" / "assets" / "qrcodes")
        shutil.copy2(work / "qr_manifest.json", next_destination / "book" / "qr_manifest.json")
        if destination.exists(): shutil.rmtree(destination)
        next_destination.replace(destination)
    from .lulu_press import export_lulu_interior

    export_lulu_interior(root, "es")
    return root / PUBLIC_ROOT / PDF_RELATIVE_PATH


def activate_spanish_pdf_link(root: Path) -> None:
    """Refresh only the English landing after a validated Spanish publish."""
    from .book import BOOK_INTERACTIVE_APP_PUBLISHED_HREF, render_book_landing_html

    landing = root / "build" / "site" / "book" / "index.html"
    if not (root / PUBLIC_ROOT / PDF_RELATIVE_PATH).exists() or not landing.exists():
        raise RuntimeError("Cannot activate Spanish PDF link before the Spanish PDF is published")
    overwrite(
        landing,
        render_book_landing_html(root, BOOK_INTERACTIVE_APP_PUBLISHED_HREF, "../esp/book/pdf/full_book.pdf"),
    )
