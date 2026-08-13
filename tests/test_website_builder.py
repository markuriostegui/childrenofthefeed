from __future__ import annotations

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from apps.research_cli.research_cli.book import (
    BOOK_INTERACTIVE_APP_LOCAL_HREF,
    BOOK_INTERACTIVE_APP_PUBLISHED_HREF,
    CHAPTER_FOOTER_NAV_MARKER,
    SOUNDCLOUD_EMBED_MARKER,
    build_site,
    export_book,
    inject_soundcloud_into_chapter_html,
    inject_chapter_footer_nav,
    inject_soundcloud_into_full_book_html,
    render_chapter_footer_nav,
    render_book_landing_html,
    render_soundcloud_audio_block,
)
from apps.research_cli.research_cli.doctrine import VIMEO_HERO_EMBED_URL
from apps.research_cli.research_cli.papers import render_publication_index
from apps.research_cli.research_cli.publication_review import analyze_site_tree, analyze_website_bundle, render_report
from apps.research_cli.research_cli.website import (
    build_website,
    default_reader_state,
    delete_note,
    get_autoplay_delay_ms,
    merge_text_pieces,
    normalize_reader_state,
    render_css,
    render_js,
    serialize_chapter,
    split_long_text,
    toggle_favorite,
    update_progress,
    upsert_note,
    rewrite_chapters_for_pages_mirror,
)


