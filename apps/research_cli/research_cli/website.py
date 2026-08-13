from __future__ import annotations

import html
import json
import re
import shutil
import textwrap
from pathlib import Path
from typing import Any

from .fs import dump_json, ensure_dir, overwrite

BOOK_TITLE = "Children of the Feed. Servants of the AI God"
BOOK_SUBTITLE = "A chapter-based story reader built from the editorial book source"
STORAGE_KEY = "ai_empire_reader_state"
STATE_VERSION = 1
ALLOWED_SECTIONS = {"Opening", "Main Narrative"}
IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
EMPHASIS_PATTERN = re.compile(r"(\*\*|__|\*|_|~~|`)")
BLOCK_TARGET_WORDS = 38
BLOCK_SOFT_MAX_WORDS = 52
BLOCK_MIN_MERGE_WORDS = 14
AUTOPLAY_SHORT_WORDS_MAX = 18
AUTOPLAY_MEDIUM_WORDS_MAX = 48
AUTOPLAY_SHORT_WORDS_PER_MINUTE = 260
AUTOPLAY_MEDIUM_WORDS_PER_MINUTE = 225
AUTOPLAY_LONG_WORDS_PER_MINUTE = 190
AUTOPLAY_SHORT_PAUSE_MS = 300
AUTOPLAY_MEDIUM_PAUSE_MS = 700
AUTOPLAY_LONG_PAUSE_MS = 1200
AUTOPLAY_MIN_MS = 2200
AUTOPLAY_MAX_MS = 18000
BUNDLE_VERSION = "reader-fit-v5"
BRAND_LOGO_NAME = "waken-ai-black.webp"
BOOK_LANDING_URL = "../book/index.html"
RESEARCH_PAPER_URL = "../papers/html/11_children-of-the-feed-servants-of-the-ai-god_paper.html"


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---\n"):
        return {}, content
    _, remainder = content.split("---\n", 1)
    frontmatter_text, separator, body = remainder.partition("\n---\n")
    if not separator:
        return {}, content
    data: dict[str, str] = {}
    for line in frontmatter_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data, body.lstrip()


def word_count(text: str) -> int:
    return len([word for word in text.split() if word])


def clean_markdown_text(text: str) -> str:
    without_images = IMAGE_PATTERN.sub("", text)
    without_links = LINK_PATTERN.sub(r"\1", without_images)
    without_marks = EMPHASIS_PATTERN.sub("", without_links)
    normalized = without_marks.replace("\\", "")
    normalized = re.sub(r"^\s*>\s?", "", normalized, flags=re.MULTILINE)
    normalized = re.sub(r"\s+", " ", normalized)
    return html.unescape(normalized).strip()


def split_sentences(text: str) -> list[str]:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    return sentences or [text.strip()]


def split_by_words(text: str, max_words: int) -> list[str]:
    words = text.split()
    return [" ".join(words[index : index + max_words]) for index in range(0, len(words), max_words)]


def split_long_clause(sentence: str, max_words: int) -> list[str]:
    fragments = [fragment.strip() for fragment in re.split(r"(?<=[,:;])\s+", sentence) if fragment.strip()]
    if len(fragments) <= 1:
        return split_by_words(sentence, max_words)

    chunks: list[str] = []
    current = ""
    for fragment in fragments:
        candidate = fragment if not current else f"{current} {fragment}".strip()
        if word_count(candidate) <= max_words:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if word_count(fragment) <= max_words:
            current = fragment
        else:
            chunks.extend(split_by_words(fragment, max_words))
            current = ""
    if current:
        chunks.append(current)
    return chunks


def split_long_text(text: str, target_words: int = BLOCK_TARGET_WORDS, soft_max_words: int = BLOCK_SOFT_MAX_WORDS) -> list[str]:
    if word_count(text) <= soft_max_words:
        return [text]

    chunks: list[str] = []
    current: list[str] = []
    current_words = 0
    for sentence in split_sentences(text):
        sentence_words = word_count(sentence)
        if sentence_words > soft_max_words:
            if current:
                chunks.append(" ".join(current).strip())
                current = []
                current_words = 0
            chunks.extend(split_long_clause(sentence, soft_max_words))
            continue
        proposed_words = current_words + sentence_words
        if current and proposed_words > target_words and current_words >= BLOCK_MIN_MERGE_WORDS:
            chunks.append(" ".join(current).strip())
            current = [sentence]
            current_words = sentence_words
            continue
        if current and proposed_words > soft_max_words:
            chunks.append(" ".join(current).strip())
            current = [sentence]
            current_words = sentence_words
            continue
        current.append(sentence)
        current_words = proposed_words
    if current:
        chunks.append(" ".join(current).strip())
    return chunks


def merge_text_pieces(
    pieces: list[str],
    target_words: int = BLOCK_TARGET_WORDS + 4,
    soft_max_words: int = BLOCK_SOFT_MAX_WORDS,
) -> list[str]:
    merged: list[str] = []
    buffer = ""
    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        if not buffer:
            buffer = piece
            continue
        candidate = f"{buffer} {piece}".strip()
        buffer_words = word_count(buffer)
        candidate_words = word_count(candidate)
        if candidate_words <= target_words or (buffer_words < BLOCK_MIN_MERGE_WORDS and candidate_words <= soft_max_words):
            buffer = candidate
            continue
        merged.append(buffer)
        buffer = piece
    if buffer:
        merged.append(buffer)
    return merged


def extract_markdown_image(line: str) -> str | None:
    match = IMAGE_PATTERN.fullmatch(line.strip())
    return match.group(1) if match else None


def extract_title(body: str, source_path: Path) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return source_path.stem


def extract_cover_image(body: str) -> str | None:
    for line in body.splitlines():
        image = extract_markdown_image(line)
        if image:
            return image
    return None


def extract_section_items(body: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current_section = ""
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        paragraph = clean_markdown_text(" ".join(paragraph_lines))
        if paragraph:
            items.append({"type": "text", "value": paragraph})
        paragraph_lines.clear()

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            flush_paragraph()
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            current_section = stripped[3:].strip()
            continue
        image = extract_markdown_image(stripped)
        if image and current_section in ALLOWED_SECTIONS:
            flush_paragraph()
            items.append({"type": "image", "value": image})
            continue
        if current_section not in ALLOWED_SECTIONS:
            continue
        if not stripped:
            flush_paragraph()
            continue
        paragraph_lines.append(stripped)

    flush_paragraph()
    return items


def chapter_sort_key(source_path: Path) -> tuple[str, str]:
    frontmatter, _ = parse_frontmatter(source_path.read_text(encoding="utf-8"))
    return frontmatter.get("chapter_id", source_path.stem), source_path.name


def source_image_to_output_path(root: Path, source_path: Path) -> Path:
    book_assets_root = (root / "book" / "assets").resolve()
    if source_path.is_relative_to(book_assets_root):
        relative = source_path.relative_to(book_assets_root)
        return Path("assets") / "images" / relative
    sanitized_parts = [part for part in source_path.parts[-3:] if part not in {"..", "."}]
    return Path("assets") / "images" / "external" / Path(*sanitized_parts)


def copy_image(root: Path, website_root: Path, image_ref: str, source_markdown_path: Path, image_map: dict[Path, str]) -> str:
    source_path = (source_markdown_path.parent / image_ref).resolve()
    if source_path in image_map:
        return image_map[source_path]
    if not source_path.exists():
        raise FileNotFoundError(f"Referenced image does not exist: {source_path}")
    relative_output = source_image_to_output_path(root, source_path)
    destination_path = website_root / relative_output
    ensure_dir(destination_path.parent)
    shutil.copy2(source_path, destination_path)
    image_map[source_path] = relative_output.as_posix()
    return image_map[source_path]


def serialize_chapter(root: Path, website_root: Path, source_path: Path, image_map: dict[Path, str]) -> dict[str, Any]:
    frontmatter, body = parse_frontmatter(source_path.read_text(encoding="utf-8"))
    del frontmatter
    title = extract_title(body, source_path)
    cover_image_ref = extract_cover_image(body)
    if cover_image_ref is None:
        raise ValueError(f"Chapter is missing a cover image: {source_path}")
    current_image = copy_image(root, website_root, cover_image_ref, source_path, image_map)

    raw_items = extract_section_items(body)
    blocks: list[dict[str, str]] = []
    text_buffer: list[str] = []

    def flush_buffer() -> None:
        nonlocal text_buffer
        if not text_buffer:
            return
        for chunk in merge_text_pieces(text_buffer):
            blocks.append({"text": chunk, "image": current_image})
        text_buffer = []

    for item in raw_items:
        if item["type"] == "image":
            flush_buffer()
            current_image = copy_image(root, website_root, item["value"], source_path, image_map)
            continue
        for piece in split_long_text(item["value"]):
            text_buffer.append(piece)

    flush_buffer()
    if not blocks:
        raise ValueError(f"Chapter produced no reader blocks: {source_path}")
    return {"title": title, "blocks": blocks}


def derive_hook_candidates(chapters: list[dict[str, Any]]) -> list[str]:
    hooks: list[str] = []
    seen: set[str] = set()
    preferred_starts = ("Do you", "What happens", "Can you", "Do we", "If ", "When ", "Why ")
    for chapter in chapters:
        for block in chapter["blocks"][:4]:
            for sentence in split_sentences(block["text"]):
                candidate = sentence.strip()
                if not candidate:
                    continue
                is_question = candidate.endswith("?")
                total_words = word_count(candidate)
                is_preferred = candidate.startswith(preferred_starts)
                if (is_question and total_words <= BLOCK_TARGET_WORDS) or is_preferred or 5 <= total_words <= 12:
                    if candidate not in seen:
                        hooks.append(candidate)
                        seen.add(candidate)
                    break
    if hooks:
        return hooks
    fallback_sentence = split_sentences(chapters[0]["blocks"][0]["text"])[0]
    return [fallback_sentence]


def default_reader_state() -> dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "lastPosition": {"chapterIndex": 0, "blockIndex": 0},
        "chapterProgress": {},
        "favorites": [],
        "notes": [],
    }


