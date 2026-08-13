from __future__ import annotations

import re
from pathlib import Path

from .constants import CHAPTERS
from .fs import overwrite

MASTER_FILENAME = "11_children-of-the-feed-servants-of-the-ai-god_paper.md"
MASTER_TITLE = "Children of the Feed. Servants of the AI God"
MASTER_SUBTITLE = "A synthesis paper derived from the AI Empire research series"


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


def extract_section(content: str, heading: str) -> str:
    pattern = rf"{re.escape(heading)}\n\n(.*?)(?:\n## |\Z)"
    match = re.search(pattern, content, re.S)
    return match.group(1).strip() if match else ""


def split_paragraphs(text: str) -> list[str]:
    return [chunk.strip() for chunk in re.split(r"\n\s*\n", text.strip()) if chunk.strip()]


def clean_text(text: str) -> str:
    text = re.sub(r"\^\[Sources:\s.*?\]", "", text, flags=re.S)
    text = text.replace("`", "")
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        lines.append(stripped)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def first_sentence(text: str) -> str:
    compact = clean_text(text)
    if not compact:
        return ""
    match = re.search(r"(.+?[.!?])(?:\s|$)", compact)
    if match:
        return match.group(1).strip()
    return compact


def paper_metadata(root: Path) -> list[dict]:
    papers = []
    for chapter in CHAPTERS:
        matches = sorted((root / "papers").glob(f"{chapter['id']}_*_paper.md"))
        if not matches:
            continue
        path = matches[0]
        content = path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        title = frontmatter.get("title", path.stem)
        papers.append(
            {
                "chapter_id": chapter["id"],
                "chapter_title": chapter["title"],
                "path": path,
                "title": title,
                "content": content,
                "abstract": extract_section(content, "## Abstract"),
                "central_thesis": extract_section(content, "## Central Thesis"),
                "main_analysis": extract_section(content, "## Main Analysis"),
                "reform_relevance": extract_section(content, "## Reform Relevance"),
                "conclusion": extract_section(content, "## Conclusion"),
            }
        )
    return papers


