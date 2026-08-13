from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import tempfile
import textwrap
import unicodedata
from html import escape
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - runtime fallback for minimal environments
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]

from .constants import CHAPTERS
from .doctrine import (
    WAKENAI_URL,
    copy_brand_logo,
    patrimony_markdown_block,
    render_public_document_header,
    render_public_logo_header,
    render_patimony_html_card,
    render_vimeo_hero_block,
)
from .fs import dump_json, ensure_dir, overwrite, write_if_missing
from .papers import export_markdown_document, paper_stem_for_chapter, render_publication_index
from .website import publish_website_bundle

BOOK_TITLE = "Children of the Feed. Servants of the AI God"
BOOK_SUBTITLE = "How technofeudalism raised us as digital serfs"
BOOK_AUTHOR = "Mark Uriostegui"
BOOK_PUBLISHER = "WakenAI Labs"
BOOK_COPYRIGHT = "Copyright Mark Uriostegui 2026"
BOOK_PRINT_ADAPTATION_LINE = "A trade-book adaptation of the AI Empire research program."
DEDICATION_HEADING = "Ad Magnificam Humanitatem"
DEDICATION_INTRO = "To our beloved:"
BOOK_INTERACTIVE_APP_LOCAL_HREF = "../site/website/index.html"
BOOK_INTERACTIVE_APP_PUBLISHED_HREF = "../website/index.html"
SOUNDCLOUD_EMBED_MARKER = "soundcloud-audio-block"
CHAPTER_FOOTER_NAV_MARKER = "chapter-footer-nav"
DEDICATION_LINES = [
    "אֱנוֹשׁוּת מַפְלִיאָה",
    "महान मानवता",
    "الإنسانية العظيمة",
    "伟大的人类",
    "偉大なる人類",
    "위대한 인류",
    "Magnifica Umanità",
    "Humanité Magnifique",
    "Magnífica Humanidad",
    "Magnífica Humanidade",
    "Großartige Menschheit",
    "Великолепное человечество",
    "Magnificent Humanity",
]
BOOK_BG = "#05080d"
BOOK_PANEL = "#12171f"
BOOK_BONE = "#f6e8c8"
BOOK_MUTED = "#d8c9a4"
BOOK_GOLD = "#ffd166"

FONT_REGULAR_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
]
FONT_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf",
    "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
]

BOOK_CHAPTERS = [
    {
        "id": "00",
        "source_file": "00_opening-framework.md",
        "title": "Before the Machine Could Speak",
        "deck": "The opening wound: how humanity was turned into signal before AI could be sold as destiny.",
        "paper_title": "Chapter 00: Opening Framework",
        "accent": "#ff5e3a",
    },
    {
        "id": "01",
        "source_file": "01_the-free-trap.md",
        "title": "The Free Trap",
        "deck": "How the platforms taught us to confuse participation with payment while they harvested the map of our behavior.",
        "paper_title": "Chapter 01: Social Networks as Infrastructure for Free Data Capture",
        "accent": "#ff6b35",
    },
    {
        "id": "02",
        "source_file": "02_raised-by-the-algorithm.md",
        "title": "Raised by the Algorithm",
        "deck": "A generation did not simply lose attention. Attention was farmed.",
        "paper_title": "Chapter 02: Social Erosion and Moral Reconfiguration",
        "accent": "#d94d2b",
    },
    {
        "id": "03",
        "source_file": "03_lockdown-and-the-great-acceleration.md",
        "title": "Lockdown and the Great Acceleration",
        "deck": "The world went inside. The platforms were waiting.",
        "paper_title": "Chapter 03: COVID as a Historical Accelerator",
        "accent": "#f59e0b",
    },
    {
        "id": "04",
        "source_file": "04_we-were-the-dataset.md",
        "title": "We Were the Dataset",
        "deck": "First they captured what we made. Then they captured how we think.",
        "paper_title": "Chapter 04: AI Arrives When the Human Raw Material Already Exists",
        "accent": "#ff4d4f",
    },
    {
        "id": "05",
        "source_file": "05_the-layoff-ritual.md",
        "title": "The Layoff Ritual",
        "deck": "The machine did not only learn from workers. It was used to discipline them.",
        "paper_title": "Chapter 05: Talent, Overhiring, Valuation, and Layoffs",
        "accent": "#c2410c",
    },
    {
        "id": "06",
        "source_file": "06_the-dual-use-gospel.md",
        "title": "The Dual-Use Gospel",
        "deck": "How the same system is sold as miracle, weapon, tutor, oracle, and dependency engine.",
        "paper_title": "Chapter 06: AI as a Dual-Use Rhetorical Weapon",
        "accent": "#ef4444",
    },
    {
        "id": "07",
        "source_file": "07_the-gates-of-intelligence.md",
        "title": "The Gates of Intelligence",
        "deck": "Compute, export controls, and defense alignments decide who may approach the new oracle.",
        "paper_title": "Chapter 07: Imperial Control Over Access",
        "accent": "#eab308",
    },
    {
        "id": "08",
        "source_file": "08_the-legitimacy-machine.md",
        "title": "The Legitimacy Machine",
        "deck": "The empire does not survive by code alone. It survives by praise, access, prestige, and institutional blessing.",
        "paper_title": "Chapter 08: Power Network, Legitimacy, and Institutional Capture",
        "accent": "#f97316",
    },
    {
        "id": "09",
        "source_file": "09_if-no-one-acts.md",
        "title": "If No One Acts",
        "deck": "What comes next if dependence, enclosure, and state-corporate fusion harden into infrastructure.",
        "paper_title": "Chapter 09: Future if No Action Is Taken",
        "accent": "#facc15",
    },
    {
        "id": "10",
        "source_file": "10_the-three-reforms.md",
        "title": "The Three Reforms",
        "deck": "The response is no longer a mood. It is a program.",
        "paper_title": "Chapter 10: What To Do",
        "accent": "#ffd166",
    },
]


def slugify(value: str) -> str:
    ascii_value = value.encode("ascii", "ignore").decode("ascii")
    normalized = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower())
    return normalized.strip("-")


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
        data[key.strip()] = value.strip().strip('"')
    return data


def strip_frontmatter(content: str) -> str:
    if not content.startswith("---\n"):
        return content
    _, remainder = content.split("---\n", 1)
    _, _, body = remainder.partition("\n---\n")
    return body.lstrip()


def chapter_entry(chapter_id: str) -> dict:
    for entry in BOOK_CHAPTERS:
        if entry["id"] == chapter_id:
            return entry
    raise KeyError(f"Unknown book chapter id: {chapter_id}")


def chapter_markdown_path(root: Path, chapter_id: str) -> Path:
    return root / "book" / "chapters" / chapter_entry(chapter_id)["source_file"]


def chapter_markdown_paths(root: Path) -> list[Path]:
    return [chapter_markdown_path(root, entry["id"]) for entry in BOOK_CHAPTERS]


def chapter_output_stem(chapter_id: str) -> str:
    entry = chapter_entry(chapter_id)
    return f"{chapter_id}_{slugify(entry['title'])}"


def chapter_document_stem(chapter_id: str) -> str:
    return Path(chapter_entry(chapter_id)["source_file"]).stem


def chapter_entry_for_document_stem(document_stem: str) -> dict:
    for entry in BOOK_CHAPTERS:
        if chapter_document_stem(entry["id"]) == document_stem:
            return entry
    raise KeyError(f"Unknown chapter document stem: {document_stem}")


def chapter_paper_link_text(root: Path, chapter_id: str) -> str:
    paper_stem = paper_stem_for_chapter(root, chapter_id)
    chapter = chapter_entry(chapter_id)
    html_stem = paper_stem if paper_stem.endswith("_paper") else f"{paper_stem}_paper"
    html_link = f"../../papers/html/{html_stem}.html"
    pdf_link = f"../../papers/pdf/{html_stem}/{html_stem}.pdf"
    return f"[{chapter['paper_title']}]({html_link}) ([PDF]({pdf_link}))"