def normalize_reader_state(raw: Any) -> dict[str, Any]:
    state = default_reader_state()
    if not isinstance(raw, dict):
        return state
    last_position = raw.get("lastPosition", {})
    if isinstance(last_position, dict):
        chapter_index = last_position.get("chapterIndex", 0)
        block_index = last_position.get("blockIndex", 0)
        if isinstance(chapter_index, int) and chapter_index >= 0 and isinstance(block_index, int) and block_index >= 0:
            state["lastPosition"] = {"chapterIndex": chapter_index, "blockIndex": block_index}
    chapter_progress = raw.get("chapterProgress", {})
    if isinstance(chapter_progress, dict):
        normalized_progress: dict[str, Any] = {}
        for key, value in chapter_progress.items():
            if not isinstance(value, dict):
                continue
            completed_blocks = value.get("completedBlocks", [])
            normalized_progress[str(key)] = {
                "lastBlockIndex": int(value.get("lastBlockIndex", 0)),
                "completedBlocks": [int(block) for block in completed_blocks if isinstance(block, int)],
                "progressPercent": int(value.get("progressPercent", 0)),
                "completed": bool(value.get("completed", False)),
                "updatedAt": value.get("updatedAt", ""),
            }
        state["chapterProgress"] = normalized_progress
    favorites = raw.get("favorites", [])
    if isinstance(favorites, list):
        state["favorites"] = [favorite for favorite in favorites if isinstance(favorite, dict)]
    notes = raw.get("notes", [])
    if isinstance(notes, list):
        state["notes"] = [note for note in notes if isinstance(note, dict)]
    return state


def update_progress(state: dict[str, Any], chapter_index: int, block_index: int, total_blocks: int, timestamp: str) -> dict[str, Any]:
    chapter_key = str(chapter_index)
    chapter_progress = state.setdefault("chapterProgress", {})
    entry = chapter_progress.get(chapter_key, {})
    completed_blocks = set(entry.get("completedBlocks", []))
    completed_blocks.add(block_index)
    progress_percent = round((len(completed_blocks) / max(total_blocks, 1)) * 100)
    chapter_progress[chapter_key] = {
        "lastBlockIndex": block_index,
        "completedBlocks": sorted(completed_blocks),
        "progressPercent": progress_percent,
        "completed": block_index >= total_blocks - 1,
        "updatedAt": timestamp,
    }
    state["lastPosition"] = {"chapterIndex": chapter_index, "blockIndex": block_index}
    return state


def favorite_id(chapter_index: int, block_index: int) -> str:
    return f"fav-{chapter_index}-{block_index}"


def note_id(chapter_index: int, block_index: int) -> str:
    return f"note-{chapter_index}-{block_index}"


def toggle_favorite(
    state: dict[str, Any],
    chapter_index: int,
    block_index: int,
    chapter_title: str,
    text: str,
    image: str,
    timestamp: str,
) -> dict[str, Any]:
    favorites = list(state.get("favorites", []))
    target_id = favorite_id(chapter_index, block_index)
    existing = next((favorite for favorite in favorites if favorite.get("id") == target_id), None)
    if existing:
        state["favorites"] = [favorite for favorite in favorites if favorite.get("id") != target_id]
        return state
    favorites.append(
        {
            "id": target_id,
            "chapterIndex": chapter_index,
            "blockIndex": block_index,
            "chapterTitle": chapter_title,
            "text": text,
            "image": image,
            "createdAt": timestamp,
        }
    )
    state["favorites"] = favorites
    return state


def upsert_note(
    state: dict[str, Any],
    chapter_index: int,
    block_index: int,
    chapter_title: str,
    block_text: str,
    comment: str,
    image: str,
    timestamp: str,
) -> dict[str, Any]:
    notes = list(state.get("notes", []))
    target_id = note_id(chapter_index, block_index)
    existing = next((note for note in notes if note.get("id") == target_id), None)
    if existing:
        existing["comment"] = comment
        existing["updatedAt"] = timestamp
        existing["chapterTitle"] = chapter_title
        existing["blockText"] = block_text
        existing["image"] = image
        state["notes"] = notes
        return state
    notes.append(
        {
            "id": target_id,
            "chapterIndex": chapter_index,
            "blockIndex": block_index,
            "chapterTitle": chapter_title,
            "blockText": block_text,
            "comment": comment,
            "image": image,
            "createdAt": timestamp,
            "updatedAt": timestamp,
        }
    )
    state["notes"] = notes
    return state


def delete_note(state: dict[str, Any], target_id: str) -> dict[str, Any]:
    state["notes"] = [note for note in state.get("notes", []) if note.get("id") != target_id]
    return state


def get_autoplay_delay_ms(text: str) -> int:
    words = max(word_count(text), 0)
    if words <= AUTOPLAY_SHORT_WORDS_MAX:
        words_per_minute = AUTOPLAY_SHORT_WORDS_PER_MINUTE
        pause_ms = AUTOPLAY_SHORT_PAUSE_MS
    elif words <= AUTOPLAY_MEDIUM_WORDS_MAX:
        words_per_minute = AUTOPLAY_MEDIUM_WORDS_PER_MINUTE
        pause_ms = AUTOPLAY_MEDIUM_PAUSE_MS
    else:
        words_per_minute = AUTOPLAY_LONG_WORDS_PER_MINUTE
        pause_ms = AUTOPLAY_LONG_PAUSE_MS
    base_delay = round((words / words_per_minute) * 60000 + pause_ms)
    return max(AUTOPLAY_MIN_MS, min(AUTOPLAY_MAX_MS, base_delay))


def generate_readme() -> str:
    return textwrap.dedent(
        f"""\
        # Story Reader SPA

        This directory is a generated static reader bundle for **{BOOK_TITLE}**.

        ## Regenerate

        ```bash
        PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \\
        python3 -m research_cli.cli build-website --root /Users/hassan/repos/AI-Empire
        ```

        ## Structure

        - `index.html`: SPA shell
        - `assets/css/app.css`: mobile-first cinematic styling
        - `assets/js/app.js`: router, reader UI, and local storage state
        - `assets/images/`: copied editorial imagery for self-contained runtime use
        - `data/chapters.json`: generated chapter/block data contract

        `build-site` publishes the same bundle at `build/site/website/`.
        `build-website` remains available for targeted local reader rebuilds.
        """
    )


def copy_brand_logo(root: Path, website_root: Path) -> None:
    candidate_paths = [
        root / "public" / "assets" / "brand" / BRAND_LOGO_NAME,
        root / "build" / "site" / "assets" / "brand" / BRAND_LOGO_NAME,
        root / "build" / "site" / BRAND_LOGO_NAME,
    ]
    source_path = next((path for path in candidate_paths if path.exists()), None)
    if source_path is None:
        return
    destination_path = website_root / "assets" / "images" / BRAND_LOGO_NAME
    ensure_dir(destination_path.parent)
    shutil.copy2(source_path, destination_path)