def appendix_anchor(index: int, title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"appendix-a{index}-{slug}"


def appendix_link(index: int, title: str) -> str:
    return f"[Appendix A{index}](#{appendix_anchor(index, title)})"


def series_paper_link(entry: dict) -> str:
    stem = entry["path"].stem
    return f"[{entry['title']}]({stem}.html)"


def series_footnote(entries: list[dict], index_map: dict[str, int]) -> str:
    parts = []
    for entry in entries:
        index = index_map[entry["chapter_id"]]
        parts.append(
            f"AI Empire Research Program, {series_paper_link(entry)} (see {appendix_link(index, entry['title'])})"
        )
    return f"^[Series sources: {'; '.join(parts)}]"


def group(entries: list[dict], chapter_ids: list[str]) -> list[dict]:
    wanted = set(chapter_ids)
    return [entry for entry in entries if entry["chapter_id"] in wanted]


def synthesis_paragraph(entries: list[dict], index_map: dict[str, int]) -> str:
    pieces = []
    for entry in entries:
        sentence = first_sentence(entry["central_thesis"]) or first_sentence(entry["main_analysis"])
        if sentence:
            pieces.append(sentence)
    if not pieces:
        return ""
    return " ".join(pieces) + " " + series_footnote(entries, index_map)


def build_master_paper(root: Path) -> Path:
    entries = paper_metadata(root)
    index_map = {entry["chapter_id"]: idx for idx, entry in enumerate(entries, start=1)}

    feed_entries = group(entries, ["00", "01", "02", "03"])
    model_entries = group(entries, ["04", "05", "06"])
    empire_entries = group(entries, ["07", "08", "09", "10"])

    introduction = (
        "This paper synthesizes the full AI Empire research series into one researcher-facing argument. "
        "Its claim is that surveillance platforms first trained populations into life through interfaces, "
        "then converted that social dependence into data, then converted that data and labor into frontier-model capacity, "
        "and finally wrapped that capacity in state access, legitimacy, and reform-resistant power. "
        + series_footnote(entries, index_map)
    )

    historical_context = (
        "The argument begins before generative AI. The series shows that social media normalized free behavioral capture, "
        "youth dependence, algorithmic mediation, and platform indispensability long before frontier labs claimed to be building neutral intelligence infrastructure. "
        "COVID then accelerated dependency rather than originating it. "
        + series_footnote(feed_entries, index_map)
    )

    main_analysis = "\n\n".join(
        [
            "### I. Children of the Feed",
            synthesis_paragraph(feed_entries, index_map),
            (
                "Taken together, these papers support the dossier's first civilizational claim: populations were not merely entertained by the feed. "
                "They were habituated into an environment where attention, desire, social trust, and everyday coordination could be continuously captured, ranked, and redirected. "
                + series_footnote(feed_entries, index_map)
            ),
            "### II. Servants of the Model",
            synthesis_paragraph(model_entries, index_map),
            (
                "The middle layer of the series shows how captured expression becomes frontier capability. "
                "The legal ambiguity around training, the economic correction hidden beneath AI rhetoric, and the dual-use marketing of cheap yet dangerous intelligence all serve one enclosure logic: "
                "socially produced value is reissued as private model power. "
                + series_footnote(model_entries, index_map)
            ),
            "### III. Toward the AI God",
            synthesis_paragraph(empire_entries, index_map),
            (
                "The final layer of the series traces how that power is hardened. "
                "Compute chokepoints, national-security offerings, lobbying, governance restructuring, moral legitimation, and future-of-civilization rhetoric all elevate frontier firms beyond vendors. "
                "They begin to look like would-be custodians of intelligence infrastructure itself. "
                + series_footnote(empire_entries, index_map)
            ),
            "### IV. The Reform Synthesis",
            (
                "The series therefore converges on three reforms rather than a loose ethics wishlist: refactor Section 230 for sovereign-scale platform power; treat frontier AI weights as a patrimony problem rather than ordinary private property; and impose anti-capture obligations on AI firms that operate through public support, national-security channels, or strategic policy access. "
                + series_footnote(group(entries, ["01", "02", "04", "07", "08", "10"]), index_map)
            ),
        ]
    )

    counterarguments = (
        "The strongest counterargument is that this paper risks overstating systemic coherence. "
        "The series does not prove a single omniscient conspiracy. It proves a sequence of documented structures that reinforce one another: platform extraction, social weakening, contested training, financial enclosure, access control, and institutional capture. "
        "Where the evidence is interpretive, the underlying papers say so directly. "
        + series_footnote(group(entries, ["00", "03", "04", "08"]), index_map)
    )

    limits = (
        "This synthesis inherits the limits of the underlying papers. It does not claim that every frontier lab has fully disclosed its training stack, "
        "that the origin of COVID-19 is settled, or that current law already recognizes AI weights as public patrimony. "
        "It advances a bounded political reading built from the series' documented record. "
        + series_footnote(group(entries, ["03", "04", "10"]), index_map)
    )

    reform_relevance = (
        "As a final publication object, this paper exists to make the end state unmistakable. "
        "If the feed trains social dependence, if the model encloses collectively produced cognition, and if the frontier firm seeks privileged state alignment, then piecemeal reform is structurally inadequate. "
        "The response has to move at the level of infrastructure, property, and public power. "
        + series_footnote(group(entries, ["01", "04", "07", "08", "10"]), index_map)
    )

    conclusion = (
        "Children of the Feed. Servants of the AI God argues that contemporary AI power was not born in a vacuum. "
        "It was prepared socially by the feed, economically by enclosure, and politically by institutional capture. "
        "The project of resistance therefore cannot stop at critique. It has to reorganize platform liability, frontier-model ownership, and the terms on which governments may empower AI firms. "
        + series_footnote(group(entries, ["00", "09", "10"]), index_map)
    )

    reference_lines = []
    appendix_source_lines = []
    for index, entry in enumerate(entries, start=1):
        reference_lines.append(
            f"{index}. AI Empire Research Program. {series_paper_link(entry)}. Series paper. "
            f"Paper appendix: {appendix_link(index, entry['title'])}. Relevance: Supports the synthesis layer of this master paper."
        )
        appendix_source_lines.extend(
            [
                f"### Appendix A{index}. {entry['title']} {{#{appendix_anchor(index, entry['title'])}}}",
                f"**Series role:** Chapter {entry['chapter_id']} in the AI Empire publication set.",
                f"**Series paper link:** {series_paper_link(entry)}",
                f"**Why it matters in this paper:** {first_sentence(entry['reform_relevance']) or first_sentence(entry['central_thesis'])}",
                f"**Source layer:** Internal series paper",
                "",
            ]
        )

    claim_lines = [
        "### Appendix B1. The feed prepared the social conditions later exploited by frontier AI",
        "**Claim statement:** The AI Empire series supports the argument that large platforms first normalized social dependence, then translated that dependence into data capture and downstream model power.",
        "**Evidence status:** Hypothesis / Interpretation",
        f"**Source support:** {appendix_link(index_map['01'], next(entry['title'] for entry in entries if entry['chapter_id'] == '01'))}, {appendix_link(index_map['02'], next(entry['title'] for entry in entries if entry['chapter_id'] == '02'))}, {appendix_link(index_map['03'], next(entry['title'] for entry in entries if entry['chapter_id'] == '03'))}",
        "",
        "### Appendix B2. Frontier AI power is best understood as a problem of enclosure plus strategic access",
        "**Claim statement:** The strongest cumulative reading of the series is that frontier-model capability is socially derived, financially enclosed, and then hardened through privileged state and institutional access.",
        "**Evidence status:** Hypothesis / Interpretation",
        f"**Source support:** {appendix_link(index_map['04'], next(entry['title'] for entry in entries if entry['chapter_id'] == '04'))}, {appendix_link(index_map['05'], next(entry['title'] for entry in entries if entry['chapter_id'] == '05'))}, {appendix_link(index_map['07'], next(entry['title'] for entry in entries if entry['chapter_id'] == '07'))}, {appendix_link(index_map['08'], next(entry['title'] for entry in entries if entry['chapter_id'] == '08'))}",
        "",
        "### Appendix B3. The series converges on a three-reform doctrine rather than open-ended ethics",
        "**Claim statement:** The full publication set consistently supports a final program centered on Section 230 reform, patrimony-oriented governance of AI weights, and limits on government capture by AI firms.",
        "**Evidence status:** Documented Fact",
        f"**Source support:** {appendix_link(index_map['00'], next(entry['title'] for entry in entries if entry['chapter_id'] == '00'))}, {appendix_link(index_map['10'], next(entry['title'] for entry in entries if entry['chapter_id'] == '10'))}",
        "",
    ]

    timeline_lines = [
        "### Appendix C1. 2024-12-17: Congressional uptake of the weights argument",
        "**Event summary:** The series documents that the House AI Task Force report recorded the copyright / weights / compensation conflict in a bipartisan policy record.",
        f"**Source support:** {appendix_link(index_map['00'], next(entry['title'] for entry in entries if entry['chapter_id'] == '00'))}, {appendix_link(index_map['04'], next(entry['title'] for entry in entries if entry['chapter_id'] == '04'))}",
        "",
        "### Appendix C2. 2025-06: Government-specific frontier AI offerings become explicit",
        "**Event summary:** The series documents June 2025 as a key moment in which frontier AI firms publicly formalized government-only product lines and security-facing coordination.",
        f"**Source support:** {appendix_link(index_map['07'], next(entry['title'] for entry in entries if entry['chapter_id'] == '07'))}, {appendix_link(index_map['10'], next(entry['title'] for entry in entries if entry['chapter_id'] == '10'))}",
        "",
        "### Appendix C3. 2026-05-15: Moral legitimacy extends into the Vatican field",
        "**Event summary:** The series documents the expansion of AI legitimacy discourse into formal religious authority.",
        f"**Source support:** {appendix_link(index_map['08'], next(entry['title'] for entry in entries if entry['chapter_id'] == '08'))}",
        "",
    ]

    entity_lines = [
        "### Appendix D1. Meta",
        "**Entity type:** company",
        "**Role in this paper:** Archetype of the feed-era extraction platform and reputational redirection cycle.",
        f"**Relevant series papers:** {appendix_link(index_map['01'], next(entry['title'] for entry in entries if entry['chapter_id'] == '01'))}, {appendix_link(index_map['02'], next(entry['title'] for entry in entries if entry['chapter_id'] == '02'))}, {appendix_link(index_map['03'], next(entry['title'] for entry in entries if entry['chapter_id'] == '03'))}",
        "",
        "### Appendix D2. OpenAI",
        "**Entity type:** company",
        "**Role in this paper:** Core example of model enclosure, governance turbulence, and government-facing strategic repositioning.",
        f"**Relevant series papers:** {appendix_link(index_map['06'], next(entry['title'] for entry in entries if entry['chapter_id'] == '06'))}, {appendix_link(index_map['07'], next(entry['title'] for entry in entries if entry['chapter_id'] == '07'))}, {appendix_link(index_map['08'], next(entry['title'] for entry in entries if entry['chapter_id'] == '08'))}",
        "",
        "### Appendix D3. Anthropic",
        "**Entity type:** company",
        "**Role in this paper:** Core example of frontier legitimacy, safety rhetoric, and government-facing model access.",
        f"**Relevant series papers:** {appendix_link(index_map['06'], next(entry['title'] for entry in entries if entry['chapter_id'] == '06'))}, {appendix_link(index_map['07'], next(entry['title'] for entry in entries if entry['chapter_id'] == '07'))}, {appendix_link(index_map['08'], next(entry['title'] for entry in entries if entry['chapter_id'] == '08'))}",
        "",
    ]

    evidence_boundary_lines = [
        "### Appendix E1. Disputed Matters",
        "",
        "- The series does not treat the origin of COVID-19 as settled. See the Chapter 03 paper for the bounded formulation.",
        "",
        "### Appendix E2. Interpretive Boundaries",
        "",
        "- This master paper argues for a structural reading of extraction, enclosure, and capture. It does not claim a single omniscient conspiracy behind every event in the record.",
        "",
        "### Appendix E3. Speculative Narrative Risks",
        "",
        "- The series explicitly rejects the overclaim that current law already settles frontier AI weights as patrimony, public trust property, or common heritage.",
        "",
        "### Appendix E4. Sensitive or Review-Worthy Note Flags",
        "",
        "- Named-individual disputes remain bounded by the underlying Chapter 08 evidence rules and should not be read as guilt by association.",
        "",
    ]

    content = "\n".join(
        [
            "---",
            f'title: "{MASTER_TITLE}"',
            f'subtitle: "{MASTER_SUBTITLE}"',
            'author: ""',
            'date: ""',
            "lang: en-US",
            "---",
            "",
            "## Abstract",
            "",
            "This paper synthesizes the eleven-paper AI Empire series into one argument: the feed prepared the subject, the model enclosed the subject's output, and the frontier firm sought to govern the resulting intelligence infrastructure. The result is a cumulative case for three reforms: refactor Section 230, treat frontier AI weights as a patrimony problem, and limit government capture by AI companies.",
            "",
            "## Keywords",
            "",
            "surveillance capitalism; AI imperialism; Section 230 reform; AI weights; patrimony of humanity; government capture; platform power; research synthesis",
            "",
            "## Research Question",
            "",
            "What does the validated AI Empire paper series establish, taken as a whole, about the path from feed-based extraction to frontier AI enclosure and state-corporate alignment?",
            "",
            "## Scope and Framing Note",
            "",
            "This paper is the series-level synthesis document derived from the validated standalone papers in the AI Empire publication set. It is written to circulate independently, but it deliberately cites the chapter papers as its evidence spine so that readers can move from the final synthesis back into the deeper specialized arguments.",
            "",
            "## Central Thesis",
            "",
            "Children of the Feed. Servants of the AI God argues that contemporary AI power is not simply a technical breakthrough. It is the latest political form of a longer process in which platforms captured social life, converted that capture into model capability, and then sought to stabilize the resulting power through institutional access and legitimacy.",
            "",
            "## Evidence and Method Note",
            "",
            "This synthesis is built from the completed chapter papers in the AI Empire series. It treats those papers as validated internal sources, preserves their factual and interpretive boundaries, and advances only claims that can be grounded in the documented publication set.",
            "",
            "## Introduction",
            "",
            introduction,
            "",
            "## Historical or Institutional Context",
            "",
            historical_context,
            "",
            "## Main Analysis",
            "",
            main_analysis,
            "",
            "## Position Within the Series",
            "",
            "This paper closes the research program's first major publication cycle. Where the individual chapter papers defend narrower domains, this synthesis paper states the integrated argument they were building toward.",
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
            "This synthesis cites the validated chapter papers as its internal evidence base. Readers who want fuller external-source inspection should move from the cited series papers into the omnibus and companion volumes.",
            "",
            "## References / Bibliography",
            "",
            "\n".join(reference_lines),
            "",
            "## Appendix A. Source Register for This Paper",
            "",
            "\n".join(appendix_source_lines).strip(),
            "",
            "## Appendix B. Claims Used in This Paper",
            "",
            "\n".join(claim_lines).strip(),
            "",
            "## Appendix C. Timeline Slice",
            "",
            "\n".join(timeline_lines).strip(),
            "",
            "## Appendix D. Relevant Entities",
            "",
            "\n".join(entity_lines).strip(),
            "",
            "## Appendix E. Evidence Boundaries",
            "",
            "\n".join(evidence_boundary_lines).strip(),
            "",
        ]
    ).rstrip() + "\n"

    target_path = root / "papers" / MASTER_FILENAME
    overwrite(target_path, content)
    return target_path