class WebsiteBuilderTests(unittest.TestCase):
    def make_root(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        (root / "apps" / "templates").mkdir(parents=True)
        (root / "book" / "chapters").mkdir(parents=True)
        (root / "book" / "assets" / "generated" / "covers").mkdir(parents=True)
        (root / "book" / "assets" / "generated" / "illustrations").mkdir(parents=True)
        (root / "book" / "assets" / "generated" / "infographics").mkdir(parents=True)
        (root / "build" / "book" / "assets" / "generated" / "covers").mkdir(parents=True)
        (root / "build" / "book" / "assets" / "generated" / "illustrations").mkdir(parents=True)
        (root / "build" / "book" / "assets" / "generated" / "infographics").mkdir(parents=True)
        (root / "public" / "assets" / "brand").mkdir(parents=True)
        (root / "build" / "site").mkdir(parents=True)
        (root / "public" / "assets" / "brand" / "waken-ai-black.webp").write_bytes(b"brand")
        (root / "apps" / "templates" / "book_export.css").write_text("body{}", encoding="utf-8")
        (root / "apps" / "templates" / "book_export_header.tex").write_text("% header", encoding="utf-8")
        (root / "book" / "index.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: "Index"
                ---

                Preface body.
                """
            ),
            encoding="utf-8",
        )

        images = {
            "book/assets/generated/master_cover.png",
            "book/assets/generated/covers/alpha-cover.png",
            "book/assets/generated/covers/beta-cover.png",
            "book/assets/generated/illustrations/alpha-scene.png",
            "book/assets/generated/illustrations/beta-scene.png",
            "book/assets/generated/infographics/alpha-graphic.png",
        }
        for relative in images:
            path = root / relative
            path.write_bytes(b"not-a-real-image-but-good-enough-for-copy")
            build_book_path = root / "build" / "book" / Path(relative).relative_to("book")
            build_book_path.parent.mkdir(parents=True, exist_ok=True)
            build_book_path.write_bytes(b"not-a-real-image-but-good-enough-for-copy")

        alpha = textwrap.dedent(
            """\
            ---
            title: "Alpha"
            chapter_id: "01"
            ---

            # Alpha

            ## Deck

            ![Alpha cover](../assets/generated/covers/alpha-cover.png)

            ## Opening

            Do you feel the feed already shaping what you notice first?

            Tiny line.

            ## Main Narrative

            This is the first long paragraph. It should stay readable when the reader turns chapter prose into mobile blocks. The text should split cleanly by sentence if it grows too long for a screen and should still preserve the emotional beat of the original editorial chapter.

            ![Alpha scene](../assets/generated/illustrations/alpha-scene.png)

            After the image, the chapter should switch backgrounds for all following text blocks.

            ![Alpha infographic](../assets/generated/infographics/alpha-graphic.png)

            Another short fragment that should stay attached to the infographic image.

            ## Research Basis

            This line should not be serialized.

            ## Next

            This line should also not be serialized.
            """
        )
        beta = textwrap.dedent(
            """\
            ---
            title: "Beta"
            chapter_id: "02"
            ---

            # Beta

            ## Deck

            ![Beta cover](../assets/generated/covers/beta-cover.png)

            ## Opening

            Can a reader start anywhere and still feel the chapter rhythm?

            ## Main Narrative

            A second chapter proves ordering and bundle generation.

            ![Beta scene](../assets/generated/illustrations/beta-scene.png)

            The second scene confirms that mirrored assets stay self-contained.
            """
        )
        # Intentionally write chapter files out of order to verify chapter_id sorting.
        (root / "book" / "chapters" / "02_beta.md").write_text(beta, encoding="utf-8")
        (root / "book" / "chapters" / "01_alpha.md").write_text(alpha, encoding="utf-8")
        return root

    def test_split_long_text_respects_soft_ceiling(self) -> None:
        text = " ".join(
            [
                "This is a sentence about reading rhythm."
                " Another sentence keeps the pacing clear."
                " A third sentence adds pressure to the chunk size."
            ]
            * 8
        )
        chunks = split_long_text(text)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk.split()) <= 110 for chunk in chunks))

    def test_merge_text_pieces_merges_short_fragments(self) -> None:
        merged = merge_text_pieces(
            [
                "Do you feel the feed watching?",
                "Tiny line.",
                "Another brief fragment to keep the block readable.",
            ]
        )
        self.assertEqual(len(merged), 1)
        self.assertIn("Tiny line.", merged[0])

    def test_serialize_chapter_excludes_research_and_respects_images(self) -> None:
        root = self.make_root()
        website_root = root / "website"
        (website_root / "assets" / "images").mkdir(parents=True)
        chapter = serialize_chapter(
            root,
            website_root,
            root / "book" / "chapters" / "01_alpha.md",
            {},
        )
        joined = " ".join(block["text"] for block in chapter["blocks"])
        self.assertNotIn("serialized.", joined)
        self.assertNotIn("also not be serialized", joined)
        self.assertEqual(chapter["blocks"][0]["image"], "assets/images/generated/covers/alpha-cover.png")
        self.assertEqual(chapter["blocks"][-1]["image"], "assets/images/generated/infographics/alpha-graphic.png")

    def test_build_website_writes_bundle_and_mirror(self) -> None:
        root = self.make_root()
        build_website(root)

        website_root = root / "website"
        mirrored_root = root / "build" / "site" / "website"
        chapters = json.loads((website_root / "data" / "chapters.json").read_text(encoding="utf-8"))
        mirrored_chapters = json.loads((mirrored_root / "data" / "chapters.json").read_text(encoding="utf-8"))

        self.assertEqual([chapter["title"] for chapter in chapters], ["Alpha", "Beta"])
        self.assertTrue((website_root / "index.html").exists())
        self.assertTrue((website_root / "assets" / "css" / "app.css").exists())
        self.assertTrue((website_root / "assets" / "js" / "app.js").exists())
        self.assertTrue((mirrored_root / "data" / "chapters.json").exists())
        self.assertTrue(all(set(block.keys()) == {"text", "image"} for chapter in chapters for block in chapter["blocks"]))
        for chapter in chapters:
            self.assertGreater(len(chapter["blocks"]), 0)
            for block in chapter["blocks"]:
                self.assertTrue((website_root / block["image"]).exists(), block["image"])
        self.assertTrue(all(block["image"].startswith("../book/assets/generated/") for chapter in mirrored_chapters for block in chapter["blocks"]))
        self.assertFalse((mirrored_root / "assets" / "images" / "generated").exists())
        self.assertTrue((mirrored_root / "assets" / "images" / "waken-ai-black.webp").exists())

    def test_build_site_rebuilds_website_bundle_automatically(self) -> None:
        root = self.make_root()
        build_site(root)

        mirrored_root = root / "build" / "site" / "website"
        first_titles = [
            chapter["title"]
            for chapter in json.loads((mirrored_root / "data" / "chapters.json").read_text(encoding="utf-8"))
        ]
        (mirrored_root / "data" / "chapters.json").write_text("[]", encoding="utf-8")

        build_site(root)

        rebuilt_titles = [
            chapter["title"]
            for chapter in json.loads((mirrored_root / "data" / "chapters.json").read_text(encoding="utf-8"))
        ]
        self.assertEqual(first_titles, ["Alpha", "Beta"])
        self.assertEqual(rebuilt_titles, ["Alpha", "Beta"])
        rebuilt_chapters = json.loads((mirrored_root / "data" / "chapters.json").read_text(encoding="utf-8"))
        self.assertTrue(all(block["image"].startswith("../book/assets/generated/") for chapter in rebuilt_chapters for block in chapter["blocks"]))

    def test_analyze_website_bundle_detects_broken_assets(self) -> None:
        root = self.make_root()
        build_site(root)

        website_root = root / "build" / "site" / "website"
        result = analyze_website_bundle(website_root)
        self.assertEqual(result["status"], "pass")

        chapters = json.loads((website_root / "data" / "chapters.json").read_text(encoding="utf-8"))
        broken_image = (website_root / chapters[0]["blocks"][0]["image"]).resolve()
        broken_image.unlink()

        broken_result = analyze_website_bundle(website_root)
        self.assertEqual(broken_result["status"], "fail")
        self.assertGreater(broken_result["broken_image_count"], 0)

    def test_rewrite_chapters_for_pages_mirror_preserves_schema(self) -> None:
        chapters = [
            {
                "title": "Alpha",
                "blocks": [
                    {"text": "One", "image": "assets/images/generated/covers/alpha-cover.png"},
                    {"text": "Two", "image": "assets/images/waken-ai-black.webp"},
                ],
            }
        ]
        rewritten = rewrite_chapters_for_pages_mirror(chapters)
        self.assertEqual(set(rewritten[0].keys()), {"title", "blocks"})
        self.assertEqual(set(rewritten[0]["blocks"][0].keys()), {"text", "image"})
        self.assertEqual(rewritten[0]["blocks"][0]["image"], "../book/assets/generated/covers/alpha-cover.png")
        self.assertEqual(rewritten[0]["blocks"][1]["image"], "assets/images/waken-ai-black.webp")

    def test_render_report_includes_website_bundle_section(self) -> None:
        report = render_report(
            {
                "papers": [],
                "volumes": [],
                "books": [],
                "site": {"status": "pass", "literary_card_present": True, "book_link_present": True, "raw_repo_path_hits": 0},
                "site_tree": {
                    "status": "pass",
                    "html_file_count": 1,
                    "checked_reference_count": 0,
                    "missing_local_target_count": 0,
                    "forbidden_artifact_count": 0,
                },
                "website": {
                    "status": "pass",
                    "index_present": True,
                    "chapters_json_present": True,
                    "chapter_count": 2,
                    "block_count": 4,
                    "chapter_shape_issue_count": 0,
                    "broken_image_count": 0,
                    "errors": [],
                },
            }
        )
        self.assertIn("Website bundle status: pass", report)
        self.assertIn("## Story Reader Website", report)

    def test_analyze_site_tree_ignores_query_strings_on_local_assets(self) -> None:
        root = self.make_root()
        site_root = root / "build" / "site"
        (site_root / "assets" / "css").mkdir(parents=True, exist_ok=True)
        (site_root / "assets" / "css" / "app.css").write_text("body{}", encoding="utf-8")
        (site_root / "index.html").write_text(
            '<!doctype html><html><head><link rel="stylesheet" href="assets/css/app.css?v=test"></head><body></body></html>',
            encoding="utf-8",
        )

        result = analyze_site_tree(site_root)
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["missing_local_target_count"], 0)

    def test_build_site_reduces_pages_artifact_by_deduplicating_generated_images(self) -> None:
        root = self.make_root()
        build_site(root)

        site_root = root / "build" / "site"
        website_generated = site_root / "website" / "assets" / "images" / "generated"
        book_generated = site_root / "book" / "assets" / "generated"
        self.assertFalse(website_generated.exists())
        self.assertTrue(book_generated.exists())

    def test_render_book_landing_html_includes_interactive_app_cta(self) -> None:
        root = self.make_root()
        local_html = render_book_landing_html(root, BOOK_INTERACTIVE_APP_LOCAL_HREF)
        published_html = render_book_landing_html(root, BOOK_INTERACTIVE_APP_PUBLISHED_HREF)

        self.assertIn("Choose Your Experience", local_html)
        self.assertIn("You can also scroll down to read specific chapters", local_html)
        self.assertIn("Read the full book", local_html)
        self.assertIn("Download the PDF", local_html)
        self.assertIn("Interactive App", local_html)
        self.assertIn(f'href="{BOOK_INTERACTIVE_APP_LOCAL_HREF}"', local_html)
        self.assertIn(f'href="{BOOK_INTERACTIVE_APP_PUBLISHED_HREF}"', published_html)
        self.assertIn("fonts.googleapis.com/css2?family=Material+Symbols+Rounded", local_html)
        self.assertIn('<a class="experience-button"', local_html)
        self.assertIn('<span class="experience-icon" aria-hidden="true">auto_stories</span>', local_html)
        self.assertIn('<span class="experience-icon" aria-hidden="true">menu_book</span>', local_html)
        self.assertIn('<span class="experience-icon" aria-hidden="true">download</span>', local_html)
        self.assertNotIn('class="button primary"', local_html)
        self.assertNotIn('class="button secondary"', local_html)
        interactive_at = local_html.find("Interactive App")
        read_at = local_html.find("Read the full book")
        download_at = local_html.find("Download the PDF")
        self.assertTrue(-1 not in {interactive_at, read_at, download_at})
        self.assertTrue(interactive_at < read_at < download_at)
        self.assertIn(VIMEO_HERO_EMBED_URL, local_html)
        self.assertIn(VIMEO_HERO_EMBED_URL, local_html)
        header_end = local_html.index("</header>")
        video_at = local_html.index('class="video-hero"')
        hero_at = local_html.index('class="hero"')
        self.assertTrue(header_end < video_at < hero_at)
        card_end = local_html.index("</section>", local_html.index('class="experience-card"'))
        soundcloud_at = local_html.index(SOUNDCLOUD_EMBED_MARKER)
        self.assertTrue(card_end < soundcloud_at)

    def test_render_publication_index_includes_vimeo_row_before_main_heading(self) -> None:
        root = self.make_root()
        (root / "papers").mkdir(parents=True, exist_ok=True)
        (root / "volumes").mkdir(parents=True, exist_ok=True)
        (root / "sources").mkdir(parents=True, exist_ok=True)
        (root / "claims").mkdir(parents=True, exist_ok=True)
        (root / "profiles").mkdir(parents=True, exist_ok=True)
        (root / "timelines").mkdir(parents=True, exist_ok=True)
        (root / "sources" / "catalog.jsonl").write_text("", encoding="utf-8")
        (root / "claims" / "master_claims.jsonl").write_text("", encoding="utf-8")
        (root / "profiles" / "entities.jsonl").write_text("", encoding="utf-8")
        (root / "timelines" / "master_timeline.jsonl").write_text("", encoding="utf-8")
        (root / "papers" / "00_opening-framework_paper.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: "Chapter 00: Opening Framework"
                ---
                """
            ),
            encoding="utf-8",
        )
        (root / "volumes" / "corpus_companion.md").write_text(
            textwrap.dedent(
                """\
                ---
                title: "Corpus Companion"
                ---
                """
            ),
            encoding="utf-8",
        )

        html = render_publication_index(root, base_prefix="", book_index_rel="book/index.html")

        self.assertIn(VIMEO_HERO_EMBED_URL, html)
        self.assertIn(VIMEO_HERO_EMBED_URL, html)
        self.assertIn('href="book/index.html"', html)
        self.assertIn("Chapter 00: Opening Framework", html)
        self.assertIn("Corpus Companion", html)
        header_end = html.index("</header>")
        video_at = html.index('class="video-hero"')
        heading_at = html.index("<h1>AI Empire Research Program</h1>")
        self.assertTrue(header_end < video_at < heading_at)

    def test_render_soundcloud_audio_block_contains_embed_and_credit(self) -> None:
        block = render_soundcloud_audio_block()
        self.assertIn("w.soundcloud.com/player", block)
        self.assertIn(SOUNDCLOUD_EMBED_MARKER, block)
        self.assertNotIn("BRB2ME", block)
        self.assertNotIn("AI Warriros", block)

    def test_inject_soundcloud_into_chapter_html_places_block_before_opening(self) -> None:
        html = textwrap.dedent(
            """\
            <html><body>
            <figure>
            <img src="../assets/generated/covers/00_before-the-machine-could-speak_cover.png" alt="Chapter 00 cover" />
            <figcaption aria-hidden="true">Chapter 00 cover</figcaption>
            </figure>
            <h2 id="opening">Opening</h2>
            <p>Alpha</p>
            </body></html>
            """
        )
        updated = inject_soundcloud_into_chapter_html(html)
        self.assertIn(SOUNDCLOUD_EMBED_MARKER, updated)
        self.assertTrue(updated.index(SOUNDCLOUD_EMBED_MARKER) < updated.index('<h2 id="opening">'))

    def test_inject_soundcloud_into_chapter_html_is_idempotent(self) -> None:
        html = textwrap.dedent(
            """\
            <html><body>
            <figure><figcaption aria-hidden="true">Chapter 00 cover</figcaption></figure>
            <h2 id="opening">Opening</h2>
            </body></html>
            """
        )
        once = inject_soundcloud_into_chapter_html(html)
        twice = inject_soundcloud_into_chapter_html(once)
        self.assertEqual(once.count(SOUNDCLOUD_EMBED_MARKER), 1)
        self.assertEqual(twice.count(SOUNDCLOUD_EMBED_MARKER), 1)

    def test_inject_soundcloud_into_chapter_html_skips_non_chapter_or_missing_opening(self) -> None:
        full_book_like = "<html><body><h1>Preface</h1><p>No opening marker here.</p></body></html>"
        self.assertEqual(inject_soundcloud_into_chapter_html(full_book_like), full_book_like)

    def test_inject_soundcloud_into_full_book_html_places_block_before_preface(self) -> None:
        html = textwrap.dedent(
            """\
            <html><body>
            <figure>
            <img src="../assets/generated/master_cover.png" alt="Book cover" />
            <figcaption aria-hidden="true">Children of the Feed</figcaption>
            </figure>
            <h1 id="preface">Preface</h1>
            <p>Alpha</p>
            </body></html>
            """
        )
        updated = inject_soundcloud_into_full_book_html(html)
        self.assertIn(SOUNDCLOUD_EMBED_MARKER, updated)
        self.assertTrue(updated.index("</figure>") < updated.index(SOUNDCLOUD_EMBED_MARKER))
        self.assertTrue(updated.index(SOUNDCLOUD_EMBED_MARKER) < updated.index('<h1 id="preface">'))

    def test_inject_soundcloud_into_full_book_html_is_idempotent(self) -> None:
        html = textwrap.dedent(
            """\
            <html><body>
            <figure><figcaption aria-hidden="true">Children of the Feed</figcaption></figure>
            <h1 id="preface">Preface</h1>
            </body></html>
            """
        )
        once = inject_soundcloud_into_full_book_html(html)
        twice = inject_soundcloud_into_full_book_html(once)
        self.assertEqual(once.count(SOUNDCLOUD_EMBED_MARKER), 1)
        self.assertEqual(twice.count(SOUNDCLOUD_EMBED_MARKER), 1)

    def test_render_chapter_footer_nav_handles_middle_and_edge_chapters(self) -> None:
        middle_nav = render_chapter_footer_nav("04")
        self.assertIn("Previous", middle_nav)
        self.assertIn("Lockdown and the Great Acceleration", middle_nav)
        self.assertIn("Next", middle_nav)
        self.assertIn("The Layoff Ritual", middle_nav)

        first_nav = render_chapter_footer_nav("00")
        self.assertNotIn("Before the Machine Could Speak</span>", first_nav)
        self.assertIn("The Free Trap", first_nav)
        self.assertIn('chapter-footer-spacer is-previous', first_nav)

        last_nav = render_chapter_footer_nav("10")
        self.assertIn("If No One Acts", last_nav)
        self.assertIn('chapter-footer-spacer is-next', last_nav)
        self.assertNotIn("The Three Reforms</span>", last_nav)

    def test_inject_chapter_footer_nav_places_block_before_body_close_once(self) -> None:
        html = "<html><body><h2 id=\"next\">Next</h2><p>Alpha</p></body></html>"
        once = inject_chapter_footer_nav(html, "04")
        twice = inject_chapter_footer_nav(once, "04")
        self.assertIn(CHAPTER_FOOTER_NAV_MARKER, once)
        self.assertTrue(once.index(CHAPTER_FOOTER_NAV_MARKER) < once.index("</body>"))
        self.assertEqual(once.count(CHAPTER_FOOTER_NAV_MARKER), 1)
        self.assertEqual(twice.count(CHAPTER_FOOTER_NAV_MARKER), 1)

    def test_export_book_refreshes_site_book_assets_and_landing_when_site_exists(self) -> None:
        root = self.make_root()
        site_book_root = root / "build" / "site" / "book"
        site_book_root.mkdir(parents=True, exist_ok=True)
        (site_book_root / "index.html").write_text("stale", encoding="utf-8")

        original_export_markdown_document = __import__("apps.research_cli.research_cli.book", fromlist=["export_markdown_document"]).export_markdown_document

        def fake_export_markdown_document(
            markdown_path: Path,
            tex_root: Path,
            pdf_root: Path,
            processed_root: Path,
            html_root: Path,
            header_path: Path,
            css_path: Path,
            child_env: dict,
            resource_paths: list[str],
            font_size: str,
            build_pdf: bool,
        ) -> None:
            stem = markdown_path.stem
            (tex_root / f"{stem}.tex").write_text("tex", encoding="utf-8")
            chapter_pdf_dir = pdf_root / stem
            chapter_pdf_dir.mkdir(parents=True, exist_ok=True)
            (chapter_pdf_dir / f"{stem}.pdf").write_bytes(b"pdf")
            source_text = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else "# Missing fixture chapter\n"
            (processed_root / markdown_path.name).write_text(source_text, encoding="utf-8")
            if stem == "full_book":
                html = textwrap.dedent(
                    """\
                    <html><body>
                    <figure>
                    <img src="../assets/generated/master_cover.png" alt="Book cover" />
                    <figcaption aria-hidden="true">Children of the Feed</figcaption>
                    </figure>
                    <h1 id="preface">Preface</h1>
                    <p>chapter</p>
                    </body></html>
                    """
                )
            else:
                html = textwrap.dedent(
                    f"""\
                    <html><body>
                    <figure>
                    <img src="../assets/generated/covers/{stem}_cover.png" alt="Chapter cover" />
                    <figcaption aria-hidden="true">Chapter cover</figcaption>
                    </figure>
                    <h2 id="opening">Opening</h2>
                    <p>chapter</p>
                    </body></html>
                    """
                )
            (html_root / f"{stem}.html").write_text(html, encoding="utf-8")

        import apps.research_cli.research_cli.book as book_module

        book_module.export_markdown_document = fake_export_markdown_document
        try:
            export_book(root)
        finally:
            book_module.export_markdown_document = original_export_markdown_document

        self.assertTrue((site_book_root / "assets" / "brand" / "waken-ai-black.webp").exists())
        self.assertTrue((site_book_root / "assets" / "generated" / "master_cover.png").exists())
        site_index = (site_book_root / "index.html").read_text(encoding="utf-8")
        self.assertIn("Interactive App", site_index)
        self.assertIn(f'href="{BOOK_INTERACTIVE_APP_PUBLISHED_HREF}"', site_index)
        self.assertNotEqual(site_index, "stale")
        chapter_html = (site_book_root / "html" / "00_opening-framework.html").read_text(encoding="utf-8")
        self.assertIn(SOUNDCLOUD_EMBED_MARKER, chapter_html)
        self.assertTrue(chapter_html.index(SOUNDCLOUD_EMBED_MARKER) < chapter_html.index('<h2 id="opening">'))
        self.assertIn(CHAPTER_FOOTER_NAV_MARKER, chapter_html)
        self.assertTrue(chapter_html.index(CHAPTER_FOOTER_NAV_MARKER) < chapter_html.index("dedication-coda"))
        self.assertIn("The Free Trap", chapter_html)
        full_book_html = (site_book_root / "html" / "full_book.html").read_text(encoding="utf-8")
        self.assertIn(SOUNDCLOUD_EMBED_MARKER, full_book_html)
        self.assertTrue(full_book_html.index("</figure>") < full_book_html.index(SOUNDCLOUD_EMBED_MARKER))
        self.assertTrue(full_book_html.index(SOUNDCLOUD_EMBED_MARKER) < full_book_html.index('<h1 id="preface">'))
        self.assertNotIn(CHAPTER_FOOTER_NAV_MARKER, full_book_html)

    def test_export_book_repairs_stale_site_book_index(self) -> None:
        root = self.make_root()
        build_site(root)
        site_index_path = root / "build" / "site" / "book" / "index.html"
        site_index_path.write_text("stale", encoding="utf-8")

        original_export_markdown_document = __import__("apps.research_cli.research_cli.book", fromlist=["export_markdown_document"]).export_markdown_document

        def fake_export_markdown_document(
            markdown_path: Path,
            tex_root: Path,
            pdf_root: Path,
            processed_root: Path,
            html_root: Path,
            header_path: Path,
            css_path: Path,
            child_env: dict,
            resource_paths: list[str],
            font_size: str,
            build_pdf: bool,
        ) -> None:
            stem = markdown_path.stem
            (tex_root / f"{stem}.tex").write_text("tex", encoding="utf-8")
            chapter_pdf_dir = pdf_root / stem
            chapter_pdf_dir.mkdir(parents=True, exist_ok=True)
            (chapter_pdf_dir / f"{stem}.pdf").write_bytes(b"pdf")
            source_text = markdown_path.read_text(encoding="utf-8") if markdown_path.exists() else "# Missing fixture chapter\n"
            (processed_root / markdown_path.name).write_text(source_text, encoding="utf-8")
            if stem == "full_book":
                html = textwrap.dedent(
                    """\
                    <html><body>
                    <figure>
                    <img src="../assets/generated/master_cover.png" alt="Book cover" />
                    <figcaption aria-hidden="true">Children of the Feed</figcaption>
                    </figure>
                    <h1 id="preface">Preface</h1>
                    <p>chapter</p>
                    </body></html>
                    """
                )
            else:
                html = textwrap.dedent(
                    f"""\
                    <html><body>
                    <figure>
                    <img src="../assets/generated/covers/{stem}_cover.png" alt="Chapter cover" />
                    <figcaption aria-hidden="true">Chapter cover</figcaption>
                    </figure>
                    <h2 id="opening">Opening</h2>
                    <p>chapter</p>
                    </body></html>
                    """
                )
            (html_root / f"{stem}.html").write_text(html, encoding="utf-8")

        import apps.research_cli.research_cli.book as book_module

        book_module.export_markdown_document = fake_export_markdown_document
        try:
            export_book(root)
        finally:
            book_module.export_markdown_document = original_export_markdown_document

        repaired = site_index_path.read_text(encoding="utf-8")
        self.assertIn("Interactive App", repaired)
        self.assertIn(f'href="{BOOK_INTERACTIVE_APP_PUBLISHED_HREF}"', repaired)
        self.assertNotEqual(repaired, "stale")

    def test_normalize_reader_state_recovers_from_invalid_data(self) -> None:
        normalized = normalize_reader_state({"lastPosition": "bad", "chapterProgress": [], "favorites": "bad"})
        self.assertEqual(normalized["version"], 1)
        self.assertEqual(normalized["lastPosition"], {"chapterIndex": 0, "blockIndex": 0})
        self.assertEqual(normalized["favorites"], [])
        self.assertEqual(normalized["notes"], [])

    def test_update_progress_marks_completion(self) -> None:
        state = default_reader_state()
        update_progress(state, 0, 0, 4, "2026-07-03T12:00:00Z")
        update_progress(state, 0, 3, 4, "2026-07-03T12:01:00Z")
        entry = state["chapterProgress"]["0"]
        self.assertEqual(entry["completedBlocks"], [0, 3])
        self.assertEqual(entry["progressPercent"], 50)
        self.assertTrue(entry["completed"])

    def test_toggle_favorite_toggles_by_block(self) -> None:
        state = default_reader_state()
        toggle_favorite(state, 1, 2, "Alpha", "Saved fragment", "assets/images/alpha.png", "2026-07-03T12:15:00Z")
        self.assertEqual(len(state["favorites"]), 1)
        toggle_favorite(state, 1, 2, "Alpha", "Saved fragment", "assets/images/alpha.png", "2026-07-03T12:16:00Z")
        self.assertEqual(state["favorites"], [])

    def test_get_autoplay_delay_ms_uses_tiered_reading_profiles(self) -> None:
        short_text = "word " * 4
        medium_text = "word " * 24
        long_text = "word " * 200
        self.assertEqual(get_autoplay_delay_ms(short_text), 2200)
        self.assertEqual(get_autoplay_delay_ms(medium_text), 7100)
        self.assertEqual(get_autoplay_delay_ms(long_text), 18000)

    def test_render_js_stops_autoplay_for_modal_and_route_changes(self) -> None:
        js = render_js()
        self.assertIn("function getAutoplayDelay(text)", js)
        self.assertIn("const AUTOPLAY_SHORT_WORDS_MAX =", js)
        self.assertIn("const AUTOPLAY_MEDIUM_WORDS_MAX =", js)
        self.assertIn("let wordsPerMinute = AUTOPLAY_LONG_WORDS_PER_MINUTE;", js)
        self.assertIn("if (route.name !== \"read\") {", js)
        self.assertIn("stopAutoplay();", js)
        self.assertIn("function openNoteDialog(chapterIndex, blockIndex) {", js)
        self.assertIn("renderCurrentRoute();", js)
        self.assertIn("resetAutoplayIndicator();", js)
        self.assertIn("autoplayGeneration += 1;", js)

    def test_render_js_resets_and_stops_autoplay_inside_reader(self) -> None:
        js = render_js()
        self.assertIn("clearAutoplayTimer();", js)
        self.assertIn("scheduleAutoplay(safe.chapterIndex, safe.blockIndex);", js)
        self.assertIn("if (blockIndex >= chapter.blocks.length - 1) {", js)
        self.assertIn("navigateTo(`#/read/${chapterIndex}/${blockIndex + 1}`);", js)
        self.assertIn("startAutoplayIndicator(delay);", js)
        self.assertIn("if (!isAutoplaying || generation !== autoplayGeneration) return;", js)

    def test_render_js_emits_footer_order_and_next_control(self) -> None:
        js = render_js()
        favorite_at = js.find('id="favorite-toggle"')
        note_at = js.find('id="note-toggle"')
        autoplay_at = js.find('id="autoplay-toggle"')
        next_at = js.find('id="next-toggle"')
        self.assertTrue(-1 not in {favorite_at, note_at, autoplay_at, next_at})
        self.assertTrue(favorite_at < note_at < autoplay_at < next_at)
        self.assertIn('aria-label="Next block"', js)
        self.assertNotIn("Tap or swipe to continue", js)
        self.assertIn("advanceReader(safe.chapterIndex, safe.blockIndex, 1, { preserveAutoplay: isAutoplaying });", js)

    def test_render_js_includes_live_reader_fit_hooks(self) -> None:
        js = render_js()
        self.assertIn("function scheduleReaderFit()", js)
        self.assertIn("function bindReaderFitObserver()", js)
        self.assertIn("new ResizeObserver(() => {", js)
        self.assertIn("window.addEventListener(\"orientationchange\"", js)
        self.assertIn("textBody.scrollHeight <= textBody.clientHeight", js)

    def test_render_css_emits_reader_no_scroll_contract(self) -> None:
        css = render_css()
        self.assertIn("html.reader-route,", css)
        self.assertIn("body.reader-route .app-main {", css)
        self.assertIn(".reader-screen {", css)
        self.assertIn("overflow: hidden;", css)
        self.assertIn(".reader-text-body {", css)

    def test_render_css_emits_footer_pacing_and_smaller_controls(self) -> None:
        css = render_css()
        self.assertIn(".reader-autoplay-progress {", css)
        self.assertIn(".reader-autoplay-fill {", css)
        self.assertIn("width: 2.1rem;", css)
        self.assertIn("font-size: 0.98rem;", css)
        self.assertIn("height: min(100%, clamp(22rem, 62vh, 38rem));", css)
        self.assertIn("rgba(3, 5, 9, 0.62)", css)

    def test_render_js_emits_home_links_and_brand_header(self) -> None:
        js = render_js()
        self.assertIn("../book/index.html", js)
        self.assertIn("../papers/html/11_children-of-the-feed-servants-of-the-ai-god_paper.html", js)
        self.assertIn("function renderBrandHeader()", js)
        self.assertIn('href="https://wakenai.com"', js)
        self.assertIn("assets/images/waken-ai-black.webp", js)
        self.assertIn("../assets/brand/waken-ai-black.webp", js)

    def test_upsert_note_edit_and_delete(self) -> None:
        state = default_reader_state()
        upsert_note(
            state,
            0,
            1,
            "Alpha",
            "Block text",
            "First note",
            "assets/images/alpha.png",
            "2026-07-03T12:20:00Z",
        )
        upsert_note(
            state,
            0,
            1,
            "Alpha",
            "Block text",
            "Edited note",
            "assets/images/alpha.png",
            "2026-07-03T12:21:00Z",
        )
        self.assertEqual(len(state["notes"]), 1)
        self.assertEqual(state["notes"][0]["comment"], "Edited note")
        delete_note(state, state["notes"][0]["id"])
        self.assertEqual(state["notes"], [])


if __name__ == "__main__":
    unittest.main()
