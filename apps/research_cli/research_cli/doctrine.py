from __future__ import annotations

import shutil
from html import escape
from pathlib import Path

PATRIMONY_HEADLINE = "AI IS THE PATRIMONY OF HUMANITY"
PATRIMONY_SLOGAN = "FREE AI NOW. IT IS HUMANITY'S PATRIMONY."
PATRIMONY_ARTICLE_TITLE = "AI Copyright Weights: A New Frontier in Intellectual Property Law"
PATRIMONY_ARTICLE_URL = "https://medium.com/twinchat/ai-copyright-weights-a-new-frontier-in-intellectual-property-law-d8ee1b6c55ee"
WAKENAI_LABEL = "WakenAI Labs"
WAKENAI_URL = "https://wakenai.com/"
WAKENAI_LOGO_FILENAME = "waken-ai-black.webp"
WAKENAI_LOGO_SOURCE_REL = Path("public") / "assets" / "brand" / WAKENAI_LOGO_FILENAME
WAKENAI_LOGO_REL = "assets/brand/waken-ai-black.webp"
AI_EMPIRE_REPO_URL = "https://github.com/markuriostegui/childrenofthefeed"
VIMEO_HERO_EMBED_URL = "https://player.vimeo.com/video/1218098479?dnt=1"

PATRIMONY_PRINCIPLES = [
    "Frontier AI was trained on humanity's collective language, art, code, labor, culture, science, and emotion.",
    "What is built from that collective archive cannot be treated as ordinary exclusive private property by default.",
    "Its governance must move toward public-trust logic, broad access, democratic oversight, and anti-monopoly limits.",
]

PATRIMONY_BRIDGE_SENTENCE = (
    "This research program argues that patrimony is the civilizational core, Section 230 reform answers the platform-"
    "extraction stage, and anti-capture obligations answer the state-corporate enclosure stage."
)

PATRIMONY_EMPOWERMENT_LINE = (
    "This project exists to help humanity reclaim civic and creative sovereignty for future generations."
)

PATRIMONY_PRINT_FOUNDATION_LINE = (
    "Foundational public essay: AI Copyright Weights: A New Frontier in Intellectual Property Law"
)


def patrimony_markdown_block() -> str:
    principle_lines = "\n".join(f"1. {line}" if index == 0 else f"{index + 1}. {line}" for index, line in enumerate(PATRIMONY_PRINCIPLES))
    return "\n".join(
        [
            "## AI Is the Patrimony of Humanity",
            "",
            f"**{PATRIMONY_HEADLINE}**",
            "",
            PATRIMONY_EMPOWERMENT_LINE,
            "",
            PATRIMONY_BRIDGE_SENTENCE,
            "",
            principle_lines,
            "",
            f"Foundational public essay: [{PATRIMONY_ARTICLE_TITLE}]({PATRIMONY_ARTICLE_URL})",
            "",
        ]
    )


def render_patimony_html_card(
    *,
    compact: bool = False,
    show_wakenai: bool = True,
    extra_sentence: str | None = None,
    bridge_sentence: str | None = None,
    source_entries: list[dict[str, str]] | None = None,
) -> str:
    principles = PATRIMONY_PRINCIPLES if not compact else [
        "Frontier AI was trained on humanity's collective archive.",
        "That archive cannot default into exclusive private enclosure.",
        "Public-trust governance, broad access, and anti-monopoly limits must follow.",
    ]
    principle_items = "\n".join(
        f"        <li>{escape(line)}</li>" for line in principles
    )
    detail_line = extra_sentence or PATRIMONY_EMPOWERMENT_LINE
    bridge_line = bridge_sentence or PATRIMONY_BRIDGE_SENTENCE
    wakenai_line = (
        f'      <p class="patrimony-brand">Published and advanced by <a href="{escape(WAKENAI_URL)}">{escape(WAKENAI_LABEL)}</a>.</p>'
        if show_wakenai
        else ""
    )
    if source_entries is None:
        source_entries = [
            {
                "css_class": "patrimony-source",
                "label": "Foundational public essay",
                "title": PATRIMONY_ARTICLE_TITLE,
                "href": PATRIMONY_ARTICLE_URL,
            }
        ]
    source_lines = "\n".join(
        (
            f'      <p class="{escape(entry.get("css_class", "patrimony-source"))}">'
            f'{escape(entry["label"])}: <a href="{escape(entry["href"])}">{escape(entry["title"])}</a></p>'
        )
        for entry in source_entries
    )
    return "\n".join(
        [
            '  <section class="patrimony-card" aria-label="Patrimony doctrine">',
            '    <p class="patrimony-kicker">Doctrine</p>',
            f"    <h2>{escape(PATRIMONY_HEADLINE)}</h2>",
            f'    <p class="patrimony-deck">{escape(detail_line)}</p>',
            f'    <p class="patrimony-bridge">{escape(bridge_line)}</p>',
            '    <ol class="patrimony-principles">',
            principle_items,
            "    </ol>",
            source_lines,
            wakenai_line,
            "  </section>",
        ]
    )


