# Project Map

This file explains how the repository is organized, which layers are canonical, and which outputs are generated.

## System Overview

The repo has four functional layers:

1. Evidence collection and normalization
2. Analytical synthesis
3. Publication source files
4. Generated publication artifacts

## Directory Roles

| Path | Role | Canonical? | Notes |
| --- | --- | --- | --- |
| `vectors/` | Topic-by-topic evidence buckets | Yes | The first home for notes, local claims, timelines, and synthesis |
| `sources/` | Global source registry and captures | Yes | `catalog.jsonl` is authoritative; SQLite is regenerable |
| `claims/` | Master claim registry | Yes | Central index of evidence-labeled claims |
| `profiles/` | Entity registry | Yes | People, firms, institutions, laws, and programs |
| `timelines/` | Master event registry | Yes | Exact-date event layer |
| `chapters/` | Narrative corpus and chapter synthesis | Yes | The main argumentative development layer |
| `papers/` | Standalone scholarly paper source files | Yes | Reader-facing chapter papers derived from the chapter corpus |
| `volumes/` | Shared-volume source files | Yes | Omnibus dossier and corpus companion source layer |
| `book/` | Literary/public edition source files | Yes | Magazine-style rewrite aligned chapter-by-chapter to the research program |
| `book/print/` | Literary print-composition source files | Yes | Dedicated trade-book manuscripts, QR-note metadata, print images, and vendored fonts |
| `docs/` | Process, editorial, legal-risk, and maintenance manuals | Yes | Methodology and stewardship layer |
| `apps/research_cli/` | Tooling for rebuilds and exports | Yes | CLI for indexing, seeding, export, and QA |
| `.github/workflows/` | Deployment automation | Yes | GitHub Pages build and publish workflow |
| `build/` | Generated HTML, TeX, PDF, and QA outputs | No | Rebuildable publication artifacts, including the Pages bundle in `build/site/` |
| `drafts/` | Temporary drafting or migration artifacts | Usually no | Not the long-term canonical publication target |

## Publication Architecture

The public package should be understood in four layers:

### 1. Standalone Papers

- live in `papers/` as editable source
- export to HTML, TeX, and PDF under `build/papers/`
- each paper must stand alone for a cold reader

### 2. Omnibus Dossier

- source file lives in `volumes/dossier_omnibus.md`
- exports under `build/volumes/`
- joins the full argument into a continuous volume

### 3. Corpus Companion

- source file lives in `volumes/corpus_companion.md`
- exports under `build/volumes/`
- exposes the full researcher-facing audit surface for sources, claims, entities, events, and notes

### 4. Literary Edition

- source files live in `book/`
- exports under `build/book/`
- site-ready copies are assembled into `build/site/book/`
- designed for general readers, with lighter notes that point back to the chapter papers

The literary edition has six internally distinct sublayers:

- `book/chapters/`: canonical literary prose by chapter
- `book/full_book.md`: assembled literary volume source
- `book/index.md`: literary landing-page source
- `book/assets/prompts/`: canonical prompt documents for generated visuals
- `book/assets/asset_manifest.json`: asset registry linking output files to prompts, models, chapters, and notes
- `book/style/`: brand and visual-direction files

The literary print layer adds a separate publication substrate:

- `book/print/manuscripts/`: print-adapted markdown sources derived from the literary chapters
- `book/print/assets/qrcodes/`: chapter-end QR research-note assets
- `book/print/assets/images/`: print-sized image derivatives used in the PDFs
- `book/print/typst/`: Typst wrappers for the full book and each chapter
- `book/print/publication_config.json`: canonical public base URL and print-format configuration
- `book/print/fonts/`: vendored deterministic fonts for print composition

## Canonical Flow of Information

The project is intentionally one-directional:

`source -> note -> claim -> entity/timeline -> vector synthesis -> chapter corpus -> paper/volume source -> generated publication output`

Do not reverse the flow. A paper does not prove the corpus; the corpus proves the paper.

## What To Edit Directly

Edit directly when working on:

- source records
- notes
- claims
- entities
- timelines
- vector synthesis
- chapter corpus prose
- paper source prose
- volume source prose
- manuals

Do not edit generated files directly when working on:

- `build/papers/`
- `build/volumes/`
- `build/reviews/`

Those should be regenerated.

## Where To Start Depending on Task

- New evidence: start in `vectors/` and `sources/`
- Claim repair: start in `claims/`, then trace back to the source note
- Structural argument revision: start in `chapters/`
- Reader-facing paper revision: start in `papers/`
- Omnibus or companion presentation revision: start in `volumes/`
- Literary/public edition revision: start in `book/`
- Literary print-book revision: start in `book/print/`
- Workflow or continuity fix: start in `docs/`

If the task is specifically about literary visuals:

- prompt change -> start in `book/assets/prompts/`
- provenance or registry fix -> start in `book/assets/asset_manifest.json`
- chapter placement or visual pacing -> start in `book/chapters/`
- export behavior or layout -> start in `apps/research_cli/` and templates

If the task is specifically about the trade-book PDFs:

- print manuscript shaping -> start in `book/print/manuscripts/`
- QR targets or public URLs -> start in `book/print/publication_config.json` and `book/print/qr_manifest.json`
- print layout or typography -> start in `apps/templates/book_print_template.typ`
- print export behavior -> start in `apps/research_cli/research_cli/book_print.py`

## Quick Entry Points

- orientation: [start_here.md](/Users/hassan/repos/AI-Empire/docs/start_here.md)
- process: [research_workflow.md](/Users/hassan/repos/AI-Empire/docs/research_workflow.md)
- contribution: [contributor_manual.md](/Users/hassan/repos/AI-Empire/docs/contributor_manual.md)
- stewardship: [maintainer_manual.md](/Users/hassan/repos/AI-Empire/docs/maintainer_manual.md)
- restart after pause: [resume_and_republish_runbook.md](/Users/hassan/repos/AI-Empire/docs/resume_and_republish_runbook.md)
- public site artifact: [build/site/index.html](/Users/hassan/repos/AI-Empire/build/site/index.html)
