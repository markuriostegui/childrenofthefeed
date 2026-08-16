"""Lulu-specific 6 x 9 inch interior PDF post-processing."""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from .book import DEDICATION_HEADING, DEDICATION_INTRO, DEDICATION_LINES


PAGE_WIDTH = 432.0
PAGE_HEIGHT = 648.0
TRIM_IN = (6.0, 9.0)
TITLE_ART_PIXELS = (2160, 3240)
SAFE_MARGIN = 36.0  # Lulu's 0.5 inch minimum safe area.
LULU_ROOT = Path("lulu-press")
PAPER_FILL = b"/c0 cs 0.96862745 0.9490196 0.9098039 scn"
WHITE_PAPER_FILL = b"/DeviceRGB cs 1 1 1 scn"
# ReportLab's compact equivalent is useful for isolated fixture PDFs.
REPORTLAB_PAPER_FILL = b".968627 .94902 .909804 rg"
REPORTLAB_WHITE_PAPER_FILL = b"1 1 1 rg"


@dataclass(frozen=True)
class LuluEdition:
    key: str
    isbn: str
    language: str
    title: str
    subtitle: str
    author: str
    copyright: str
    source_pdf: Path
    title_art: Path

    @property
    def output_pdf(self) -> Path:
        return LULU_ROOT / self.key / f"{self.isbn}-interior.pdf"


EDITIONS = {
    "en": LuluEdition(
        key="en",
        isbn="978-0-557-94877-2",
        language="English",
        title="Children of the Feed. Servants of the AI God",
        subtitle="How technofeudalism raised us as digital serfs",
        author="Mark Uriostegui",
        copyright="Copyright Mark Uriostegui 2026",
        source_pdf=Path("build/book/pdf/full_book/full_book.pdf"),
        title_art=LULU_ROOT / "assets/title-art/children-of-the-feed-en-gpt-image-2.png",
    ),
    "es": LuluEdition(
        key="es",
        isbn="978-0-557-94875-8",
        language="Spanish (es-419)",
        title="Hijos del Feed. Siervos del Dios de la IA",
        subtitle="Cómo el tecnofeudalismo nos crió como siervos digitales",
        author="Mark Uriostegui & Paul Lara",
        copyright="Copyright Mark Uriostegui & Paul Lara 2026",
        source_pdf=Path("build/esp/book/pdf/full_book.pdf"),
        title_art=LULU_ROOT / "assets/title-art/children-of-the-feed-es-gpt-image-2.png",
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _register_fonts(root: Path) -> tuple[str, str]:
    font_dir = root / "book/print/fonts"
    regular = "LuluSourceSerif"
    bold = "LuluSourceSans"
    if regular not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(regular, str(font_dir / "SourceSerif4.ttf")))
    if bold not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(bold, str(font_dir / "SourceSans3.ttf")))
    return regular, bold


def _single_page_pdf(draw: Any) -> Any:
    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=(PAGE_WIDTH, PAGE_HEIGHT), pageCompression=1)
    draw(canvas)
    canvas.save()
    return PdfReader(io.BytesIO(buffer.getvalue())).pages[0]


def _title_page(root: Path, edition: LuluEdition) -> Any:
    title_art = root / edition.title_art
    if not title_art.exists():
        raise RuntimeError(f"Missing approved Lulu title art: {title_art}")
    with Image.open(title_art) as image:
        if image.size != TITLE_ART_PIXELS:
            raise RuntimeError(f"Lulu title art must be {TITLE_ART_PIXELS[0]}x{TITLE_ART_PIXELS[1]}: {title_art}")

    def draw(canvas: Canvas) -> None:
        # Page 1 is full trim: Lulu prints this exact 6x9 page with no separate
        # exterior-cover bleed extension or crop marks.
        # Keep any raster edge interpolation visually continuous with the
        # predominantly black cover art.
        canvas.setFillColor(HexColor("#000000"))
        canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
        canvas.drawImage(
            ImageReader(str(title_art)),
            0,
            0,
            width=PAGE_WIDTH,
            height=PAGE_HEIGHT,
            preserveAspectRatio=False,
            mask="auto",
        )

    return _single_page_pdf(draw)