def ensure_pillow() -> None:
    if Image is None or ImageDraw is None or ImageFont is None:
        raise RuntimeError(
            "Pillow is required for the literary asset pipeline. Install `pillow` in the active Python "
            "environment or run the book build from an environment that already includes it."
        )


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    ensure_pillow()
    candidates = FONT_BOLD_CANDIDATES if bold else FONT_REGULAR_CANDIDATES
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _draw_vertical_gradient(draw: ImageDraw.ImageDraw, width: int, height: int, top_hex: str, bottom_hex: str) -> None:
    top = _hex_to_rgb(top_hex)
    bottom = _hex_to_rgb(bottom_hex)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line((0, y, width, y), fill=color)


def _draw_glow(image: Image.Image, center: tuple[int, int], radius: int, color_hex: str, alpha: int) -> None:
    ensure_pillow()
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(overlay)
    r, g, b = _hex_to_rgb(color_hex)
    for step in range(radius, 0, -20):
        opacity = int(alpha * (step / radius) ** 2)
        glow_draw.ellipse(
            (center[0] - step, center[1] - step, center[0] + step, center[1] + step),
            fill=(r, g, b, opacity),
        )
    image.alpha_composite(overlay)


def _wrapped_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> str:
    ensure_pillow()
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "\n".join(lines)


def render_chapter_cover_png(entry: dict) -> Image.Image:
    ensure_pillow()
    width, height = 1600, 900
    image = Image.new("RGBA", (width, height), BOOK_BG)
    draw = ImageDraw.Draw(image)
    _draw_vertical_gradient(draw, width, height, "#05080d", "#12171f")
    _draw_glow(image, (800, 230), 260, entry["accent"], 115)
    draw = ImageDraw.Draw(image)

    accent = entry["accent"]
    bone = _hex_to_rgb(BOOK_BONE)
    gold = _hex_to_rgb(BOOK_GOLD)
    ember = _hex_to_rgb(accent)

    for x in (120, 320, 1280, 1480):
        draw.line((x, 120, x, 820), fill=(*ember, 42), width=2)
    for y in (180, 700):
        draw.line((120, y, 1480, y), fill=(*ember, 38), width=2)

    draw.ellipse((625, 75, 975, 425), outline=(*ember, 95), width=4)
    draw.ellipse((690, 140, 910, 360), outline=(*gold, 115), width=3)
    draw.ellipse((760, 210, 840, 290), fill=(*ember, 205))

    font_eyebrow = _load_font(34, bold=False)
    font_chapter = _load_font(98, bold=True)
    font_title = _load_font(86, bold=True)
    font_deck = _load_font(34, bold=False)
    font_banner = _load_font(42, bold=True)

    draw.text((120, 105), "CHILDREN OF THE FEED", fill=bone, font=font_eyebrow)
    draw.text((120, 170), f"Chapter {entry['id']}", fill=ember, font=font_chapter)
    draw.text((120, 330), entry["title"], fill=bone, font=font_title)

    wrapped_deck = _wrapped_text(draw, entry["deck"], font_deck, 980)
    draw.multiline_text((120, 430), wrapped_deck, fill=(229, 220, 200), font=font_deck, spacing=10)

    draw.rounded_rectangle((120, 670, 1140, 762), radius=14, fill=(8, 12, 18, 220), outline=(*ember, 220), width=3)
    draw.text((160, 700), "How technofeudalism raised us as digital serfs", fill=gold, font=font_banner)
    return image.convert("RGB")


def _draw_chart_card(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    outline_hex: str,
    lines: list[str],
) -> None:
    ensure_pillow()
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=24, fill=(19, 28, 39), outline=_hex_to_rgb(outline_hex), width=4)
    font = _load_font(34, bold=True)
    line_height = 40
    total_height = len(lines) * line_height
    start_y = y0 + ((y1 - y0) - total_height) // 2 - 6
    for index, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_x = x0 + ((x1 - x0) - (bbox[2] - bbox[0])) // 2
        draw.text((text_x, start_y + index * line_height), line, fill=_hex_to_rgb(BOOK_BONE), font=font)


def render_platform_harvest_chart_png() -> Image.Image:
    ensure_pillow()
    width, height = 1400, 800
    image = Image.new("RGB", (width, height), "#071018")
    draw = ImageDraw.Draw(image)
    _draw_vertical_gradient(draw, width, height, "#071018", "#101722")
    title_font = _load_font(54, bold=True)
    body_font = _load_font(28, bold=False)
    small_font = _load_font(26, bold=False)
    draw.text((80, 90), "From free connection to model power", fill=_hex_to_rgb(BOOK_BONE), font=title_font)
    draw.text(
        (80, 140),
        "A simplified visual of the extraction chain described across Chapters 01, 04, 05, and 06.",
        fill=_hex_to_rgb(BOOK_MUTED),
        font=body_font,
    )
    cards = [
        ((90, 250, 320, 390), "#f97316", ["Free social", "participation"]),
        ((410, 250, 640, 390), "#ef4444", ["Behavioral", "capture"]),
        ((730, 250, 960, 390), "#eab308", ["Training and", "licensing"]),
        ((1050, 250, 1280, 390), "#ffd166", ["Private", "model power"]),
    ]
    for bounds, accent, lines in cards:
        _draw_chart_card(draw, bounds, accent, lines)
    for start, end in ((320, 410), (640, 730), (960, 1050)):
        draw.line((start, 320, end, 320), fill=_hex_to_rgb("#f5d98e"), width=6)
    descriptions = [
        (90, ["Users are told the service is free.", "The real payment is attention, identity, and trace behavior."]),
        (410, ["Platforms persist, combine, and monetize expression.", "The behavioral map becomes a corporate asset."]),
        (730, ["Captured expression is scraped, filtered, labeled, or licensed.", "Weights condense the archive into strategic capability."]),
        (1050, ["The result is sold back as intelligence, efficiency, and inevitability.", "The harvest returns as dependency."]),
    ]
    for x, lines in descriptions:
        y = 505
        for line in lines:
            draw.text((x, y), line, fill=(213, 217, 223), font=small_font)
            y += 40
    return image


def render_dependency_timeline_chart_png() -> Image.Image:
    ensure_pillow()
    width, height = 1400, 980
    image = Image.new("RGB", (width, height), "#071018")
    draw = ImageDraw.Draw(image)
    _draw_vertical_gradient(draw, width, height, "#071018", "#101722")
    title_font = _load_font(54, bold=True)
    body_font = _load_font(28, bold=False)
    year_font = _load_font(34, bold=True)
    small_font = _load_font(24, bold=False)
    draw.text((80, 90), "Dependency acceleration", fill=_hex_to_rgb(BOOK_BONE), font=title_font)
    draw.text(
        (80, 140),
        "A narrative timeline connecting the feed era, lockdown intensification, and the rise of frontier AI.",
        fill=_hex_to_rgb(BOOK_MUTED),
        font=body_font,
    )
    draw.line((120, 470, 1280, 470), fill=_hex_to_rgb("#f5d98e"), width=5)
    points = [
        (220, "#ff6b35", "2008-2014", ["Platforms become daily territory.", "Identity migrates into the feed."]),
        (510, "#ef4444", "2015-2019", ["Recommendation systems harden.", "The behavioral archive deepens."]),
        (800, "#f59e0b", "2020-2021", ["Lockdown pushes school, work,", "desire, and politics into screens."]),
        (1090, "#ffd166", "2022-2026", ["Frontier AI monetizes the archive.", "Access becomes stratified."]),
    ]
    for x, color, years, lines in points:
        draw.ellipse((x - 18, 470 - 18, x + 18, 470 + 18), fill=_hex_to_rgb(color))
        draw.text((x - 70, 390), years, fill=_hex_to_rgb(BOOK_BONE), font=year_font)
        card = (x - 150, 560, x + 150, 690)
        draw.rounded_rectangle(card, radius=18, fill=(18, 25, 36), outline=_hex_to_rgb(color), width=3)
        for idx, line in enumerate(lines):
            draw.text((x - 126, 602 + idx * 34), line, fill=(226, 228, 231), font=small_font)
    curve_points = [(220, 470), (350, 360), (510, 470), (650, 590), (800, 470), (945, 310), (1090, 470)]
    draw.line(curve_points, fill=_hex_to_rgb("#ff7b5a"), width=7, joint="curve")
    draw.text(
        (114, 820),
        "The point is not that one event explains everything. It is that each stage enlarged the archive and made mediated life feel more normal.",
        fill=_hex_to_rgb(BOOK_MUTED),
        font=small_font,
    )
    return image