def render_index_html(chapters: list[dict[str, Any]], hooks: list[str]) -> str:
    chapters_json = json.dumps(chapters, ensure_ascii=False)
    hooks_json = json.dumps(hooks, ensure_ascii=False)
    return textwrap.dedent(
        f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
          <title>{html.escape(BOOK_TITLE)} Reader</title>
          <meta name="description" content="A chapter-based story reader generated from the editorial book source.">
          <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%2305080d'/%3E%3Cpath d='M17 15h12c8 0 13 3 13 11 0 5-2 9-7 10v1c6 1 9 5 9 12 0 10-7 15-18 15H17zm11 19c5 0 7-2 7-6s-3-5-7-5h-3v11zm1 22c6 0 9-2 9-7 0-4-3-6-9-6h-4v13z' fill='%23f7eedb'/%3E%3C/svg%3E">
          <link rel="preconnect" href="https://fonts.googleapis.com">
          <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
          <link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Cormorant+Garamond:wght@400;500;600;700&display=swap" rel="stylesheet">
          <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:FILL@0..1" rel="stylesheet">
          <link rel="stylesheet" href="assets/css/app.css?v={BUNDLE_VERSION}">
        </head>
        <body>
          <div class="app-shell">
            <main id="app" class="app-main" aria-live="polite"></main>
            <nav class="bottom-nav" aria-label="Primary">
              <a href="#/home" data-nav="home">Home</a>
              <a href="#/index" data-nav="index">Index</a>
              <a href="#/favorites" data-nav="favorites">Favorites</a>
              <a href="#/notes" data-nav="notes">Notes</a>
            </nav>
          </div>

          <dialog id="note-dialog" class="note-dialog">
            <form method="dialog" class="note-form" id="note-form">
              <p class="dialog-kicker">Private note</p>
              <h2 id="note-dialog-title">Add a note</h2>
              <p id="note-context" class="note-context"></p>
              <textarea id="note-input" rows="6" placeholder="Write a private note about this block..."></textarea>
              <div class="note-actions">
                <button value="cancel" type="button" id="note-cancel">Cancel</button>
                <button value="delete" type="button" id="note-delete" class="danger">Delete</button>
                <button value="save" type="submit" class="primary">Save note</button>
              </div>
            </form>
          </dialog>

          <script id="chapters-data" type="application/json">{chapters_json}</script>
          <script id="hook-data" type="application/json">{hooks_json}</script>
          <script defer src="assets/js/app.js?v={BUNDLE_VERSION}"></script>
        </body>
        </html>
        """
    )


def render_css() -> str:
    return textwrap.dedent(
        """\
        :root {
          color-scheme: dark;
          --bg: #040508;
          --panel: rgba(8, 11, 16, 0.74);
          --panel-strong: rgba(7, 9, 14, 0.92);
          --line: rgba(255, 244, 223, 0.16);
          --text: #f7eedb;
          --muted: #d0c0a1;
          --soft: #948468;
          --accent: #ffb84d;
          --accent-2: #ff6a3d;
          --danger: #ff6b6b;
          --shadow: 0 24px 70px rgba(0, 0, 0, 0.35);
          --nav-h: 84px;
          --shell-w: 1080px;
          --device-w: 640px;
          --radius: 22px;
          --serif: "Cormorant Garamond", "Iowan Old Style", "Palatino Linotype", serif;
          --sans: "Bebas Neue", "Avenir Next Condensed", "Arial Narrow", sans-serif;
        }

        * {
          box-sizing: border-box;
        }

        html,
        body {
          margin: 0;
          min-height: 100%;
          background:
            radial-gradient(circle at top, rgba(255, 136, 0, 0.18), transparent 36%),
            linear-gradient(180deg, #06080d 0%, #020305 100%);
          color: var(--text);
          font-family: var(--serif);
        }

        body {
          min-height: 100vh;
        }

        html.reader-route,
        body.reader-route {
          height: 100dvh;
          overflow: hidden;
          overscroll-behavior: none;
        }

        a {
          color: inherit;
          text-decoration: none;
        }

        button,
        textarea {
          font: inherit;
        }

        .app-shell {
          min-height: 100vh;
          padding-bottom: calc(var(--nav-h) + 1.2rem + env(safe-area-inset-bottom, 0px));
        }

        body.reader-route .app-shell {
          height: 100dvh;
          overflow: hidden;
        }

        .app-main {
          min-height: 100vh;
        }

        body.reader-route .app-main {
          height: 100%;
          min-height: 100%;
          overflow: hidden;
        }

        .screen {
          width: min(100%, var(--shell-w));
          margin: 0 auto;
          padding: 1.1rem 1rem 1rem;
        }

        .screen.screen-centered {
          min-height: calc(100dvh - var(--nav-h) - 2rem);
          display: grid;
          align-items: center;
        }

        .screen-stack {
          width: 100%;
          display: grid;
          gap: 1rem;
        }

        .reader-screen {
          width: min(100%, var(--device-w));
          padding: 0;
          height: calc(100dvh - var(--nav-h) - 1.3rem);
          overflow: hidden;
        }

        .hero-card,
        .panel,
        .chapter-card,
        .saved-card {
          background: linear-gradient(180deg, rgba(12, 16, 24, 0.9), rgba(5, 8, 14, 0.96));
          border: 1px solid var(--line);
          border-radius: var(--radius);
          box-shadow: var(--shadow);
          overflow: hidden;
        }

        .hero-card {
          min-height: calc(100dvh - var(--nav-h) - 2rem);
          display: grid;
          align-items: end;
          background-size: cover;
          background-position: center;
          position: relative;
          max-height: 860px;
        }

        .hero-card.home-card {
          min-height: 0;
          max-height: none;
        }

        .hero-card::before,
        .reader-stage::before {
          content: "";
          position: absolute;
          inset: 0;
          background:
            linear-gradient(180deg, rgba(0, 0, 0, 0.18) 0%, rgba(3, 5, 8, 0.62) 40%, rgba(2, 3, 5, 0.94) 100%),
            linear-gradient(90deg, rgba(255, 137, 41, 0.14), transparent 44%, rgba(0, 0, 0, 0.3) 100%);
        }

        .hero-copy,
        .reader-copy {
          position: relative;
          z-index: 1;
          padding: 1.3rem;
        }

        .hero-copy {
          max-width: min(100%, 25rem);
        }

        .brand-header {
          display: flex;
          justify-content: center;
          margin-bottom: 0.75rem;
        }

        .brand-link {
          width: min(100%, 560px);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 0.75rem 1.2rem;
          background: #ffffff;
          border-radius: 999px;
          border: 1px solid rgba(0, 0, 0, 0.04);
          box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
        }

        .brand-link img {
          display: block;
          height: 30px;
          width: auto;
        }

        .eyebrow,
        .meta-label,
        .dialog-kicker {
          margin: 0 0 0.55rem;
          color: var(--accent);
          letter-spacing: 0.16em;
          text-transform: uppercase;
          font-family: var(--sans);
          font-size: 0.78rem;
        }

        h1,
        h2,
        h3 {
          margin: 0;
          font-family: var(--sans);
          line-height: 0.95;
          text-wrap: balance;
        }

        .hero-title {
          font-size: clamp(2.7rem, 11vw, 5.6rem);
          max-width: 9ch;
        }

        .hero-subtitle,
        .hero-hook,
        .hero-copy p,
        .chapter-card p,
        .saved-card p,
        .note-context,
        .empty-state p {
          color: var(--muted);
          line-height: 1.55;
        }

        .hero-subtitle {
          font-size: 1rem;
          max-width: 20ch;
          margin-top: 0.85rem;
        }

        .hero-hook {
          font-size: 1.34rem;
          color: var(--text);
          max-width: 15ch;
          margin: 1.15rem 0 0.9rem;
        }

        .resume-meta {
          margin: 0 0 1rem;
          font-family: var(--sans);
          font-size: 0.92rem;
          letter-spacing: 0.08em;
          color: var(--soft);
        }

        .button-row,
        .saved-actions,
        .reader-actions,
        .note-actions {
          display: flex;
          gap: 0.75rem;
          flex-wrap: wrap;
        }

        .button,
        .note-actions button,
        .saved-actions button {
          border: 1px solid var(--line);
          border-radius: 999px;
          padding: 0.82rem 1.1rem;
          background: rgba(255, 255, 255, 0.04);
          color: var(--text);
          cursor: pointer;
          transition: transform 140ms ease, background 140ms ease, border-color 140ms ease;
        }

        .button:hover,
        .note-actions button:hover,
        .saved-actions button:hover {
          transform: translateY(-1px);
          background: rgba(255, 255, 255, 0.08);
        }

        .button.primary,
        .note-actions .primary {
          background: linear-gradient(135deg, var(--accent-2), var(--accent));
          color: #130d06;
          border-color: transparent;
          font-weight: 700;
        }

        .danger {
          color: #ffd5d5;
          border-color: rgba(255, 107, 107, 0.45);
        }

        .section-head {
          display: flex;
          justify-content: space-between;
          align-items: end;
          gap: 1rem;
          margin-bottom: 1rem;
        }

        .section-head h1 {
          font-size: clamp(2rem, 8vw, 3.1rem);
        }

        .section-head p {
          max-width: 34ch;
          margin: 0;
          color: var(--muted);
        }

        .chapter-grid,
        .saved-grid {
          display: grid;
          gap: 1rem;
        }

        .chapter-card {
          display: grid;
        }

        .chapter-cover {
          aspect-ratio: 16 / 10;
          background-size: cover;
          background-position: center;
          position: relative;
        }

        .chapter-cover::after {
          content: "";
          position: absolute;
          inset: 0;
          background: linear-gradient(180deg, rgba(0, 0, 0, 0.1), rgba(3, 5, 8, 0.82));
        }

        .chapter-body,
        .saved-body {
          padding: 1rem;
        }

        .chapter-body h2,
        .saved-body h2 {
          font-size: 1.55rem;
          margin-bottom: 0.55rem;
        }

        .progress-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 0.8rem;
          margin: 0.8rem 0 1rem;
          font-family: var(--sans);
          color: var(--soft);
        }

        .progress-bar {
          flex: 1;
          height: 7px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.08);
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, var(--accent-2), var(--accent));
        }

        .reader-stage {
          height: 100%;
          display: flex;
          align-items: stretch;
          background-size: cover;
          background-position: center;
          position: relative;
          overflow: hidden;
          max-height: 900px;
        }

        .reader-copy {
          width: 100%;
          height: 100%;
          padding: 1rem;
          overflow: hidden;
        }

        .reader-frame {
          width: 100%;
          height: 100%;
          display: grid;
          grid-template-rows: auto 1fr auto;
          gap: 1rem;
        }

        .reader-header,
        .reader-footer {
          position: relative;
          z-index: 1;
        }

        .reader-header {
          display: grid;
          gap: 0.7rem;
          padding: 0.15rem;
        }

        .reader-topline {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-family: var(--sans);
          color: var(--muted);
          letter-spacing: 0.08em;
          gap: 1rem;
        }

        .reader-chapter {
          font-size: clamp(1.35rem, 4vw, 2rem);
          max-width: 14ch;
          color: var(--text);
        }

        .reader-progress {
          font-size: 0.95rem;
          color: var(--soft);
        }

        .reader-progress-bar {
          height: 4px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.1);
          overflow: hidden;
        }

        .reader-main {
          position: relative;
          z-index: 1;
          min-height: 0;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .reader-fit-area {
          width: 100%;
          height: 100%;
          min-height: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0.1rem 0;
          overflow: hidden;
        }

        .reader-text-panel {
          width: min(100%, 34rem);
          height: min(100%, clamp(22rem, 62vh, 38rem));
          padding: 1.3rem 1.1rem;
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: calc(var(--radius) - 4px);
          background:
            linear-gradient(180deg, rgba(3, 5, 9, 0.62), rgba(6, 10, 16, 0.71)),
            radial-gradient(circle at top, rgba(255, 184, 77, 0.08), transparent 42%);
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
          overflow: hidden;
        }

        .reader-text-body {
          width: 100%;
          height: 100%;
          display: grid;
          place-items: center;
          overflow: hidden;
        }

        .reader-text {
          font-size: var(--reader-font-size, 2rem);
          line-height: 1.24;
          text-wrap: balance;
          margin: 0;
          width: 100%;
          max-width: 20ch;
          letter-spacing: 0.01em;
          overflow-wrap: anywhere;
        }

        .reader-footer {
          display: grid;
          gap: 0.38rem;
          justify-items: center;
          padding: 0;
        }

        .reader-actions {
          justify-content: center;
          gap: 0.5rem;
        }

        .reader-autoplay-progress {
          width: min(100%, 34rem);
          height: 3px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.08);
          overflow: hidden;
          opacity: 0;
          transition: opacity 120ms ease;
        }

        .reader-autoplay-progress.active {
          opacity: 1;
        }

        .reader-autoplay-fill {
          width: 100%;
          height: 100%;
          transform: scaleX(1);
          transform-origin: left center;
          background: linear-gradient(90deg, var(--accent-2), var(--accent));
        }

        .icon-button {
          width: 2.1rem;
          height: 2.1rem;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          border: 1px solid var(--line);
          border-radius: 999px;
          background: rgba(10, 14, 22, 0.72);
          color: var(--text);
          cursor: pointer;
          transition: transform 140ms ease, background 140ms ease, border-color 140ms ease, color 140ms ease;
          padding: 0;
          backdrop-filter: blur(18px);
        }

        .icon-button:hover {
          transform: translateY(-1px);
          background: rgba(255, 255, 255, 0.08);
        }

        .icon-button.active {
          background: rgba(255, 184, 77, 0.14);
          border-color: rgba(255, 184, 77, 0.4);
          color: var(--accent);
        }

        .reader-icon {
          font-family: "Material Symbols Rounded";
          font-weight: normal;
          font-style: normal;
          font-size: 0.98rem;
          line-height: 1;
          letter-spacing: normal;
          text-transform: none;
          display: inline-block;
          white-space: nowrap;
          word-wrap: normal;
          direction: ltr;
          font-variation-settings: "FILL" 0, "wght" 450, "GRAD" 0, "opsz" 24;
        }

        .icon-button.active .reader-icon {
          font-variation-settings: "FILL" 1, "wght" 500, "GRAD" 0, "opsz" 24;
        }

        .sr-only {
          position: absolute;
          width: 1px;
          height: 1px;
          padding: 0;
          margin: -1px;
          overflow: hidden;
          clip: rect(0, 0, 0, 0);
          white-space: nowrap;
          border: 0;
        }

        .saved-card {
          display: grid;
          grid-template-columns: 112px minmax(0, 1fr);
        }

        .saved-thumb {
          min-height: 100%;
          background-size: cover;
          background-position: center;
        }

        .saved-meta {
          margin-bottom: 0.65rem;
          color: var(--soft);
          font-family: var(--sans);
          font-size: 0.9rem;
        }

        .saved-snippet {
          font-size: 1.05rem;
          color: var(--text);
          margin-bottom: 0.8rem;
        }

        .empty-state {
          padding: 1.2rem;
          text-align: center;
        }

        .empty-state h2 {
          margin-bottom: 0.5rem;
        }

        .bottom-nav {
          position: fixed;
          left: 50%;
          transform: translateX(-50%);
          bottom: max(0.65rem, env(safe-area-inset-bottom, 0px));
          width: min(calc(100% - 1rem), 620px);
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 0.55rem;
          padding: 0.8rem 0.9rem;
          backdrop-filter: blur(24px);
          background: linear-gradient(180deg, rgba(5, 8, 12, 0.5), rgba(5, 8, 12, 0.94));
          border: 1px solid rgba(255, 255, 255, 0.07);
          border-radius: 24px;
          z-index: 12;
          box-shadow: 0 22px 44px rgba(0, 0, 0, 0.35);
        }

        .bottom-nav a {
          text-align: center;
          padding: 0.78rem 0.3rem;
          border-radius: 18px;
          border: 1px solid transparent;
          font-family: var(--sans);
          color: var(--soft);
        }

        .bottom-nav a.active {
          color: var(--text);
          border-color: rgba(255, 184, 77, 0.28);
          background: rgba(255, 184, 77, 0.08);
        }

        .note-dialog {
          width: min(92vw, 560px);
          border: 1px solid var(--line);
          border-radius: 24px;
          padding: 0;
          background: rgba(8, 11, 16, 0.96);
          color: var(--text);
          box-shadow: var(--shadow);
        }

        .note-dialog::backdrop {
          background: rgba(0, 0, 0, 0.56);
          backdrop-filter: blur(6px);
        }

        .note-form {
          padding: 1.15rem;
        }

        .note-form h2 {
          font-size: 1.65rem;
          margin-bottom: 0.5rem;
        }

        .note-context {
          margin-bottom: 0.8rem;
          font-size: 0.96rem;
        }

        #note-input {
          width: 100%;
          min-height: 180px;
          border-radius: 20px;
          padding: 1rem;
          border: 1px solid var(--line);
          background: rgba(255, 255, 255, 0.03);
          color: var(--text);
          resize: vertical;
        }

        @media (min-width: 760px) {
          .screen {
            padding: 1.3rem 1.35rem 1.2rem;
          }

          .screen.screen-centered {
            min-height: calc(100dvh - var(--nav-h) - 2.8rem);
          }

          .reader-screen {
            padding: 0.3rem 0 0.5rem;
            height: min(calc(100dvh - var(--nav-h) - 2.6rem), 860px);
          }

          .chapter-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .saved-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .hero-card {
            min-height: min(calc(100dvh - var(--nav-h) - 2.8rem), 820px);
          }

          .hero-card.home-card {
            min-height: 0;
          }

          .hero-copy,
          .reader-copy {
            padding: 1.5rem;
          }

          .reader-copy {
            padding: 1.35rem;
          }

          .reader-frame {
            gap: 1.2rem;
          }

          .reader-text-panel {
            max-width: 38rem;
            padding: 1.65rem 1.5rem;
            height: min(100%, clamp(24rem, 60vh, 42rem));
          }

          .reader-text {
            max-width: 23ch;
          }

          .saved-card {
            grid-template-columns: 132px minmax(0, 1fr);
          }

          .brand-link {
            width: min(100%, 620px);
          }
        }

        @media (max-width: 420px) {
          .hero-copy,
          .reader-copy {
            padding: 0.95rem;
          }

          .reader-text-panel {
            padding: 1.05rem 0.95rem;
            height: min(100%, clamp(19rem, 58vh, 34rem));
          }
        }

        body.reader-route.reader-compact .reader-screen {
          height: calc(100dvh - 4.7rem);
        }

        body.reader-route.reader-compact .bottom-nav {
          width: min(calc(100% - 0.75rem), 540px);
          gap: 0.35rem;
          padding: 0.45rem 0.6rem;
          bottom: max(0.3rem, env(safe-area-inset-bottom, 0px));
        }

        body.reader-route.reader-compact .bottom-nav a {
          padding: 0.46rem 0.2rem;
          font-size: 0.82rem;
        }

        body.reader-route.reader-compact .reader-copy {
          padding: 0.65rem;
        }

        body.reader-route.reader-compact .reader-frame {
          gap: 0.4rem;
        }

        body.reader-route.reader-compact .reader-header {
          gap: 0.3rem;
        }

        body.reader-route.reader-compact .reader-chapter {
          font-size: clamp(1rem, 3vw, 1.25rem);
        }

        body.reader-route.reader-compact .reader-progress {
          font-size: 0.78rem;
        }

        body.reader-route.reader-compact .reader-text-panel {
          height: 100%;
          padding: 0.8rem 0.9rem;
        }

        body.reader-route.reader-compact .reader-footer {
          gap: 0.18rem;
        }

        body.reader-route.reader-compact .icon-button {
          width: 1.81rem;
          height: 1.81rem;
        }

        body.reader-route.reader-compact .reader-icon {
          font-size: 0.85rem;
        }
        """
    )


def render_js() -> str:
    return textwrap.dedent(
        f"""\
        (() => {{
          const BOOK_TITLE = {json.dumps(BOOK_TITLE)};
          const STORAGE_KEY = {json.dumps(STORAGE_KEY)};
          const STATE_VERSION = {STATE_VERSION};
          const AUTOPLAY_SHORT_WORDS_MAX = {AUTOPLAY_SHORT_WORDS_MAX};
          const AUTOPLAY_MEDIUM_WORDS_MAX = {AUTOPLAY_MEDIUM_WORDS_MAX};
          const AUTOPLAY_SHORT_WORDS_PER_MINUTE = {AUTOPLAY_SHORT_WORDS_PER_MINUTE};
          const AUTOPLAY_MEDIUM_WORDS_PER_MINUTE = {AUTOPLAY_MEDIUM_WORDS_PER_MINUTE};
          const AUTOPLAY_LONG_WORDS_PER_MINUTE = {AUTOPLAY_LONG_WORDS_PER_MINUTE};
          const AUTOPLAY_SHORT_PAUSE_MS = {AUTOPLAY_SHORT_PAUSE_MS};
          const AUTOPLAY_MEDIUM_PAUSE_MS = {AUTOPLAY_MEDIUM_PAUSE_MS};
          const AUTOPLAY_LONG_PAUSE_MS = {AUTOPLAY_LONG_PAUSE_MS};
          const AUTOPLAY_MIN_MS = {AUTOPLAY_MIN_MS};
          const AUTOPLAY_MAX_MS = {AUTOPLAY_MAX_MS};
          const appRoot = document.getElementById("app");
          const noteDialog = document.getElementById("note-dialog");
          const noteForm = document.getElementById("note-form");
          const noteInput = document.getElementById("note-input");
          const noteTitle = document.getElementById("note-dialog-title");
          const noteContext = document.getElementById("note-context");
          const noteCancel = document.getElementById("note-cancel");
          const noteDelete = document.getElementById("note-delete");
          const navLinks = Array.from(document.querySelectorAll(".bottom-nav a"));

          let chapters = [];
          let hooks = [];
          let state = createDefaultState();
          let activeNoteContext = null;
          let touchStart = null;
          let fitTimer = null;
          let fitFrame = null;
          let isAutoplaying = false;
          let autoplayTimerId = null;
          let autoplayGeneration = 0;
          let readerFitObserver = null;

          function createDefaultState() {{
            return {{
              version: STATE_VERSION,
              lastPosition: {{ chapterIndex: 0, blockIndex: 0 }},
              chapterProgress: {{}},
              favorites: [],
              notes: [],
            }};
          }}

          function safeInt(value, fallback = 0) {{
            return Number.isInteger(value) && value >= 0 ? value : fallback;
          }}

          function normalizeState(raw) {{
            if (!raw || typeof raw !== "object") {{
              return createDefaultState();
            }}
            const base = createDefaultState();
            const lastPosition = raw.lastPosition || {{}};
            base.lastPosition = {{
              chapterIndex: safeInt(lastPosition.chapterIndex, 0),
              blockIndex: safeInt(lastPosition.blockIndex, 0),
            }};
            if (raw.chapterProgress && typeof raw.chapterProgress === "object") {{
              for (const [key, value] of Object.entries(raw.chapterProgress)) {{
                if (!value || typeof value !== "object") continue;
                const completedBlocks = Array.isArray(value.completedBlocks)
                  ? value.completedBlocks.filter((item) => Number.isInteger(item) && item >= 0).sort((a, b) => a - b)
                  : [];
                base.chapterProgress[key] = {{
                  lastBlockIndex: safeInt(value.lastBlockIndex, 0),
                  completedBlocks,
                  progressPercent: safeInt(value.progressPercent, 0),
                  completed: Boolean(value.completed),
                  updatedAt: typeof value.updatedAt === "string" ? value.updatedAt : "",
                }};
              }}
            }}
            base.favorites = Array.isArray(raw.favorites) ? raw.favorites.filter((item) => item && typeof item === "object") : [];
            base.notes = Array.isArray(raw.notes) ? raw.notes.filter((item) => item && typeof item === "object") : [];
            return base;
          }}

          function loadState() {{
            try {{
              const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
              state = normalizeState(parsed);
            }} catch {{
              state = createDefaultState();
            }}
            saveState();
          }}

          function saveState() {{
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
          }}

          function nowIso() {{
            return new Date().toISOString();
          }}

          function wordCount(text) {{
            return String(text).trim().split(/\\s+/).filter(Boolean).length;
          }}

          function getAutoplayDelay(text) {{
            const words = wordCount(text);
            let wordsPerMinute = AUTOPLAY_LONG_WORDS_PER_MINUTE;
            let pauseMs = AUTOPLAY_LONG_PAUSE_MS;
            if (words <= AUTOPLAY_SHORT_WORDS_MAX) {{
              wordsPerMinute = AUTOPLAY_SHORT_WORDS_PER_MINUTE;
              pauseMs = AUTOPLAY_SHORT_PAUSE_MS;
            }} else if (words <= AUTOPLAY_MEDIUM_WORDS_MAX) {{
              wordsPerMinute = AUTOPLAY_MEDIUM_WORDS_PER_MINUTE;
              pauseMs = AUTOPLAY_MEDIUM_PAUSE_MS;
            }}
            const unclamped = Math.round((words / wordsPerMinute) * 60000 + pauseMs);
            return Math.min(AUTOPLAY_MAX_MS, Math.max(AUTOPLAY_MIN_MS, unclamped));
          }}

          function clearAutoplayTimer() {{
            if (autoplayTimerId !== null) {{
              window.clearTimeout(autoplayTimerId);
              autoplayTimerId = null;
            }}
          }}

          function stopAutoplay() {{
            isAutoplaying = false;
            autoplayGeneration += 1;
            clearAutoplayTimer();
            resetAutoplayIndicator();
          }}

          function setReaderRouteState(isActive) {{
            const isCompact = isActive && window.innerHeight <= 520;
            document.documentElement.classList.toggle("reader-route", isActive);
            document.body.classList.toggle("reader-route", isActive);
            document.documentElement.classList.toggle("reader-compact", isCompact);
            document.body.classList.toggle("reader-compact", isCompact);
          }}

          function clearReaderFitObserver() {{
            if (readerFitObserver) {{
              readerFitObserver.disconnect();
              readerFitObserver = null;
            }}
          }}

          function scheduleReaderFit() {{
            if (routeInfo().name === "read") {{
              setReaderRouteState(true);
            }}
            if (fitFrame) {{
              window.cancelAnimationFrame(fitFrame);
            }}
            fitFrame = window.requestAnimationFrame(() => {{
              fitFrame = null;
              fitReaderText();
            }});
          }}

          function resetAutoplayIndicator() {{
            const progress = document.getElementById("autoplay-progress");
            const fill = document.getElementById("autoplay-progress-fill");
            if (!progress || !fill) return;
            progress.classList.remove("active");
            fill.style.transition = "none";
            fill.style.transform = "scaleX(1)";
          }}

          function startAutoplayIndicator(durationMs) {{
            const progress = document.getElementById("autoplay-progress");
            const fill = document.getElementById("autoplay-progress-fill");
            if (!progress || !fill) return;
            progress.classList.add("active");
            fill.style.transition = "none";
            fill.style.transform = "scaleX(1)";
            void fill.offsetWidth;
            window.requestAnimationFrame(() => {{
              fill.style.transition = `transform ${{durationMs}}ms linear`;
              fill.style.transform = "scaleX(0)";
            }});
          }}

          function favoriteId(chapterIndex, blockIndex) {{
            return `fav-${{chapterIndex}}-${{blockIndex}}`;
          }}

          function noteId(chapterIndex, blockIndex) {{
            return `note-${{chapterIndex}}-${{blockIndex}}`;
          }}

          function chapterProgressEntry(chapterIndex) {{
            return state.chapterProgress[String(chapterIndex)] || {{
              lastBlockIndex: 0,
              completedBlocks: [],
              progressPercent: 0,
              completed: false,
              updatedAt: "",
            }};
          }}

          function updateProgress(chapterIndex, blockIndex) {{
            const totalBlocks = chapters[chapterIndex]?.blocks.length || 1;
            const key = String(chapterIndex);
            const entry = chapterProgressEntry(chapterIndex);
            const completedBlocks = new Set(entry.completedBlocks);
            completedBlocks.add(blockIndex);
            state.chapterProgress[key] = {{
              lastBlockIndex: blockIndex,
              completedBlocks: Array.from(completedBlocks).sort((a, b) => a - b),
              progressPercent: Math.round((completedBlocks.size / totalBlocks) * 100),
              completed: blockIndex >= totalBlocks - 1,
              updatedAt: nowIso(),
            }};
            state.lastPosition = {{ chapterIndex, blockIndex }};
            saveState();
          }}

          function getFavorite(chapterIndex, blockIndex) {{
            const id = favoriteId(chapterIndex, blockIndex);
            return state.favorites.find((favorite) => favorite.id === id) || null;
          }}

          function toggleFavorite(chapterIndex, blockIndex) {{
            const chapter = chapters[chapterIndex];
            const block = chapter.blocks[blockIndex];
            const id = favoriteId(chapterIndex, blockIndex);
            const existing = getFavorite(chapterIndex, blockIndex);
            if (existing) {{
              state.favorites = state.favorites.filter((favorite) => favorite.id !== id);
            }} else {{
              state.favorites.push({{
                id,
                chapterIndex,
                blockIndex,
                chapterTitle: chapter.title,
                text: block.text,
                image: block.image,
                createdAt: nowIso(),
              }});
            }}
            saveState();
          }}

          function getNote(chapterIndex, blockIndex) {{
            const id = noteId(chapterIndex, blockIndex);
            return state.notes.find((note) => note.id === id) || null;
          }}

          function upsertNote(chapterIndex, blockIndex, comment) {{
            const chapter = chapters[chapterIndex];
            const block = chapter.blocks[blockIndex];
            const id = noteId(chapterIndex, blockIndex);
            const existing = getNote(chapterIndex, blockIndex);
            const timestamp = nowIso();
            if (existing) {{
              existing.comment = comment;
              existing.updatedAt = timestamp;
              existing.chapterTitle = chapter.title;
              existing.blockText = block.text;
              existing.image = block.image;
            }} else {{
              state.notes.push({{
                id,
                chapterIndex,
                blockIndex,
                chapterTitle: chapter.title,
                blockText: block.text,
                comment,
                image: block.image,
                createdAt: timestamp,
                updatedAt: timestamp,
              }});
            }}
            saveState();
          }}

          function deleteNote(id) {{
            state.notes = state.notes.filter((note) => note.id !== id);
            saveState();
          }}

          function deriveHooks(chaptersList) {{
            const embeddedHooks = readJsonScript("hook-data");
            if (Array.isArray(embeddedHooks) && embeddedHooks.length) {{
              return embeddedHooks;
            }}
            const candidates = [];
            const seen = new Set();
            for (const chapter of chaptersList) {{
              for (const block of chapter.blocks.slice(0, 4)) {{
                const firstSentence = String(block.text).split(/(?<=[.!?])\\s+/)[0].trim();
                const candidate = firstSentence.endsWith("?") ? firstSentence : String(block.text).trim();
                const wordTotal = candidate.split(/\\s+/).filter(Boolean).length;
                if (wordTotal >= 5 && wordTotal <= 18 && !seen.has(candidate)) {{
                  seen.add(candidate);
                  candidates.push(candidate);
                }}
              }}
            }}
            return candidates.length ? candidates : [chaptersList[0]?.blocks[0]?.text || "Start reading."];
          }}

          function hookOfTheMoment() {{
            if (!hooks.length) return "Start reading.";
            const day = Math.floor(Date.now() / 86400000);
            return hooks[day % hooks.length];
          }}

          function readJsonScript(id) {{
            const node = document.getElementById(id);
            if (!node) return null;
            try {{
              return JSON.parse(node.textContent || "null");
            }} catch {{
              return null;
            }}
          }}

          async function loadChapters() {{
            try {{
              const response = await fetch("data/chapters.json", {{ cache: "no-store" }});
              if (!response.ok) throw new Error(`Unexpected status ${{response.status}}`);
              return await response.json();
            }} catch {{
              const embedded = readJsonScript("chapters-data");
              if (Array.isArray(embedded)) {{
                return embedded;
              }}
              throw new Error("Unable to load chapters.json");
            }}
          }}

          function clampPosition(chapterIndex, blockIndex) {{
            const safeChapterIndex = Math.min(Math.max(chapterIndex, 0), Math.max(chapters.length - 1, 0));
            const blocks = chapters[safeChapterIndex]?.blocks || [];
            const safeBlockIndex = Math.min(Math.max(blockIndex, 0), Math.max(blocks.length - 1, 0));
            return {{ chapterIndex: safeChapterIndex, blockIndex: safeBlockIndex }};
          }}

          function routeInfo() {{
            const hash = window.location.hash || "#/home";
            const trimmed = hash.replace(/^#\\/?/, "");
            const segments = trimmed.split("/").filter(Boolean);
            const primary = segments[0] || "home";
            if (primary === "read") {{
              return {{
                name: "read",
                chapterIndex: safeInt(Number(segments[1]), 0),
                blockIndex: safeInt(Number(segments[2]), 0),
              }};
            }}
            return {{ name: primary }};
          }}

          function navigateTo(hash) {{
            window.location.hash = hash;
          }}

          function setActiveNav(name) {{
            for (const link of navLinks) {{
              link.classList.toggle("active", link.dataset.nav === name);
            }}
          }}

          function progressBar(percent) {{
            return `
              <div class="progress-row">
                <div class="progress-bar" aria-hidden="true"><div class="progress-fill" style="width: ${{percent}}%"></div></div>
                <span>${{percent}}%</span>
              </div>
            `;
          }}

          function renderBrandHeader() {{
            return `
              <header class="brand-header">
                <a class="brand-link" href="https://wakenai.com" aria-label="WakenAI">
                  <img
                    src="assets/images/{BRAND_LOGO_NAME}"
                    alt="WakenAI"
                    onerror="this.onerror=null;this.src='../assets/brand/{BRAND_LOGO_NAME}';"
                  >
                </a>
              </header>
            `;
          }}

          function renderHome() {{
            const last = clampPosition(state.lastPosition.chapterIndex, state.lastPosition.blockIndex);
            const lastChapter = chapters[last.chapterIndex];
            const currentBlock = lastChapter.blocks[last.blockIndex];
            const entry = chapterProgressEntry(last.chapterIndex);
            const hook = hookOfTheMoment();
            appRoot.innerHTML = `
              <section class="screen">
                <div class="screen-stack">
                  ${{renderBrandHeader()}}
                  <article class="hero-card home-card" style="background-image: url('${{escapeAttribute(currentBlock.image)}}')">
                    <div class="hero-copy">
                      <p class="eyebrow">Story reader</p>
                      <h1 class="hero-title">${{escapeHtml(BOOK_TITLE)}}</h1>
                      <p class="hero-subtitle">{html.escape(BOOK_SUBTITLE)}</p>
                      <p class="hero-hook">${{escapeHtml(hook)}}</p>
                      <p class="resume-meta">Resume with ${{escapeHtml(lastChapter.title)}} · ${{entry.progressPercent || 0}}% complete</p>
                      <div class="button-row">
                        <a class="button primary" href="#/read/${{last.chapterIndex}}/${{last.blockIndex}}">Continue reading</a>
                        <a class="button" href="#/index">Choose a chapter</a>
                        <a class="button" href="{BOOK_LANDING_URL}">HTML book</a>
                        <a class="button" href="{RESEARCH_PAPER_URL}">Research paper</a>
                      </div>
                    </div>
                  </article>
                </div>
              </section>
            `;
            setActiveNav("home");
          }}

          function renderIndex() {{
            const cards = chapters.map((chapter, chapterIndex) => {{
              const entry = chapterProgressEntry(chapterIndex);
              const actionLabel = entry.progressPercent > 0 ? "Continue" : "Start";
              const blockIndex = Math.min(entry.lastBlockIndex || 0, chapter.blocks.length - 1);
              return `
                <article class="chapter-card">
                  <div class="chapter-cover" style="background-image: url('${{escapeAttribute(chapter.blocks[0].image)}}')"></div>
                  <div class="chapter-body">
                    <p class="meta-label">Chapter ${{String(chapterIndex).padStart(2, "0")}}</p>
                    <h2>${{escapeHtml(chapter.title)}}</h2>
                    <p>${{escapeHtml(chapter.blocks[0].text)}}</p>
                    ${{progressBar(entry.progressPercent)}}
                    <div class="button-row">
                      <a class="button primary" href="#/read/${{chapterIndex}}/${{blockIndex}}">${{actionLabel}}</a>
                    </div>
                  </div>
                </article>
              `;
            }}).join("");
            appRoot.innerHTML = `
              <section class="screen">
                ${{renderBrandHeader()}}
                <div class="section-head">
                  <div>
                    <p class="eyebrow">Index</p>
                    <h1>Read out of order.</h1>
                  </div>
                  <p>Each chapter tracks its own progress, so the reader can move by mood, topic, or urgency.</p>
                </div>
                <div class="chapter-grid">${{cards}}</div>
              </section>
            `;
            setActiveNav("index");
          }}

          function renderFavorites() {{
            const favorites = [...state.favorites].sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)));
            if (!favorites.length) {{
              appRoot.innerHTML = renderEmptyState("Favorites", "Save the blocks you want to revisit later.");
              setActiveNav("favorites");
              return;
            }}
            const cards = favorites.map((favorite) => `
              <article class="saved-card">
                <div class="saved-thumb" style="background-image: url('${{escapeAttribute(favorite.image)}}')"></div>
                <div class="saved-body">
                  <p class="saved-meta">${{escapeHtml(favorite.chapterTitle)}} · Block ${{favorite.blockIndex + 1}}</p>
                  <p class="saved-snippet">${{escapeHtml(favorite.text)}}</p>
                  <div class="saved-actions">
                    <a class="button primary" href="#/read/${{favorite.chapterIndex}}/${{favorite.blockIndex}}">Return to block</a>
                  </div>
                </div>
              </article>
            `).join("");
            appRoot.innerHTML = `
              <section class="screen">
                ${{renderBrandHeader()}}
                <div class="section-head">
                  <div>
                    <p class="eyebrow">Favorites</p>
                    <h1>Saved fragments.</h1>
                  </div>
                  <p>Every saved block keeps its chapter title, exact location, and image context.</p>
                </div>
                <div class="saved-grid">${{cards}}</div>
              </section>
            `;
            setActiveNav("favorites");
          }}

          function renderNotes() {{
            const notes = [...state.notes].sort((a, b) => String(b.updatedAt || b.createdAt).localeCompare(String(a.updatedAt || a.createdAt)));
            if (!notes.length) {{
              appRoot.innerHTML = renderEmptyState("Notes", "Add a private note from any reading block.");
              setActiveNav("notes");
              return;
            }}
            const cards = notes.map((note) => `
              <article class="saved-card">
                <div class="saved-thumb" style="background-image: url('${{escapeAttribute(note.image)}}')"></div>
                <div class="saved-body">
                  <p class="saved-meta">${{escapeHtml(note.chapterTitle)}} · Block ${{note.blockIndex + 1}} · ${{formatDate(note.updatedAt || note.createdAt)}}</p>
                  <p class="saved-snippet">${{escapeHtml(note.blockText)}}</p>
                  <p>${{escapeHtml(note.comment)}}</p>
                  <div class="saved-actions">
                    <a class="button primary" href="#/read/${{note.chapterIndex}}/${{note.blockIndex}}">Return to block</a>
                    <button data-edit-note="${{note.id}}">Edit note</button>
                    <button class="danger" data-delete-note="${{note.id}}">Delete</button>
                  </div>
                </div>
              </article>
            `).join("");
            appRoot.innerHTML = `
              <section class="screen">
                ${{renderBrandHeader()}}
                <div class="section-head">
                  <div>
                    <p class="eyebrow">Notes</p>
                    <h1>Private annotations.</h1>
                  </div>
                  <p>Notes stay local to this browser and always jump back to the exact block that prompted them.</p>
                </div>
                <div class="saved-grid">${{cards}}</div>
              </section>
            `;
            bindNotesScreenActions();
            setActiveNav("notes");
          }}

          function renderEmptyState(label, message) {{
            return `
              <section class="screen">
                ${{renderBrandHeader()}}
                <div class="section-head">
                  <div>
                    <p class="eyebrow">${{escapeHtml(label)}}</p>
                    <h1>Nothing here yet.</h1>
                  </div>
                </div>
                <article class="panel empty-state">
                  <h2>${{escapeHtml(message)}}</h2>
                  <p>Use the reader to save favorites or capture private notes as you move through the book.</p>
                </article>
              </section>
            `;
          }}

          function renderReader(chapterIndex, blockIndex) {{
            const safe = clampPosition(chapterIndex, blockIndex);
            const chapter = chapters[safe.chapterIndex];
            const block = chapter.blocks[safe.blockIndex];
            clearAutoplayTimer();
            updateProgress(safe.chapterIndex, safe.blockIndex);
            const entry = chapterProgressEntry(safe.chapterIndex);
            const favorite = getFavorite(safe.chapterIndex, safe.blockIndex);
            const note = getNote(safe.chapterIndex, safe.blockIndex);
            appRoot.innerHTML = `
              <section class="screen reader-screen">
                <article class="reader-stage" style="background-image: url('${{escapeAttribute(block.image)}}')">
                  <div class="reader-copy">
                    <div class="reader-frame">
                      <div class="reader-header">
                        <div class="reader-topline">
                          <span class="reader-chapter">${{escapeHtml(chapter.title)}}</span>
                          <span class="reader-progress">${{entry.progressPercent}}%</span>
                        </div>
                        <div class="reader-progress-bar" aria-hidden="true">
                          <div class="progress-fill" style="width: ${{entry.progressPercent}}%"></div>
                        </div>
                      </div>
                      <div class="reader-main">
                          <div class="reader-fit-area">
                            <div class="reader-text-panel">
                              <div class="reader-text-body">
                                <p class="reader-text">${{escapeHtml(block.text)}}</p>
                              </div>
                            </div>
                          </div>
                      </div>
                      <div class="reader-footer">
                        <div class="reader-autoplay-progress ${{isAutoplaying ? "active" : ""}}" id="autoplay-progress" aria-hidden="true">
                          <div class="reader-autoplay-fill" id="autoplay-progress-fill"></div>
                        </div>
                        <div class="reader-actions">
                          <button
                            class="icon-button ${{favorite ? "active" : ""}}"
                            id="favorite-toggle"
                            type="button"
                            aria-label="${{favorite ? "Remove favorite" : "Save favorite"}}"
                            aria-pressed="${{favorite ? "true" : "false"}}"
                            title="${{favorite ? "Remove favorite" : "Save favorite"}}"
                          >
                            <span class="reader-icon" aria-hidden="true">${{favorite ? "favorite" : "favorite_border"}}</span>
                            <span class="sr-only">${{favorite ? "Remove favorite" : "Save favorite"}}</span>
                          </button>
                          <button
                            class="icon-button ${{note ? "active" : ""}}"
                            id="note-toggle"
                            type="button"
                            aria-label="${{note ? "Edit note" : "Add note"}}"
                            aria-pressed="${{note ? "true" : "false"}}"
                            title="${{note ? "Edit note" : "Add note"}}"
                          >
                            <span class="reader-icon" aria-hidden="true">edit_note</span>
                            <span class="sr-only">${{note ? "Edit note" : "Add note"}}</span>
                          </button>
                          <button
                            class="icon-button ${{isAutoplaying ? "active" : ""}}"
                            id="autoplay-toggle"
                            type="button"
                            aria-label="${{isAutoplaying ? "Pause autoplay" : "Start autoplay"}}"
                            aria-pressed="${{isAutoplaying ? "true" : "false"}}"
                            title="${{isAutoplaying ? "Pause autoplay" : "Start autoplay"}}"
                          >
                            <span class="reader-icon" aria-hidden="true">${{isAutoplaying ? "pause" : "play_arrow"}}</span>
                            <span class="sr-only">${{isAutoplaying ? "Pause autoplay" : "Start autoplay"}}</span>
                          </button>
                          <button
                            class="icon-button"
                            id="next-toggle"
                            type="button"
                            aria-label="Next block"
                            title="Next block"
                          >
                            <span class="reader-icon" aria-hidden="true">skip_next</span>
                            <span class="sr-only">Next block</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </article>
              </section>
            `;
            document.getElementById("autoplay-toggle")?.addEventListener("click", (event) => {{
              event.stopPropagation();
              if (isAutoplaying) {{
                stopAutoplay();
              }} else {{
                isAutoplaying = true;
                autoplayGeneration += 1;
              }}
              renderCurrentRoute();
            }});
            document.getElementById("favorite-toggle")?.addEventListener("click", (event) => {{
              event.stopPropagation();
              toggleFavorite(safe.chapterIndex, safe.blockIndex);
              renderCurrentRoute();
            }});
            document.getElementById("note-toggle")?.addEventListener("click", (event) => {{
              event.stopPropagation();
              openNoteDialog(safe.chapterIndex, safe.blockIndex);
            }});
            document.getElementById("next-toggle")?.addEventListener("click", (event) => {{
              event.stopPropagation();
              advanceReader(safe.chapterIndex, safe.blockIndex, 1, {{ preserveAutoplay: isAutoplaying }});
            }});
            bindReaderGestures(safe.chapterIndex, safe.blockIndex);
            bindReaderFitObserver();
            scheduleReaderFit();
            if (document.fonts?.ready) {{
              document.fonts.ready.then(() => scheduleReaderFit()).catch(() => scheduleReaderFit());
            }}
            if (isAutoplaying) {{
              scheduleAutoplay(safe.chapterIndex, safe.blockIndex);
            }} else {{
              resetAutoplayIndicator();
            }}
            setActiveNav("");
          }}

          function bindReaderFitObserver() {{
            clearReaderFitObserver();
            const stage = document.querySelector(".reader-stage");
            const fitArea = document.querySelector(".reader-fit-area");
            const textPanel = document.querySelector(".reader-text-panel");
            if (!stage || !fitArea || !textPanel || typeof ResizeObserver !== "function") return;
            readerFitObserver = new ResizeObserver(() => {{
              setReaderRouteState(routeInfo().name === "read");
              scheduleReaderFit();
            }});
            readerFitObserver.observe(stage);
            readerFitObserver.observe(fitArea);
            readerFitObserver.observe(textPanel);
          }}

          function fitReaderText() {{
            const textBody = document.querySelector(".reader-text-body");
            const text = document.querySelector(".reader-text");
            if (!textBody || !text) return;
            const isDesktop = window.matchMedia("(min-width: 760px)").matches && window.innerHeight >= 640;
            const minSize = isDesktop ? 16 : 14;
            const maxSize = isDesktop ? 60 : 46;
            let low = minSize;
            let high = maxSize;
            let best = minSize;
            while (low <= high) {{
              const mid = Math.floor((low + high) / 2);
              text.style.setProperty("--reader-font-size", `${{mid}}px`);
              if (textBody.scrollHeight <= textBody.clientHeight && textBody.scrollWidth <= textBody.clientWidth) {{
                best = mid;
                low = mid + 1;
              }} else {{
                high = mid - 1;
              }}
            }}
            text.style.setProperty("--reader-font-size", `${{best}}px`);
          }}

          function bindReaderGestures(chapterIndex, blockIndex) {{
            const stage = document.querySelector(".reader-stage");
            if (!stage) return;
            stage.addEventListener("click", (event) => {{
              if (event.target.closest("button")) return;
              const bounds = stage.getBoundingClientRect();
              const relativeX = event.clientX - bounds.left;
              if (relativeX > bounds.width / 2) {{
                stepReader(chapterIndex, blockIndex, 1);
              }} else {{
                stepReader(chapterIndex, blockIndex, -1);
              }}
            }});
            stage.addEventListener("touchstart", (event) => {{
              const touch = event.changedTouches[0];
              touchStart = {{ x: touch.clientX, y: touch.clientY }};
            }}, {{ passive: true }});
            stage.addEventListener("touchend", (event) => {{
              if (!touchStart) return;
              const touch = event.changedTouches[0];
              const dx = touch.clientX - touchStart.x;
              const dy = touch.clientY - touchStart.y;
              touchStart = null;
              if (Math.abs(dx) < 24 && Math.abs(dy) < 24) return;
              if (Math.abs(dx) > Math.abs(dy)) {{
                stepReader(chapterIndex, blockIndex, dx < 0 ? 1 : -1);
              }} else {{
                stepReader(chapterIndex, blockIndex, dy < 0 ? 1 : -1);
              }}
            }}, {{ passive: true }});
          }}

          function scheduleAutoplay(chapterIndex, blockIndex) {{
            clearAutoplayTimer();
            if (!isAutoplaying) return;
            const chapter = chapters[chapterIndex];
            const block = chapter?.blocks?.[blockIndex];
            if (!chapter || !block) {{
              stopAutoplay();
              return;
            }}
            if (blockIndex >= chapter.blocks.length - 1) {{
              stopAutoplay();
              renderCurrentRoute();
              return;
            }}
            const delay = getAutoplayDelay(block.text);
            const generation = autoplayGeneration;
            startAutoplayIndicator(delay);
            autoplayTimerId = window.setTimeout(() => {{
              autoplayTimerId = null;
              if (!isAutoplaying || generation !== autoplayGeneration) return;
              const route = routeInfo();
              if (route.name !== "read") {{
                stopAutoplay();
                return;
              }}
              if (route.chapterIndex !== chapterIndex || route.blockIndex !== blockIndex) {{
                scheduleAutoplay(route.chapterIndex, route.blockIndex);
                return;
              }}
              if (blockIndex >= chapter.blocks.length - 1) {{
                stopAutoplay();
                renderCurrentRoute();
                return;
              }}
              navigateTo(`#/read/${{chapterIndex}}/${{blockIndex + 1}}`);
            }}, delay);
          }}

          function nextReaderPosition(chapterIndex, blockIndex, direction) {{
            const chapter = chapters[chapterIndex];
            const nextBlockIndex = blockIndex + direction;
            if (nextBlockIndex >= 0 && nextBlockIndex < chapter.blocks.length) {{
              return {{ chapterIndex, blockIndex: nextBlockIndex }};
            }}
            const nextChapterIndex = chapterIndex + direction;
            if (nextChapterIndex >= 0 && nextChapterIndex < chapters.length) {{
              return {{
                chapterIndex: nextChapterIndex,
                blockIndex: direction > 0 ? 0 : chapters[nextChapterIndex].blocks.length - 1,
              }};
            }}
            return null;
          }}

          function advanceReader(chapterIndex, blockIndex, direction, options = {{}}) {{
            const target = nextReaderPosition(chapterIndex, blockIndex, direction);
            if (!target) {{
              if (options.preserveAutoplay) {{
                stopAutoplay();
                renderCurrentRoute();
              }}
              return;
            }}
            if (options.preserveAutoplay) {{
              autoplayGeneration += 1;
              clearAutoplayTimer();
              resetAutoplayIndicator();
            }}
            navigateTo(`#/read/${{target.chapterIndex}}/${{target.blockIndex}}`);
          }}

          function stepReader(chapterIndex, blockIndex, direction) {{
            advanceReader(chapterIndex, blockIndex, direction);
          }}

          function openNoteDialog(chapterIndex, blockIndex) {{
            if (isAutoplaying) {{
              stopAutoplay();
              renderCurrentRoute();
            }}
            const chapter = chapters[chapterIndex];
            const block = chapter.blocks[blockIndex];
            const existing = getNote(chapterIndex, blockIndex);
            activeNoteContext = {{ chapterIndex, blockIndex, noteId: existing?.id || null }};
            noteTitle.textContent = existing ? "Edit note" : "Add a note";
            noteContext.textContent = `${{chapter.title}} · Block ${{blockIndex + 1}}`;
            noteInput.value = existing?.comment || "";
            noteDelete.hidden = !existing;
            if (typeof noteDialog.showModal === "function") {{
              noteDialog.showModal();
            }}
          }}

          function closeNoteDialog() {{
            activeNoteContext = null;
            if (noteDialog.open) {{
              noteDialog.close();
            }}
          }}

          function bindNotesScreenActions() {{
            document.querySelectorAll("[data-edit-note]").forEach((button) => {{
              button.addEventListener("click", () => {{
                const note = state.notes.find((entry) => entry.id === button.getAttribute("data-edit-note"));
                if (!note) return;
                openNoteDialog(note.chapterIndex, note.blockIndex);
              }});
            }});
            document.querySelectorAll("[data-delete-note]").forEach((button) => {{
              button.addEventListener("click", () => {{
                const id = button.getAttribute("data-delete-note");
                if (!id) return;
                deleteNote(id);
                renderCurrentRoute();
              }});
            }});
          }}

          function escapeHtml(value) {{
            return String(value)
              .replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#39;");
          }}

          function escapeAttribute(value) {{
            return escapeHtml(value).replace(/`/g, "&#96;");
          }}

          function formatDate(value) {{
            const date = new Date(value);
            if (Number.isNaN(date.valueOf())) return "Saved locally";
            return date.toLocaleString(undefined, {{
              month: "short",
              day: "numeric",
              hour: "numeric",
              minute: "2-digit",
            }});
          }}

          function renderCurrentRoute() {{
            const route = routeInfo();
            setReaderRouteState(route.name === "read");
            if (route.name !== "read") {{
              clearReaderFitObserver();
            }}
            if (route.name !== "read") {{
              stopAutoplay();
            }}
            switch (route.name) {{
              case "home":
                renderHome();
                break;
              case "index":
                renderIndex();
                break;
              case "favorites":
                renderFavorites();
                break;
              case "notes":
                renderNotes();
                break;
              case "read":
                renderReader(route.chapterIndex, route.blockIndex);
                break;
              default:
                navigateTo("#/home");
            }}
          }}

          async function init() {{
            chapters = await loadChapters();
            hooks = deriveHooks(chapters);
            loadState();
            if (!window.location.hash) {{
              navigateTo("#/home");
              return;
            }}
            renderCurrentRoute();
          }}

          noteForm.addEventListener("submit", (event) => {{
            event.preventDefault();
            if (!activeNoteContext) return;
            const comment = noteInput.value.trim();
            if (!comment) {{
              closeNoteDialog();
              return;
            }}
            upsertNote(activeNoteContext.chapterIndex, activeNoteContext.blockIndex, comment);
            closeNoteDialog();
            renderCurrentRoute();
          }});

          noteCancel.addEventListener("click", () => {{
            closeNoteDialog();
            if (routeInfo().name === "read") {{
              renderCurrentRoute();
            }}
          }});
          noteDelete.addEventListener("click", () => {{
            if (!activeNoteContext?.noteId) return;
            deleteNote(activeNoteContext.noteId);
            closeNoteDialog();
            renderCurrentRoute();
          }});

          window.addEventListener("hashchange", () => renderCurrentRoute());
          window.addEventListener("resize", () => {{
            setReaderRouteState(routeInfo().name === "read");
            if (fitTimer) window.clearTimeout(fitTimer);
            fitTimer = window.setTimeout(() => {{
              if (routeInfo().name === "read") {{
                scheduleReaderFit();
              }}
            }}, 60);
          }});
          window.addEventListener("orientationchange", () => {{
            setReaderRouteState(routeInfo().name === "read");
            if (routeInfo().name === "read") {{
              scheduleReaderFit();
            }}
          }});
          window.addEventListener("keydown", (event) => {{
            const route = routeInfo();
            if (route.name !== "read" || noteDialog.open) return;
            if (["ArrowRight", "ArrowDown"].includes(event.key)) {{
              event.preventDefault();
              stepReader(route.chapterIndex, route.blockIndex, 1);
            }}
            if (["ArrowLeft", "ArrowUp"].includes(event.key)) {{
              event.preventDefault();
              stepReader(route.chapterIndex, route.blockIndex, -1);
            }}
          }});

          init().catch((error) => {{
            appRoot.innerHTML = `
              <section class="screen">
                <article class="panel empty-state">
                  <p class="eyebrow">Reader unavailable</p>
                  <h2>Unable to load the story reader.</h2>
                  <p>${{escapeHtml(error.message || "Unknown error")}}</p>
                </article>
              </section>
            `;
          }});
        }})();
        """
    )


def build_website_bundle(root: Path, website_root: Path) -> None:
    if website_root.exists():
        shutil.rmtree(website_root)
    ensure_dir(website_root)
    ensure_dir(website_root / "assets" / "css")
    ensure_dir(website_root / "assets" / "js")
    ensure_dir(website_root / "assets" / "images")
    ensure_dir(website_root / "data")
    copy_brand_logo(root, website_root)
    chapter_paths = sorted((root / "book" / "chapters").glob("*.md"), key=chapter_sort_key)
    image_map: dict[Path, str] = {}
    chapters = [serialize_chapter(root, website_root, chapter_path, image_map) for chapter_path in chapter_paths]
    hooks = derive_hook_candidates(chapters)

    dump_json(website_root / "data" / "chapters.json", chapters)
    overwrite(website_root / "index.html", render_index_html(chapters, hooks))
    overwrite(website_root / "assets" / "css" / "app.css", render_css())
    overwrite(website_root / "assets" / "js" / "app.js", render_js())
    overwrite(website_root / "README.md", generate_readme())


def rewrite_chapters_for_pages_mirror(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rewritten: list[dict[str, Any]] = []
    for chapter in chapters:
        rewritten_blocks: list[dict[str, str]] = []
        for block in chapter["blocks"]:
            image = block["image"]
            if image.startswith("assets/images/generated/"):
                image = image.replace("assets/images/generated/", "../book/assets/generated/", 1)
            rewritten_blocks.append({"text": block["text"], "image": image})
        rewritten.append({"title": chapter["title"], "blocks": rewritten_blocks})
    return rewritten


def mirror_website_bundle(website_root: Path, site_root: Path) -> None:
    mirror_root = site_root / "website"
    if mirror_root.exists():
        shutil.rmtree(mirror_root)
    shutil.copytree(website_root, mirror_root)

    chapters_path = mirror_root / "data" / "chapters.json"
    chapters = json.loads(chapters_path.read_text(encoding="utf-8"))
    dump_json(chapters_path, rewrite_chapters_for_pages_mirror(chapters))

    generated_images_root = mirror_root / "assets" / "images" / "generated"
    if generated_images_root.exists():
        shutil.rmtree(generated_images_root)


def publish_website_bundle(root: Path, site_root: Path | None = None) -> None:
    website_root = root / "website"
    build_website_bundle(root, website_root)
    target_site_root = site_root if site_root is not None else root / "build" / "site"
    if target_site_root.exists():
        mirror_website_bundle(website_root, target_site_root)


def build_website(root: Path) -> None:
    publish_website_bundle(root)
