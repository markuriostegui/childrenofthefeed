from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from pypdf import PdfReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from apps.research_cli.research_cli.lulu_press import EDITIONS, PAGE_HEIGHT, PAGE_WIDTH, TITLE_ART_PIXELS, export_lulu_interior


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class LuluPressTests(unittest.TestCase):
    def make_root(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        fonts = root / "book/print/fonts"
        fonts.mkdir(parents=True)
        for name in ("SourceSerif4.ttf", "SourceSans3.ttf"):
            shutil.copy2(PROJECT_ROOT / "book/print/fonts" / name, fonts / name)
        for edition in EDITIONS.values():
            path = root / edition.title_art
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", TITLE_ART_PIXELS, "#101010").save(path)
        (root / "book/assets/generated").mkdir(parents=True, exist_ok=True)
        (root / "esp/assets").mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (2, 2), "#111111").save(root / "book/assets/generated/master_cover.png")
        Image.new("RGB", (2, 2), "#222222").save(root / "esp/assets/master_cover_es.png")
        return root

    def make_source(self, root: Path, edition_key: str) -> Path:
        edition = EDITIONS[edition_key]
        source = root / edition.source_pdf
        source.parent.mkdir(parents=True, exist_ok=True)
        font_path = root / "book/print/fonts/SourceSerif4.ttf"
        if "FixtureSource" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("FixtureSource", str(font_path)))
        canvas = Canvas(str(source), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
        for label in ("original title", "original imprint", "dedication", "contents", "body text"):
            canvas.setFillColorRGB(0.96862745, 0.9490196, 0.9098039)
            canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, stroke=0, fill=1)
            canvas.setFillColorRGB(0, 0, 0)
            canvas.setFont("FixtureSource", 12)
            canvas.drawString(72, 500, label)
            canvas.showPage()
        canvas.save()
        return source

    def test_postprocessor_replaces_front_matter_without_changing_page_count(self) -> None:
        root = self.make_root()
        source = self.make_source(root, "en")
        output = export_lulu_interior(root, "en", source_pdf=source)
        reader = PdfReader(str(output))

        self.assertEqual(len(reader.pages), 5)
        self.assertIn("Imprint: Lulu.com", reader.pages[1].extract_text())
        self.assertIn("978-0-557-94877-2", reader.pages[1].extract_text())
        self.assertIn("Magnificent Humanity", reader.pages[2].extract_text())
        self.assertIn("contents", reader.pages[3].extract_text())
        self.assertIn("body text", reader.pages[4].extract_text())
        self.assertEqual((float(reader.pages[0].mediabox.width), float(reader.pages[0].mediabox.height)), (PAGE_WIDTH, PAGE_HEIGHT))

        manifest = json.loads((output.parent / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["isbn"], "978-0-557-94877-2")
        self.assertEqual(manifest["source_pdf"]["page_count"], manifest["interior_pdf"]["page_count"])
        self.assertTrue(manifest["preflight"]["passed"])
        self.assertEqual(manifest["title_art"]["output"]["pixels"], list(TITLE_ART_PIXELS))
        white_source = PdfReader(str(root / manifest["white_source_pdf"]["path"]))
        self.assertEqual(len(white_source.pages), 5)
        self.assertEqual(manifest["white_source_pdf"]["whitened_pages"], 5)
        self.assertNotIn(b".968627 .94902 .909804 rg", white_source.pages[4].get_contents().get_data())
        self.assertNotIn("barcode", reader.pages[0].extract_text().lower())
        # The copyright page intentionally contains no rule that can cross
        # the imprint; it has text-only content.
        self.assertNotIn(b" m ", reader.pages[1].get_contents().get_data())

    def test_spanish_copyright_page_has_its_isbn_and_authors(self) -> None:
        root = self.make_root()
        source = self.make_source(root, "es")
        output = export_lulu_interior(root, "es", source_pdf=source)
        reader = PdfReader(str(output))
        copyright_text = reader.pages[1].extract_text()

        self.assertIn("978-0-557-94875-8", copyright_text)
        self.assertIn("Mark Uriostegui & Paul Lara", copyright_text)
        self.assertNotIn("978-0-557-94877-2", copyright_text)
        self.assertEqual(len(reader.pages), len(PdfReader(str(source)).pages) + 1)
        self.assertIn("A la magnífica humanidad.", reader.pages[2].extract_text())