def render_empire_stack_chart_png() -> Image.Image:
    ensure_pillow()
    width, height = 1400, 860
    image = Image.new("RGB", (width, height), "#071018")
    draw = ImageDraw.Draw(image)
    _draw_vertical_gradient(draw, width, height, "#071018", "#101722")
    title_font = _load_font(54, bold=True)
    body_font = _load_font(28, bold=False)
    bar_font = _load_font(40, bold=True)
    small_font = _load_font(25, bold=False)
    draw.text((80, 90), "The AI empire stack", fill=_hex_to_rgb(BOOK_BONE), font=title_font)
    draw.text(
        (80, 140),
        "A simplified structural map of the dossier's argument from feed to capture to strategic access.",
        fill=_hex_to_rgb(BOOK_MUTED),
        font=body_font,
    )
    bars = [
        ((280, 640, 1120, 730), "#ff6b35", "Feed territory and behavioral capture"),
        ((340, 510, 1060, 600), "#ef4444", "Training, licensing, and weight enclosure"),
        ((400, 380, 1000, 470), "#f59e0b", "Labor discipline and AI inevitability"),
        ((460, 250, 940, 340), "#eab308", "Compute, export, and defense access"),
        ((520, 120, 880, 210), "#ffd166", "Legitimacy and capture"),
    ]
    for (x0, y0, x1, y1), outline_hex, text in bars:
        draw.rounded_rectangle((x0, y0, x1, y1), radius=20, fill=(21, 29, 40), outline=_hex_to_rgb(outline_hex), width=4)
        bbox = draw.textbbox((0, 0), text, font=bar_font)
        text_x = x0 + ((x1 - x0) - (bbox[2] - bbox[0])) // 2
        text_y = y0 + ((y1 - y0) - (bbox[3] - bbox[1])) // 2 - 6
        draw.text((text_x, text_y), text, fill=_hex_to_rgb(BOOK_BONE), font=bar_font)
    draw.text(
        (110, 760),
        "The higher the stack rises, the more power is hidden behind inevitability, prestige, and privileged access.",
        fill=(213, 217, 223),
        font=small_font,
    )
    return image