def _copyright_page(root: Path, edition: LuluEdition) -> Any:
    serif, sans = _register_fonts(root)

    def draw(canvas: Canvas) -> None:
        canvas.setFillColor(HexColor("#18130f"))
        canvas.setFont(serif, 18)
        canvas.drawCentredString(PAGE_WIDTH / 2, 470, edition.title)
        canvas.setFont(serif, 11)
        canvas.drawCentredString(PAGE_WIDTH / 2, 446, edition.subtitle)
        canvas.setFont(sans, 10)
        lines = (edition.author, edition.copyright, "Imprint: Lulu.com", f"ISBN: {edition.isbn}")
        for offset, line in enumerate(lines):
            canvas.drawCentredString(PAGE_WIDTH / 2, 346 - offset * 25, line)
        canvas.setFont(serif, 8.5)
        canvas.setFillColor(HexColor("#6d6256"))
        canvas.drawCentredString(PAGE_WIDTH / 2, 100, "Lulu Global Distribution interior edition")

    return _single_page_pdf(draw)


def _spanish_dedication_page(root: Path) -> Any:
    """Spanish source has no dedication page; add the required recto page."""
    serif, sans = _register_fonts(root)

    def draw(canvas: Canvas) -> None:
        canvas.setFillColor(HexColor("#18130f"))
        canvas.setFont(sans, 11)
        canvas.drawCentredString(PAGE_WIDTH / 2, 422, "A NUESTRA AMADA HUMANIDAD")
        canvas.setFont(serif, 16)
        canvas.drawCentredString(PAGE_WIDTH / 2, 342, "A la magnífica humanidad.")
        canvas.setStrokeColor(HexColor("#c6b18a"))
        canvas.setLineWidth(0.6)
        canvas.line(SAFE_MARGIN, 310, PAGE_WIDTH - SAFE_MARGIN, 310)
        canvas.setFont(serif, 9)
        canvas.setFillColor(HexColor("#6d6256"))
        canvas.drawCentredString(PAGE_WIDTH / 2, 155, "La IA es patrimonio de la humanidad.")

    return _single_page_pdf(draw)


def _english_dedication_page(root: Path) -> Any:
    """Rebuild the authored dedication with a fully embedded Unicode font."""
    serif, sans = _register_fonts(root)
    unicode_font = "LuluArialUnicode"
    if unicode_font not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(unicode_font, "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"))

    def draw(canvas: Canvas) -> None:
        canvas.setFillColor(HexColor("#b8872b"))
        canvas.setFont(sans, 10)
        canvas.drawCentredString(PAGE_WIDTH / 2, 565, DEDICATION_HEADING.upper())
        canvas.setFillColor(HexColor("#18130f"))
        canvas.setFont(serif, 11)
        canvas.drawCentredString(PAGE_WIDTH / 2, 520, DEDICATION_INTRO)
        canvas.setFont(unicode_font, 10)
        for index, line in enumerate(DEDICATION_LINES):
            canvas.drawCentredString(PAGE_WIDTH / 2, 495 - index * 17, line)
        canvas.setFillColor(HexColor("#9e3d23"))
        canvas.setFont(sans, 9)
        canvas.drawCentredString(PAGE_WIDTH / 2, 235, "FREE AI NOW. IT IS HUMANITY'S PATRIMONY.")
        canvas.setFillColor(HexColor("#18130f"))
        canvas.setFont(serif, 8.5)
        canvas.drawCentredString(PAGE_WIDTH / 2, 195, "Frontier AI was trained on humanity's collective language, art, code, labor, culture,")
        canvas.drawCentredString(PAGE_WIDTH / 2, 181, "science, and emotion.")
        canvas.setFillColor(HexColor("#6d6256"))
        canvas.setFont(serif, 7.5)
        canvas.drawCentredString(PAGE_WIDTH / 2, 92, "This Lulu edition preserves the dedication with embedded Unicode glyphs.")

    return _single_page_pdf(draw)