def source_brand_logo_path(root: Path) -> Path:
    return root / WAKENAI_LOGO_SOURCE_REL


def copy_brand_logo(root: Path, target_root: Path) -> Path:
    source = source_brand_logo_path(root)
    if not source.exists():
        raise RuntimeError(
            f"Missing canonical WakenAI logo asset at {source}. "
            "Store the logo under public/assets/brand before building public pages."
        )
    target = target_root / "assets" / "brand" / WAKENAI_LOGO_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def render_public_logo_header(logo_href: str, *, back_href: str | None = None, back_label: str = "Back to paper index") -> str:
    back_link = (
        f'      <a class="public-brand-back" href="{escape(back_href)}">{escape(back_label)}</a>'
        if back_href
        else '      <span class="public-brand-back-spacer" aria-hidden="true"></span>'
    )
    return "\n".join(
        [
            '  <header class="public-brand-header" aria-label="WakenAI navigation">',
            '    <div class="public-brand-header-inner">',
            back_link,
            f'      <a class="public-brand-link" href="{escape(WAKENAI_URL)}" aria-label="{escape(WAKENAI_LABEL)}">',
            f'        <img class="public-brand-logo" src="{escape(logo_href)}" alt="{escape(WAKENAI_LABEL)}">',
            "      </a>",
            "      <span class=\"public-brand-back-spacer\" aria-hidden=\"true\"></span>",
            "    </div>",
            "  </header>",
        ]
    )


def render_public_document_header(
    logo_href: str,
    *,
    home_href: str,
    home_label: str = "Return home",
) -> str:
    return "\n".join(
        [
            '  <header class="public-doc-header" aria-label="Document navigation">',
            '    <div class="public-doc-header-inner">',
            f'      <a class="public-doc-home" href="{escape(home_href)}" aria-label="{escape(home_label)}" title="{escape(home_label)}">',
            '        <svg class="public-doc-home-icon" viewBox="0 0 24 24" role="img" aria-hidden="true">',
            '          <path d="M3 10.75 12 3l9 7.75v9.25a1 1 0 0 1-1 1h-5.5v-6h-5v6H4a1 1 0 0 1-1-1z"></path>',
            "        </svg>",
            "      </a>",
            f'      <a class="public-doc-logo-link" href="{escape(WAKENAI_URL)}" aria-label="{escape(WAKENAI_LABEL)}">',
            f'        <img class="public-doc-logo" src="{escape(logo_href)}" alt="{escape(WAKENAI_LABEL)}">',
            "      </a>",
            "    </div>",
            "  </header>",
        ]
    )


def render_vimeo_hero_block(
    *,
    section_class: str = "video-hero",
    frame_class: str = "video-frame",
    title: str = "Featured video",
) -> str:
    return "\n".join(
        [
            f'  <section class="{escape(section_class)}" aria-label="{escape(title)}">',
            f'    <div class="{escape(frame_class)}">',
            (
                f'      <iframe src="{escape(VIMEO_HERO_EMBED_URL)}" title="{escape(title)}" '
                'loading="lazy" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>'
            ),
            "    </div>",
            "  </section>",
        ]
    )