def prompt_anchor(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    lowered = normalized.lower().replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")


def prompt_catalog_for_markdown(markdown_path: Path) -> dict[str, str]:
    content = markdown_path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^(#{2,6})\s+(.+)$", content, re.M))
    catalog: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(2).strip()
        section_start = match.end()
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        section = content[section_start:section_end]
        prompt_match = re.search(r"`([^`]+)`", section, re.S)
        if prompt_match:
            catalog[prompt_anchor(heading)] = prompt_match.group(1).strip()
    return catalog


def load_prompt_for_ref(root: Path, prompt_ref: str, cache: dict[str, dict[str, str]]) -> str:
    path_text, anchor = prompt_ref.split("#", 1)
    if path_text not in cache:
        cache[path_text] = prompt_catalog_for_markdown(root / path_text)
    prompt = cache[path_text].get(anchor)
    if not prompt:
        raise KeyError(f"Prompt reference not found: {prompt_ref}")
    return prompt


def load_asset_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "book" / "assets" / "asset_manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def save_asset_manifest(root: Path, manifest: dict[str, Any]) -> None:
    dump_json(root / "book" / "assets" / "asset_manifest.json", manifest)


def selected_book_assets(
    manifest: dict[str, Any],
    kind: str,
    chapter: str | None = None,
    asset_id: str | None = None,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for entry in manifest.get("entries", []):
        if kind == "infographics" and entry.get("kind") != "infographic":
            continue
        if chapter and entry.get("chapter") != chapter:
            continue
        if asset_id and entry.get("asset_id") != asset_id:
            continue
        if entry.get("status") == "retired-for-book":
            continue
        selected.append(entry)
    return selected


def build_generation_bundle(
    root: Path,
    kind: str,
    chapter: str | None = None,
    asset_id: str | None = None,
) -> dict[str, Any]:
    manifest = load_asset_manifest(root)
    prompt_cache: dict[str, dict[str, str]] = {}
    assets = selected_book_assets(manifest, kind=kind, chapter=chapter, asset_id=asset_id)
    requests: list[dict[str, Any]] = []
    for entry in assets:
        prompt_ref = entry.get("prompt_ref")
        if not prompt_ref:
            continue
        requests.append(
            {
                "asset_id": entry["asset_id"],
                "chapter": entry.get("chapter"),
                "kind": entry.get("kind"),
                "model": entry.get("model", "gpt-image-2"),
                "path": entry["path"],
                "prompt_ref": prompt_ref,
                "prompt": load_prompt_for_ref(root, prompt_ref, prompt_cache),
                "aspect_ratio": "16:9",
                "notes": entry.get("notes", ""),
            }
        )
    return {
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "kind": kind,
        "chapter": chapter,
        "asset_id": asset_id,
        "count": len(requests),
        "requests": requests,
    }


def sync_generated_asset_timestamps(root: Path, entries: list[dict[str, Any]]) -> None:
    manifest = load_asset_manifest(root)
    manifest_entries = {entry["asset_id"]: entry for entry in manifest.get("entries", [])}
    changed = False
    for entry in entries:
        asset_path = root / entry["path"]
        if not asset_path.exists():
            continue
        generated_at = dt.datetime.fromtimestamp(asset_path.stat().st_mtime, tz=dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        manifest_entry = manifest_entries.get(entry["asset_id"])
        if manifest_entry is not None and manifest_entry.get("generated_at") != generated_at:
            manifest_entry["generated_at"] = generated_at
            changed = True
    if changed:
        save_asset_manifest(root, manifest)


def generate_book_assets(
    root: Path,
    kind: str,
    chapter: str | None = None,
    asset_id: str | None = None,
) -> Path:
    requests_root = root / "book" / "assets" / "generated" / "requests"
    ensure_dir(requests_root)
    bundle = build_generation_bundle(root, kind=kind, chapter=chapter, asset_id=asset_id)
    target_name = kind
    if chapter:
        target_name += f"_{chapter}"
    if asset_id:
        target_name += f"_{asset_id}"
    bundle_path = requests_root / f"{slugify(target_name)}.json"
    dump_json(bundle_path, bundle)
    sync_generated_asset_timestamps(root, bundle["requests"])
    return bundle_path


def write_book_brand_assets(root: Path) -> None:
    ensure_pillow()
    covers_root = root / "book" / "assets" / "generated" / "covers"
    ensure_dir(covers_root)

    for entry in BOOK_CHAPTERS:
        cover_svg_path = covers_root / f"{chapter_output_stem(entry['id'])}_cover.svg"
        cover_png_path = covers_root / f"{chapter_output_stem(entry['id'])}_cover.png"
        if not cover_svg_path.exists():
            overwrite(cover_svg_path, render_chapter_cover_svg(entry))
        if not cover_png_path.exists():
            render_chapter_cover_png(entry).save(cover_png_path, format="PNG")


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
              top: "0.45in",
              right: "0.45in",
              bottom: "0.55in",
              left: "0.45in",
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


def render_chapter_cover_svg(entry: dict) -> str:
    chapter_number = entry["id"]
    title = escape(entry["title"])
    deck = escape(entry["deck"])
    accent = entry["accent"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" role="img" aria-labelledby="title desc">
  <title id="title">{title}</title>
  <desc id="desc">{deck}</desc>
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#05080d"/>
      <stop offset="55%" stop-color="#10151f"/>
      <stop offset="100%" stop-color="#050608"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="28%" r="45%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.55"/>
      <stop offset="55%" stop-color="{accent}" stop-opacity="0.14"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="metal" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#f8e7bf"/>
      <stop offset="55%" stop-color="#d1a84d"/>
      <stop offset="100%" stop-color="#fff0c7"/>
    </linearGradient>
  </defs>
  <rect width="1600" height="900" fill="url(#bg)"/>
  <rect width="1600" height="900" fill="url(#glow)"/>
  <g opacity="0.2">
    <circle cx="800" cy="250" r="175" fill="none" stroke="{accent}" stroke-width="2"/>
    <circle cx="800" cy="250" r="120" fill="none" stroke="#f8e7bf" stroke-width="1.5"/>
    <path d="M620 250c80-70 280-70 360 0-80 70-280 70-360 0Z" fill="none" stroke="#f8e7bf" stroke-width="2"/>
    <circle cx="800" cy="250" r="38" fill="{accent}" opacity="0.85"/>
  </g>
  <g opacity="0.16" stroke="{accent}" stroke-width="1.2">
    <path d="M120 820V120M320 840V150M1280 820V120M1480 840V150"/>
    <path d="M120 180H1480M100 700H1500"/>
  </g>
  <g>
    <text x="120" y="120" fill="#f8e7bf" font-size="34" font-family="Helvetica, Arial, sans-serif" letter-spacing="5">CHILDREN OF THE FEED</text>
    <text x="120" y="175" fill="{accent}" font-size="100" font-weight="700" font-family="Helvetica, Arial, sans-serif">Chapter {chapter_number}</text>
    <text x="120" y="350" fill="#f5f1e6" font-size="98" font-weight="800" font-family="Helvetica, Arial, sans-serif">{title}</text>
    <foreignObject x="120" y="400" width="1050" height="180">
      <div xmlns="http://www.w3.org/1999/xhtml" style="font-family: Helvetica, Arial, sans-serif; font-size: 34px; line-height: 1.35; color: #e5dcc8; max-width: 1000px;">
        {deck}
      </div>
    </foreignObject>
    <rect x="120" y="670" width="1020" height="92" rx="14" fill="rgba(8,12,18,0.82)" stroke="{accent}" stroke-width="2"/>
    <text x="160" y="728" fill="url(#metal)" font-size="44" font-weight="700" font-family="Helvetica, Arial, sans-serif">How technofeudalism raised us as digital serfs</text>
  </g>
</svg>
"""


def render_platform_harvest_chart() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="800" viewBox="0 0 1400 800">
  <rect width="1400" height="800" fill="#071018"/>
  <text x="80" y="90" fill="#f7e7c6" font-size="54" font-weight="700" font-family="Helvetica, Arial, sans-serif">From free connection to model power</text>
  <text x="80" y="140" fill="#d8c9a4" font-size="28" font-family="Helvetica, Arial, sans-serif">A simplified visual of the extraction chain described across Chapters 01, 04, 05, and 06.</text>
  <g font-family="Helvetica, Arial, sans-serif" font-size="34" font-weight="700">
    <rect x="90" y="250" width="230" height="140" rx="20" fill="#131c27" stroke="#f97316" stroke-width="3"/>
    <text x="205" y="310" fill="#fff4da" text-anchor="middle">Free social</text>
    <text x="205" y="350" fill="#fff4da" text-anchor="middle">participation</text>
    <rect x="410" y="250" width="230" height="140" rx="20" fill="#131c27" stroke="#ef4444" stroke-width="3"/>
    <text x="525" y="310" fill="#fff4da" text-anchor="middle">Behavioral</text>
    <text x="525" y="350" fill="#fff4da" text-anchor="middle">capture</text>
    <rect x="730" y="250" width="230" height="140" rx="20" fill="#131c27" stroke="#eab308" stroke-width="3"/>
    <text x="845" y="310" fill="#fff4da" text-anchor="middle">Training and</text>
    <text x="845" y="350" fill="#fff4da" text-anchor="middle">licensing</text>
    <rect x="1050" y="250" width="230" height="140" rx="20" fill="#131c27" stroke="#ffd166" stroke-width="3"/>
    <text x="1165" y="310" fill="#fff4da" text-anchor="middle">Private</text>
    <text x="1165" y="350" fill="#fff4da" text-anchor="middle">model power</text>
  </g>
  <g stroke="#f5d98e" stroke-width="6" fill="none" stroke-linecap="round">
    <path d="M320 320H410"/>
    <path d="M640 320H730"/>
    <path d="M960 320H1050"/>
  </g>
  <g font-family="Helvetica, Arial, sans-serif" font-size="26" fill="#d5d9df">
    <text x="90" y="505">Users are told the service is free.</text>
    <text x="90" y="545">The real payment is attention, identity, and trace behavior.</text>
    <text x="410" y="505">Platforms persist, combine, and monetize expression.</text>
    <text x="410" y="545">The behavioral map becomes a corporate asset.</text>
    <text x="730" y="505">Captured expression is scraped, filtered, labeled, or licensed.</text>
    <text x="730" y="545">Weights condense the archive into strategic capability.</text>
    <text x="1050" y="505">The result is sold back as intelligence, efficiency, and inevitability.</text>
    <text x="1050" y="545">The harvest returns as dependency.</text>
  </g>
</svg>
"""


def render_dependency_timeline_chart() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="980" viewBox="0 0 1400 980">
  <rect width="1400" height="980" fill="#071018"/>
  <text x="80" y="90" fill="#f7e7c6" font-size="54" font-weight="700" font-family="Helvetica, Arial, sans-serif">Dependency acceleration</text>
  <text x="80" y="140" fill="#d8c9a4" font-size="28" font-family="Helvetica, Arial, sans-serif">A narrative timeline connecting the feed era, lockdown intensification, and the rise of frontier AI.</text>
  <line x1="120" y1="470" x2="1280" y2="470" stroke="#f5d98e" stroke-width="5"/>
  <g font-family="Helvetica, Arial, sans-serif">
    <g>
      <circle cx="220" cy="470" r="18" fill="#ff6b35"/>
      <text x="170" y="390" fill="#fff4da" font-size="34" font-weight="700">2008–2014</text>
      <rect x="70" y="560" width="300" height="130" rx="18" fill="#121924" stroke="#ff6b35" stroke-width="3"/>
      <text x="94" y="606" fill="#e2e4e7" font-size="24">Platforms become daily territory.</text>
      <text x="94" y="640" fill="#e2e4e7" font-size="24">Identity migrates into the feed.</text>
    </g>
    <g>
      <circle cx="510" cy="470" r="18" fill="#ef4444"/>
      <text x="465" y="390" fill="#fff4da" font-size="34" font-weight="700">2015–2019</text>
      <rect x="360" y="560" width="300" height="130" rx="18" fill="#121924" stroke="#ef4444" stroke-width="3"/>
      <text x="384" y="606" fill="#e2e4e7" font-size="24">Recommendation systems harden.</text>
      <text x="384" y="640" fill="#e2e4e7" font-size="24">The behavioral archive deepens.</text>
    </g>
    <g>
      <circle cx="800" cy="470" r="18" fill="#f59e0b"/>
      <text x="760" y="390" fill="#fff4da" font-size="34" font-weight="700">2020–2021</text>
      <rect x="650" y="560" width="300" height="130" rx="18" fill="#121924" stroke="#f59e0b" stroke-width="3"/>
      <text x="674" y="606" fill="#e2e4e7" font-size="24">Lockdown pushes school, work,</text>
      <text x="674" y="640" fill="#e2e4e7" font-size="24">desire, and politics into screens.</text>
    </g>
    <g>
      <circle cx="1090" cy="470" r="18" fill="#ffd166"/>
      <text x="1048" y="390" fill="#fff4da" font-size="34" font-weight="700">2022–2026</text>
      <rect x="940" y="560" width="300" height="130" rx="18" fill="#121924" stroke="#ffd166" stroke-width="3"/>
      <text x="964" y="606" fill="#e2e4e7" font-size="24">Frontier AI monetizes the archive.</text>
      <text x="964" y="640" fill="#e2e4e7" font-size="24">Access becomes stratified.</text>
    </g>
  </g>
  <path d="M220 470C340 360 430 340 510 470S690 590 800 470 970 300 1090 470" fill="none" stroke="#ff7b5a" stroke-width="7" opacity="0.85"/>
  <text x="114" y="820" fill="#d8c9a4" font-size="26" font-family="Helvetica, Arial, sans-serif">The point is not that one event explains everything. It is that each stage enlarged the archive and made mediated life feel more normal.</text>
</svg>
"""


def render_empire_stack_chart() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="860" viewBox="0 0 1400 860">
  <rect width="1400" height="860" fill="#071018"/>
  <text x="80" y="90" fill="#f7e7c6" font-size="54" font-weight="700" font-family="Helvetica, Arial, sans-serif">The AI empire stack</text>
  <text x="80" y="140" fill="#d8c9a4" font-size="28" font-family="Helvetica, Arial, sans-serif">A simplified structural map of the dossier’s argument from feed to capture to strategic access.</text>
  <g font-family="Helvetica, Arial, sans-serif" font-weight="700">
    <rect x="280" y="640" width="840" height="90" rx="20" fill="#151d28" stroke="#ff6b35" stroke-width="3"/>
    <text x="700" y="695" fill="#fff4da" font-size="40" text-anchor="middle">Feed territory and behavioral capture</text>
    <rect x="340" y="510" width="720" height="90" rx="20" fill="#151d28" stroke="#ef4444" stroke-width="3"/>
    <text x="700" y="565" fill="#fff4da" font-size="40" text-anchor="middle">Training, licensing, and weight enclosure</text>
    <rect x="400" y="380" width="600" height="90" rx="20" fill="#151d28" stroke="#f59e0b" stroke-width="3"/>
    <text x="700" y="435" fill="#fff4da" font-size="40" text-anchor="middle">Labor discipline and AI inevitability</text>
    <rect x="460" y="250" width="480" height="90" rx="20" fill="#151d28" stroke="#eab308" stroke-width="3"/>
    <text x="700" y="305" fill="#fff4da" font-size="40" text-anchor="middle">Compute, export, and defense access</text>
    <rect x="520" y="120" width="360" height="90" rx="20" fill="#151d28" stroke="#ffd166" stroke-width="3"/>
    <text x="700" y="175" fill="#fff4da" font-size="40" text-anchor="middle">Legitimacy and capture</text>
  </g>
  <g fill="#d5d9df" font-size="25" font-family="Helvetica, Arial, sans-serif">
    <text x="110" y="760">The higher the stack rises, the more power is hidden behind inevitability, prestige, and privileged access.</text>
  </g>
</svg>
"""


def ensure_book_scaffolds(root: Path) -> None:
    for path in [
        root / "book",
        root / "book" / "chapters",
        root / "book" / "assets" / "generated" / "covers",
        root / "book" / "assets" / "generated" / "illustrations",
        root / "book" / "assets" / "charts",
        root / "book" / "assets" / "prompts",
        root / "book" / "style",
    ]:
        ensure_dir(path)

    write_book_brand_assets(root)
    write_if_missing(root / "book" / "full_book.md", build_full_book_markdown(root))


def chapter_body_markdown(root: Path, chapter_id: str) -> str:
    content = chapter_markdown_path(root, chapter_id).read_text(encoding="utf-8")
    return strip_frontmatter(content).strip()


def build_full_book_markdown(root: Path) -> str:
    preface_path = root / "book" / "index.md"
    preface_body = strip_frontmatter(preface_path.read_text(encoding="utf-8")).strip() if preface_path.exists() else ""
    chapters = [chapter_body_markdown(root, entry["id"]) for entry in BOOK_CHAPTERS if chapter_markdown_path(root, entry["id"]).exists()]
    reading_map_lines = []
    for entry in BOOK_CHAPTERS:
        reading_map_lines.append(
            f"- {entry['title']} -> {chapter_paper_link_text(root, entry['id'])}"
        )

    parts = [
        "---",
        f'title: "{BOOK_TITLE}"',
        f'subtitle: "{BOOK_SUBTITLE}"',
        f'author: "{BOOK_AUTHOR}"',
        'date: ""',
        "lang: en-US",
        "---",
        "",
        f"![{BOOK_TITLE}](../assets/generated/master_cover.png)",
        "",
        "# Preface",
        "",
        preface_body,
        "",
        patrimony_markdown_block().strip(),
        "",
        "\n\n".join(chapters),
        "",
        "## Method and Evidence Note",
        "",
        "This literary edition is a public-facing adaptation of the AI Empire research program. It simplifies the scholarly apparatus without weakening the distinction between documented fact, disputed fact, and bounded interpretation. Readers who want the full documentary burden should move from each chapter's research-basis note into the corresponding standalone paper and then into the omnibus and corpus companion.",
        "",
        "## Chapter-to-Paper Reading Map",
        "",
        "\n".join(reading_map_lines),
        "",
        "## Image and Design Note",
        "",
        "The literary edition uses a magazine-style visual language and a mixed asset system: dramatic chapter-cover art, richer infographic charts, a provided master cover, and selected GPT Image 2 narrative illustrations.",
        "",
    ]
    return "\n".join(parts).rstrip() + "\n"


def render_literary_dedication_block_html() -> str:
    lines = "\n".join(f"      <li>{escape(line)}</li>" for line in DEDICATION_LINES)
    return "\n".join(
        [
            '  <section class="dedication-coda" aria-label="Dedication and imprint">',
            f"    <p class=\"dedication-heading\">{escape(DEDICATION_INTRO)}</p>",
            "    <ul class=\"dedication-list\">",
            lines,
            "    </ul>",
            f'    <p class="dedication-imprint"><a href="{escape(WAKENAI_URL)}">{escape(BOOK_PUBLISHER)}</a></p>',
            f"    <p class=\"dedication-imprint\">{escape(BOOK_COPYRIGHT)}</p>",
            "  </section>",
        ]
    )


def append_literary_dedication_block(html: str) -> str:
    if "public-doc-header" not in html and "public-brand-header" not in html:
        header_block = render_public_document_header(
            "../assets/brand/waken-ai-black.webp",
            home_href="../index.html",
            home_label="Return to book index",
        )
        html = html.replace("<body>", "<body>\n" + header_block, 1)
    block = render_literary_dedication_block_html()
    if "dedication-coda" in html:
        return html
    return html.replace("</body>", block + "\n</body>")


def render_soundcloud_audio_block() -> str:
    return "\n".join(
        [
            f'  <section class="audio-block {SOUNDCLOUD_EMBED_MARKER}" aria-label="Featured track">',
            '    <iframe width="100%" height="166" scrolling="no" frameborder="no" allow="autoplay; encrypted-media" src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/soundcloud%253Atracks%253A2349608588&color=%23ff5500&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true"></iframe>',
            "  </section>",
        ]
    )


def inject_soundcloud_into_chapter_html(html: str) -> str:
    if SOUNDCLOUD_EMBED_MARKER in html:
        return html
    opening_match = re.search(r'<h2 id="opening">', html)
    if not opening_match:
        return html
    figure_matches = list(re.finditer(r"</figure>", html))
    if not figure_matches:
        return html
    cover_figure_end = None
    for figure_match in figure_matches:
        if figure_match.end() <= opening_match.start():
            cover_figure_end = figure_match.end()
        else:
            break
    if cover_figure_end is None:
        return html
    block = "\n" + render_soundcloud_audio_block()
    return html[:cover_figure_end] + block + html[cover_figure_end:]


def inject_soundcloud_into_full_book_html(html: str) -> str:
    if SOUNDCLOUD_EMBED_MARKER in html:
        return html
    preface_match = re.search(r'<h1 id="preface">', html)
    if not preface_match:
        return html
    figure_matches = list(re.finditer(r"</figure>", html))
    if not figure_matches:
        return html
    cover_figure_end = None
    for figure_match in figure_matches:
        if figure_match.end() <= preface_match.start():
            cover_figure_end = figure_match.end()
        else:
            break
    if cover_figure_end is None:
        return html
    block = "\n" + render_soundcloud_audio_block()
    return html[:cover_figure_end] + block + html[cover_figure_end:]


def render_chapter_footer_nav(chapter_id: str) -> str:
    index = next(i for i, entry in enumerate(BOOK_CHAPTERS) if entry["id"] == chapter_id)
    previous_entry = BOOK_CHAPTERS[index - 1] if index > 0 else None
    next_entry = BOOK_CHAPTERS[index + 1] if index < len(BOOK_CHAPTERS) - 1 else None

    def render_link(direction: str, entry: dict | None, align_class: str) -> str:
        if entry is None:
            return f'    <div class="chapter-footer-spacer {align_class}" aria-hidden="true"></div>'
        return "\n".join(
            [
                f'    <a class="chapter-footer-link {align_class}" href="{escape(chapter_document_stem(entry["id"]))}.html">',
                f'      <span class="chapter-footer-direction">{escape(direction)}</span>',
                f'      <span class="chapter-footer-title">{escape(entry["title"])}</span>',
                "    </a>",
            ]
        )

    return "\n".join(
        [
            f'  <nav class="{CHAPTER_FOOTER_NAV_MARKER}" aria-label="Chapter navigation">',
            render_link("Previous", previous_entry, "is-previous"),
            render_link("Next", next_entry, "is-next"),
            "  </nav>",
        ]
    )


def inject_chapter_footer_nav(html: str, chapter_id: str) -> str:
    if CHAPTER_FOOTER_NAV_MARKER in html:
        return html
    return html.replace("</body>", render_chapter_footer_nav(chapter_id) + "\n</body>", 1)


def render_book_landing_html(root: Path, interactive_app_href: str) -> str:
    chapter_cards = []
    for entry in BOOK_CHAPTERS:
        cover_stem = chapter_output_stem(entry["id"])
        document_stem = chapter_document_stem(entry["id"])
        chapter_cards.append(
            "\n".join(
                [
                    '<article class="chapter-card">',
                    f'  <img src="assets/generated/covers/{cover_stem}_cover.png" alt="{escape(entry["title"])} cover">',
                    f'  <div class="chapter-copy"><p class="eyebrow">Chapter {entry["id"]}</p><h3>{escape(entry["title"])}</h3><p>{escape(entry["deck"])}</p><p class="links"><a href="html/{document_stem}.html">Read HTML</a> <span>•</span> <a href="pdf/{document_stem}/{document_stem}.pdf">PDF</a></p></div>',
                    "</article>",
                ]
            )
        )

    return "\n".join(
        [
            "<!DOCTYPE html>",
            "<html lang=\"en\">",
            "<head>",
            "  <meta charset=\"utf-8\">",
            "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">",
            f"  <title>{escape(BOOK_TITLE)}</title>",
            '  <link rel="preconnect" href="https://fonts.googleapis.com">',
            '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
            '  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:FILL@0..1" rel="stylesheet">',
            "  <style>",
            "    :root { --bg: #06090f; --bg-soft: #101722; --panel: rgba(10, 14, 21, 0.82); --bone: #f4ead4; --muted: #d8c7a1; --ember: #ff5e3a; --gold: #ffd166; }",
            "    * { box-sizing: border-box; }",
            "    body { margin: 0; font-family: Georgia, 'Times New Roman', serif; background: radial-gradient(circle at top, #182233 0%, #06090f 55%, #040507 100%); color: var(--bone); }",
            "    a { color: var(--gold); }",
            "    .video-hero { max-width: 1200px; margin: 0 auto; padding: 1.4rem 1.25rem 0.75rem; }",
            "    .video-frame { position: relative; width: 100%; aspect-ratio: 16 / 9; overflow: hidden; border-radius: 22px; background: #070b12; box-shadow: 0 28px 70px rgba(0,0,0,0.34); }",
            "    .video-frame iframe { display: block; width: 100%; height: 100%; border: 0; }",
            "    .hero { max-width: 1200px; margin: 0 auto; padding: 2rem 1.25rem 1rem; display: grid; gap: 2rem; grid-template-columns: minmax(260px, 430px) 1fr; align-items: center; }",
            "    .hero img { width: 100%; border-radius: 18px; box-shadow: 0 30px 80px rgba(0,0,0,0.45); }",
            "    .eyebrow { font-family: Helvetica, Arial, sans-serif; text-transform: uppercase; letter-spacing: 0.18em; color: var(--muted); font-size: 0.84rem; }",
            "    h1 { font-family: Helvetica, Arial, sans-serif; font-size: clamp(2.8rem, 6vw, 5.2rem); line-height: 0.95; margin: 0.2rem 0 1rem; text-transform: uppercase; }",
            "    h1 .accent { color: var(--ember); }",
            "    .subtitle { font-family: Helvetica, Arial, sans-serif; font-size: clamp(1.1rem, 2vw, 1.4rem); color: var(--gold); margin-bottom: 1rem; }",
            "    .lede { font-size: 1.18rem; line-height: 1.72; max-width: 62ch; color: #f5f0e3; }",
            "    .experience-card { margin-top: 1.5rem; padding: 1.15rem; border-radius: 22px; border: 1px solid rgba(255,255,255,0.12); background: linear-gradient(180deg, rgba(14, 18, 28, 0.92), rgba(8, 10, 16, 0.9)); box-shadow: 0 20px 52px rgba(0,0,0,0.3); }",
            "    .experience-heading { margin: 0; font-family: Helvetica, Arial, sans-serif; font-size: 1.15rem; letter-spacing: 0.04em; text-transform: uppercase; color: #fff7e8; }",
            "    .experience-caption { margin: 0.45rem 0 0; color: var(--muted); font-size: 0.98rem; line-height: 1.55; }",
            "    .experience-actions { display: grid; gap: 0.8rem; margin-top: 1rem; }",
            "    .experience-button { display: inline-flex; align-items: center; gap: 0.8rem; width: 100%; padding: 0.95rem 1.05rem; border-radius: 999px; text-decoration: none; font-family: Helvetica, Arial, sans-serif; font-weight: 700; letter-spacing: 0.01em; color: #fff8eb; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.14); box-shadow: inset 0 1px 0 rgba(255,255,255,0.04); transition: transform 160ms ease, background 160ms ease, border-color 160ms ease; }",
            "    .experience-button:hover { transform: translateY(-1px); background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.2); }",
            "    .experience-icon { display: inline-flex; align-items: center; justify-content: center; width: 2.25rem; height: 2.25rem; border-radius: 999px; background: rgba(255, 94, 58, 0.14); color: var(--gold); font-family: \"Material Symbols Rounded\"; font-size: 1.2rem; font-variation-settings: \"FILL\" 1, \"wght\" 500, \"GRAD\" 0, \"opsz\" 24; flex: 0 0 auto; }",
            "    .experience-label { display: inline-flex; align-items: center; min-width: 0; }",
            "    .audio-block { margin-top: 1.2rem; padding: 0.8rem; border-radius: 18px; border: 1px solid rgba(255,255,255,0.1); background: rgba(7,10,15,0.72); box-shadow: 0 16px 40px rgba(0,0,0,0.22); }",
            "    .audio-block iframe { display: block; width: 100%; border: 0; }",
            "    .public-brand-header { background: #fffefb; border-bottom: 1px solid rgba(0,0,0,0.08); box-shadow: 0 4px 14px rgba(0,0,0,0.05); }",
            "    .public-brand-header-inner { max-width: 1200px; margin: 0 auto; min-height: 66px; padding: 0.45rem 1.25rem; display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; }",
            "    .public-brand-link { display: inline-flex; justify-self: center; align-items: center; padding: 0; background: transparent; border-radius: 0; box-shadow: none; }",
            "    .public-brand-logo { display: block; width: min(176px, 38vw); max-height: 42px; height: auto; }",
            "    .public-brand-back-spacer { display: block; min-width: 1px; }",
            "    .section { max-width: 1200px; margin: 0 auto; padding: 1rem 1.25rem 2.5rem; }",
            "    .section h2 { font-family: Helvetica, Arial, sans-serif; font-size: 2rem; margin-bottom: 0.3rem; }",
            "    .section p.intro { color: var(--muted); font-size: 1.05rem; max-width: 72ch; }",
            "    .grid { display: grid; gap: 1.15rem; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }",
            "    .chapter-card { overflow: hidden; border-radius: 18px; border: 1px solid rgba(255,255,255,0.1); background: linear-gradient(180deg, rgba(18,25,38,0.88), rgba(7,10,15,0.94)); box-shadow: 0 20px 50px rgba(0,0,0,0.28); }",
            "    .chapter-card img { width: 100%; display: block; }",
            "    .chapter-copy { padding: 1rem 1rem 1.2rem; }",
            "    .chapter-copy h3 { font-family: Helvetica, Arial, sans-serif; font-size: 1.45rem; margin: 0.3rem 0 0.5rem; }",
            "    .chapter-copy p { margin: 0.3rem 0; line-height: 1.6; color: #f3ecdd; }",
            "    .chapter-copy .links { margin-top: 0.9rem; font-family: Helvetica, Arial, sans-serif; font-size: 0.95rem; color: var(--muted); }",
            "    .chapter-copy .links span { margin: 0 0.45rem; color: #7f7358; }",
            "    .notes { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }",
            "    .note-panel { padding: 1rem 1.1rem; border-radius: 16px; background: var(--panel); border: 1px solid rgba(255,255,255,0.08); }",
            "    .note-panel h3 { font-family: Helvetica, Arial, sans-serif; margin-top: 0; }",
            "    .patrimony-card { max-width: 1200px; margin: 0 auto 0.35rem; padding: 1.6rem 1.4rem 1.7rem; border-radius: 24px; border: 1px solid rgba(255,255,255,0.14); background: linear-gradient(135deg, rgba(36,11,11,0.96), rgba(20,24,34,0.98)); box-shadow: 0 26px 70px rgba(0,0,0,0.34); }",
            "    .patrimony-kicker { margin: 0 0 0.55rem; font-family: Helvetica, Arial, sans-serif; text-transform: uppercase; letter-spacing: 0.2em; color: var(--gold); font-size: 0.78rem; }",
            "    .patrimony-card h2 { margin: 0; font-family: Helvetica, Arial, sans-serif; font-size: clamp(2rem, 3.5vw, 3rem); line-height: 0.98; text-transform: uppercase; color: #fff7e8; }",
            "    .patrimony-deck { margin: 0.95rem 0 0.5rem; color: #fff4df; font-size: 1.08rem; line-height: 1.65; max-width: 68ch; }",
            "    .patrimony-bridge { margin: 0.45rem 0 0.9rem; color: var(--muted); line-height: 1.68; max-width: 72ch; font-size: 1.08rem; }",
            "    .patrimony-principles { margin: 0; padding-left: 1.3rem; display: grid; gap: 0.65rem; color: #fff2d7; line-height: 1.62; }",
            "    .patrimony-source { margin: 1rem 0 0; font-family: Helvetica, Arial, sans-serif; color: var(--gold); }",
            "    .patrimony-source-primary { margin-top: 1.05rem; font-size: 1.12rem; font-weight: 700; color: #fff1c9; }",
            "    .patrimony-source-secondary { margin-top: 0.45rem; font-size: 0.98rem; color: var(--muted); }",
            "    .patrimony-brand { margin: 0.45rem 0 0; font-family: Helvetica, Arial, sans-serif; color: var(--muted); }",
            "    .patrimony-brand a, .dedication-imprint a { color: var(--gold); text-decoration: none; }",
            "    .dedication-coda { max-width: 920px; margin: 0 auto 4rem; padding: 2rem 1.4rem 2.2rem; border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; background: linear-gradient(180deg, rgba(19,24,34,0.96), rgba(8,11,16,0.98)); box-shadow: 0 24px 60px rgba(0,0,0,0.28); text-align: center; }",
            "    .dedication-heading { margin: 0 0 0.9rem; font-family: Helvetica, Arial, sans-serif; text-transform: uppercase; letter-spacing: 0.18em; color: var(--gold); font-size: 0.84rem; }",
            "    .dedication-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 0.4rem; color: #fff3dc; font-size: 1.05rem; line-height: 1.55; }",
            "    .dedication-imprint { margin: 1rem 0 0; color: var(--muted); font-family: Helvetica, Arial, sans-serif; font-size: 0.92rem; letter-spacing: 0.06em; text-transform: uppercase; }",
            "    @media (max-width: 900px) { .hero { grid-template-columns: 1fr; } }",
            "  </style>",
            "</head>",
            "<body>",
            render_public_logo_header("assets/brand/waken-ai-black.webp"),
            render_vimeo_hero_block(),
            '  <section class="hero">',
            '    <img src="assets/generated/master_cover.png" alt="Children of the Feed cover">',
            "    <div>",
            '      <p class="eyebrow">Literary public edition</p>',
            f'      <h1>Children of the <span class="accent">Feed</span></h1>',
            f'      <p class="subtitle">{escape(BOOK_SUBTITLE)}</p>',
            '      <p class="lede">This is the magazine-style, public-facing edition of the AI Empire research program. It translates the full dossier into a cinematic and commercially legible reading experience while keeping the documentary spine intact through lighter end notes that point back to the validated chapter papers.</p>',
            "      <section class=\"experience-card\" aria-label=\"Choose your experience\">",
            "        <h2 class=\"experience-heading\">Choose Your Experience</h2>",
            "        <p class=\"experience-caption\">You can also scroll down to read specific chapters</p>",
            "        <div class=\"experience-actions\">",
            f'          <a class="experience-button" href="{escape(interactive_app_href)}"><span class="experience-icon" aria-hidden="true">auto_stories</span><span class="experience-label">Interactive App</span></a>',
            '          <a class="experience-button" href="html/full_book.html"><span class="experience-icon" aria-hidden="true">menu_book</span><span class="experience-label">Read the full book</span></a>',
            '          <a class="experience-button" href="pdf/full_book/full_book.pdf"><span class="experience-icon" aria-hidden="true">download</span><span class="experience-label">Download the PDF</span></a>',
            "        </div>",
            "      </section>",
            render_soundcloud_audio_block(),
            "    </div>",
            "  </section>",
            render_patimony_html_card(
                compact=False,
                show_wakenai=True,
                extra_sentence="This literary edition is part of a research program aimed at empowering humanity and reclaiming civic and creative sovereignty for future generations.",
                bridge_sentence="This research program argues that AI is the patrimony of humanity as it is derived from our civilizational core.",
                source_entries=[
                    {
                        "css_class": "patrimony-source patrimony-source-primary",
                        "label": "AI-Empire",
                        "title": "Main Research Program",
                        "href": "https://markuriostegui.github.io/childrenofthefeed/",
                    },
                    {
                        "css_class": "patrimony-source patrimony-source-secondary",
                        "label": "Essay featured by the House of Representatives special AI Task Force",
                        "title": "AI Copyright Weights: A New Frontier in Intellectual Property Law",
                        "href": "https://medium.com/twinchat/ai-copyright-weights-a-new-frontier-in-intellectual-property-law-d8ee1b6c55ee",
                    },
                ],
            ),
            '  <section class="section">',
            "    <h2>How this edition works</h2>",
            '    <p class="intro">Each chapter is designed for a general reader: fewer academic interruptions, stronger visual rhythm, and a direct path back to the research papers when the reader wants the full evidence burden.</p>',
            '    <div class="notes"><div class="note-panel"><h3>Reading mode</h3><p>Read the full book as one arc, or move chapter by chapter through the literary cards below.</p></div><div class="note-panel"><h3>Evidence discipline</h3><p>Disputed matters stay bounded. Strong factual claims still rest on the corresponding papers, omnibus, and corpus companion.</p></div><div class="note-panel"><h3>Visual language</h3><p>The look combines a provided master cover, original GPT Image 2 chapter covers, selected narrative illustrations, and vivid branded infographic charts built for both HTML and PDF.</p></div></div>',
            "  </section>",
            '  <section class="section">',
            "    <h2>Chapter editions</h2>",
            '    <p class="intro">Every chapter has its own literary page and PDF. The first release goes deepest on the platform-capture, dataset, and access-control chapters while keeping the full book navigable from day one.</p>',
            '    <div class="grid">',
            *chapter_cards,
            "    </div>",
            "  </section>",
            render_literary_dedication_block_html(),
            "</body>",
            "</html>",
            "",
        ]
    )


def seed_book(root: Path, overwrite_existing: bool = False) -> None:
    ensure_book_scaffolds(root)
    if overwrite_existing or not (root / "book" / "full_book.md").exists():
        overwrite(root / "book" / "full_book.md", build_full_book_markdown(root))


def export_book(root: Path) -> None:
    pandoc = subprocess.run(["which", "pandoc"], capture_output=True, text=True)
    if pandoc.returncode != 0:
        raise RuntimeError("pandoc is required for book export but is not installed")

    seed_book(root, overwrite_existing=True)

    build_book_root = root / "build" / "book"
    html_root = build_book_root / "html"
    pdf_root = build_book_root / "pdf"
    tex_root = build_book_root / "tex"
    processed_root = build_book_root / "processed"
    assets_root = build_book_root / "assets"
    for path in [html_root, pdf_root, tex_root, processed_root, assets_root]:
        ensure_dir(path)

    source_assets = root / "book" / "assets"
    if source_assets.exists():
        if assets_root.exists():
            shutil.rmtree(assets_root)
        shutil.copytree(source_assets, assets_root, dirs_exist_ok=True)
    copy_brand_logo(root, build_book_root)

    child_env = os.environ.copy()

    header_path = root / "apps" / "templates" / "book_export_header.tex"
    css_source_path = root / "apps" / "templates" / "book_export.css"
    css_path = html_root / css_source_path.name
    overwrite(css_path, css_source_path.read_text(encoding="utf-8"))

    documents = [root / "book" / "full_book.md", *chapter_markdown_paths(root)]
    resource_paths = [str(root / "book"), str(root / "book" / "chapters"), str(root)]
    for markdown_path in documents:
        export_markdown_document(
            markdown_path,
            tex_root,
            pdf_root,
            processed_root,
            html_root,
            header_path,
            css_path,
            child_env,
            resource_paths=resource_paths,
            font_size="12pt",
            build_pdf=False,
        )
        html_path = html_root / f"{markdown_path.stem}.html"
        html_content = html_path.read_text(encoding="utf-8")
        if markdown_path.stem == "full_book":
            html_content = inject_soundcloud_into_full_book_html(html_content)
        else:
            html_content = inject_soundcloud_into_chapter_html(html_content)
            html_content = inject_chapter_footer_nav(
                html_content,
                chapter_entry_for_document_stem(markdown_path.stem)["id"],
            )
        overwrite(html_path, append_literary_dedication_block(html_content))

    overwrite(build_book_root / "index.html", render_book_landing_html(root, BOOK_INTERACTIVE_APP_LOCAL_HREF))
    site_root = root / "build" / "site"
    if site_root.exists():
        sync_book_to_site(root, site_root)
    publication_root = root / "build" / "publication"
    ensure_dir(publication_root)
    copy_brand_logo(root, publication_root)
    overwrite(
        publication_root / "index.html",
        render_publication_index(root, base_prefix="../", book_index_rel="../book/index.html"),
    )


def _copy_selected_tree(source_root: Path, target_root: Path, allowed_dirs: list[str], allowed_files: list[str] | None = None) -> None:
    ensure_dir(target_root)
    if allowed_files:
        for file_name in allowed_files:
            source_file = source_root / file_name
            if source_file.exists():
                shutil.copy2(source_file, target_root / file_name)
    for directory_name in allowed_dirs:
        source_dir = source_root / directory_name
        if source_dir.exists():
            shutil.copytree(source_dir, target_root / directory_name, dirs_exist_ok=True)


def sync_book_to_site(root: Path, site_root: Path) -> None:
    book_source = root / "build" / "book"
    if not book_source.exists():
        return
    target_root = site_root / "book"
    if target_root.exists():
        shutil.rmtree(target_root)
    _copy_selected_tree(book_source, target_root, ["html", "pdf", "tex", "assets"], allowed_files=["index.html"])
    overwrite(target_root / "index.html", render_book_landing_html(root, BOOK_INTERACTIVE_APP_PUBLISHED_HREF))


def _prune_public_artifact_noise(target_root: Path) -> None:
    for path in target_root.rglob(".DS_Store"):
        if path.is_file():
            path.unlink()


def build_site(root: Path) -> None:
    # `build-site` is the canonical one-command publication build from the
    # canonical narrative layers. It must refresh papers, shared volumes,
    # literary HTML, and literary print PDFs before assembling the Pages tree.
    from .book_print import export_book_print
    from .papers import export_papers, seed_papers

    seed_papers(root, overwrite_existing=True)
    export_papers(root)
    export_book(root)
    export_book_print(root)

    site_root = root / "build" / "site"
    if site_root.exists():
        shutil.rmtree(site_root)
    ensure_dir(site_root)
    copy_brand_logo(root, site_root)
    overwrite(site_root / ".nojekyll", "")
    overwrite(
        site_root / "index.html",
        render_publication_index(root, base_prefix="", book_index_rel="book/index.html"),
    )
    papers_source = root / "build" / "papers"
    volumes_source = root / "build" / "volumes"
    book_source = root / "build" / "book"

    if papers_source.exists():
        _copy_selected_tree(papers_source, site_root / "papers", ["html", "pdf", "tex", "assets"])
    if volumes_source.exists():
        _copy_selected_tree(volumes_source, site_root / "volumes", ["html", "pdf", "tex"])
    if book_source.exists():
        sync_book_to_site(root, site_root)
    publish_website_bundle(root, site_root)
    _prune_public_artifact_noise(site_root)