def _font_embedded(font: Any) -> bool:
    font = font.get_object()
    # ReportLab declares Helvetica for its empty initial text state even on
    # image-only pages. It is not painted in the generated title page.
    if str(font.get("/BaseFont", "")).lstrip("/") in {"Helvetica", "Times-Roman", "Courier"}:
        return True
    descriptor = font.get("/FontDescriptor")
    descendants = font.get("/DescendantFonts", [])
    if descriptor is None and descendants:
        descriptor = descendants[0].get_object().get("/FontDescriptor")
    if descriptor is None:
        return False
    descriptor = descriptor.get_object()
    return any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3"))


def _white_source_path(edition: LuluEdition) -> Path:
    return LULU_ROOT / edition.key / "white-source.pdf"


def _white_page_background(page: Any) -> bool:
    """Replace the public print template's cream full-page fill with white."""
    contents = page.get_contents()
    if contents is None:
        return False
    data = contents.get_data()
    if PAPER_FILL in data:
        replacement_source, replacement_target = PAPER_FILL, WHITE_PAPER_FILL
    elif REPORTLAB_PAPER_FILL in data:
        replacement_source, replacement_target = REPORTLAB_PAPER_FILL, REPORTLAB_WHITE_PAPER_FILL
    else:
        return False
    stream = DecodedStreamObject()
    # The source uses its custom ICC colour space (c0).  Switching only its
    # component values can still render as cream, so set white in DeviceRGB.
    stream.set_data(data.replace(replacement_source, replacement_target, 1))
    page.replace_contents(stream)
    return True


def render_lulu_white_source(root: Path, edition: LuluEdition, source_pdf: Path) -> tuple[Path, int]:
    """Create a Lulu-only white-paper source without modifying the public PDF."""
    reader = PdfReader(str(source_pdf))
    writer = PdfWriter()
    whitened_pages = 0
    for page in reader.pages:
        # Mutate the writer-owned clone.  `add_page` recreates a source page's
        # content stream, so a change made to the reader-owned page would be
        # discarded during that clone.
        writer.add_page(page)
        if _white_page_background(writer.pages[-1]):
            whitened_pages += 1
    output = root / _white_source_path(edition)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        writer.write(handle)
    return output, whitened_pages


def _page_fonts(page: Any) -> list[tuple[str, Any]]:
    resources = page.get("/Resources")
    if resources is None:
        return []
    fonts = resources.get_object().get("/Font", {})
    return [(str(name), font) for name, font in fonts.get_object().items()]


def _font_is_used(page: Any, resource_name: str) -> bool:
    """Ignore standard fallback fonts that ReportLab declares but never uses."""
    content = page.get_contents()
    if content is None:
        return False
    data = content.get_data()
    return resource_name.encode("ascii") in data


def preflight_lulu_interior(root: Path, edition: LuluEdition, pdf_path: Path) -> dict[str, Any]:
    reader = PdfReader(str(pdf_path))
    failures: list[str] = []
    if reader.is_encrypted:
        failures.append("PDF is encrypted")
    if len(reader.pages) < 4:
        failures.append("Interior must include title, copyright, dedication, and TOC pages")
    for index, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if round(width, 2) != PAGE_WIDTH or round(height, 2) != PAGE_HEIGHT:
            failures.append(f"Page {index} is not 6x9: {width}x{height}")
        for font_name, font in _page_fonts(page):
            if _font_is_used(page, font_name) and not _font_embedded(font):
                failures.append(f"Page {index} contains an unembedded font")
                break
    copyright_text = reader.pages[1].extract_text() or ""
    for required in (edition.title, edition.author, edition.copyright, "Imprint: Lulu.com", edition.isbn):
        if required not in copyright_text:
            failures.append(f"Copyright page is missing: {required}")
    if reader.pages[0].extract_text() and edition.title not in (reader.pages[0].extract_text() or ""):
        failures.append("Title page text does not contain the edition title")
    qpdf = shutil.which("qpdf")
    qpdf_result = "not installed"
    if qpdf:
        result = subprocess.run([qpdf, "--check", str(pdf_path)], capture_output=True, text=True)
        qpdf_result = result.stdout.strip() or result.stderr.strip() or "passed"
        if result.returncode:
            failures.append("qpdf structural check failed")
    report = {
        "edition": edition.key,
        "isbn": edition.isbn,
        "trim_in": {"width": TRIM_IN[0], "height": TRIM_IN[1]},
        "page_size_points": {"width": PAGE_WIDTH, "height": PAGE_HEIGHT},
        "page_count": len(reader.pages),
        "encrypted": reader.is_encrypted,
        "qpdf": qpdf_result,
        "failures": failures,
        "passed": not failures,
    }
    if failures:
        raise RuntimeError("Lulu preflight failed:\n" + "\n".join(failures))
    return report


def _write_provenance(root: Path, edition: LuluEdition) -> dict[str, Any]:
    title_art = root / edition.title_art
    reference = root / ("book/assets/generated/master_cover.png" if edition.key == "en" else "esp/assets/master_cover_es.png")
    prompt = (
        "GPT Image 2 reference-preserving full-trim 2:3 title-art rendition. Preserve all artwork, crop, "
        "colors, typography, spelling, punctuation, composition, branding, and layout; change only resolution/detail."
    )
    return {
        "model": "gpt-image-2 (ChatGPT integrated image editor)",
        "prompt": prompt,
        "reference": {"path": _relative(root, reference), "sha256": _sha256(reference)},
        "output": {"path": _relative(root, title_art), "sha256": _sha256(title_art), "pixels": list(TITLE_ART_PIXELS)},
    }


def export_lulu_interior(root: Path, edition_key: str, *, source_pdf: Path | None = None) -> Path:
    edition = EDITIONS[edition_key]
    source = source_pdf or root / edition.source_pdf
    if not source.exists():
        raise RuntimeError(f"Missing source print PDF for Lulu edition {edition_key}: {source}")
    white_source, whitened_pages = render_lulu_white_source(root, edition, source)
    source_reader = PdfReader(str(white_source))
    if len(source_reader.pages) < 4:
        raise RuntimeError("Source print PDF has insufficient front matter for Lulu post-processing")
    output = root / edition.output_pdf
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    writer.add_page(_title_page(root, edition))
    writer.add_page(_copyright_page(root, edition))
    if edition.key == "es":
        writer.add_page(_spanish_dedication_page(root))
        remaining_pages = source_reader.pages[2:]
    else:
        # Re-render rather than copy page 3 because the source PDF has missing
        # Devanagari/CJK glyphs in headless raster review.
        writer.add_page(_english_dedication_page(root))
        remaining_pages = source_reader.pages[3:]
    for page in remaining_pages:
        writer.add_page(page)
    writer.add_metadata({"/Title": edition.title, "/Author": edition.author, "/Subject": f"Lulu 6x9 interior · ISBN {edition.isbn}"})
    with output.open("wb") as handle:
        writer.write(handle)
    expected_page_count = len(source_reader.pages) + (1 if edition.key == "es" else 0)
    if len(writer.pages) != expected_page_count:
        raise RuntimeError("Lulu post-processing produced an unexpected page count")
    report = preflight_lulu_interior(root, edition, output)
    manifest = {
        "edition": edition.key,
        "language": edition.language,
        "isbn": edition.isbn,
        "imprint": "Lulu.com",
        "source_pdf": {"path": _relative(root, source), "sha256": _sha256(source), "page_count": len(source_reader.pages)},
        "white_source_pdf": {
            "path": _relative(root, white_source),
            "sha256": _sha256(white_source),
            "page_count": len(source_reader.pages),
            "whitened_pages": whitened_pages,
        },
        "interior_pdf": {"path": _relative(root, output), "sha256": _sha256(output), "page_count": len(writer.pages)},
        "title_art": _write_provenance(root, edition),
        "front_matter": ["visual title art", "copyright / ISBN", "dedication", "generated TOC"],
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "preflight": report,
    }
    (output.parent / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output.parent / "preflight.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return output


def review_lulu_interiors(root: Path) -> None:
    for edition in EDITIONS.values():
        pdf_path = root / edition.output_pdf
        if not pdf_path.exists():
            raise RuntimeError(f"Missing Lulu interior: {pdf_path}")
        preflight_lulu_interior(root, edition, pdf_path)
