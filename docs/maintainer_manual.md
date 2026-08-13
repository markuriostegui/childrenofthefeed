# Maintainer Manual

## Purpose

This repository is the canonical English-language research OS for the AI Empire program. It is designed to be expandable, auditable, and republishable without losing evidence discipline, editorial clarity, or the project's three-reform end state:

- `Refactor Section 230`
- `AI Weights as Patrimony of Humanity`
- `Limit Government Capture by AI Companies`

This manual is for long-term stewardship. If you are new to the repo, start first with:

- [start_here.md](/Users/hassan/repos/AI-Empire/docs/start_here.md)
- [project_map.md](/Users/hassan/repos/AI-Empire/docs/project_map.md)
- [resume_and_republish_runbook.md](/Users/hassan/repos/AI-Empire/docs/resume_and_republish_runbook.md)
- [publication_completion_audit.md](/Users/hassan/repos/AI-Empire/docs/publication_completion_audit.md)
- [github_pages_release.md](/Users/hassan/repos/AI-Empire/docs/github_pages_release.md) when the task includes live-site publication

## Canonical vs Generated Artifacts

### Canonical editable layers

- `vectors/`
- `sources/`
- `claims/`
- `profiles/`
- `timelines/`
- `chapters/`
- `papers/`
- `volumes/`
- `book/`
- `docs/`
- `apps/research_cli/`
- `.github/workflows/`

### Generated layers

- `build/papers/`
- `build/volumes/`
- `build/book/`
- `build/site/`
- `build/reviews/`

Generated artifacts should be rebuilt, not edited directly.

## Publication Package

The researcher-facing package has four public surfaces:

1. standalone chapter papers
2. the omnibus dossier volume
3. the corpus companion / audit volume
4. the literary/public edition under `book/`

The fastest public entry point is:

- [build/site/index.html](/Users/hassan/repos/AI-Empire/build/site/index.html)

The source layers for that package are:

- `papers/` for standalone papers
- `volumes/dossier_omnibus.md` for the omnibus
- `volumes/corpus_companion.md` for the companion
- `book/` for the literary/public edition

The literary/public edition now includes its own maintainable visual program:

- `book/chapters/` for canonical literary prose
- `book/assets/prompts/` for prompt-source documents
- `book/assets/generated/covers/` for chapter covers
- `book/assets/generated/illustrations/` for chapter scenes
- `book/assets/generated/infographics/` for branded infographic plates
- `book/assets/generated/requests/` for manifest-driven regeneration bundles
- `book/assets/asset_manifest.json` for asset provenance

The literary/public edition also has a separate print-composition layer:

- `book/print/manuscripts/` for print-adapted markdown sources
- `book/print/assets/qrcodes/` for chapter-end research-note QR assets
- `book/print/assets/images/` for print-sized image derivatives
- `book/print/typst/` for the Typst wrappers
- `book/print/publication_config.json` for the canonical public base URL and print metadata
- `book/print/fonts/` for vendored deterministic fonts

The print branch has fixed edition rules that future maintainers should preserve unless the book is intentionally redesigned:

- the full-book PDF uses 4 fixed opening pages before Chapter 00
- page 1 is the full-bleed cover only
- page 2 is the title/imprint page
- page 3 is the `Ad Magnificam Humanitatem` dedication page
- page 4 is the full-book TOC with resolved page numbers
- visible folios are suppressed on those opening pages and resume with chapter content
- every standalone chapter PDF mirrors the same 4-page opening logic with a chapter opener, chapter imprint page, dedication page, and local mini TOC
- chapter-end QR research notes remain the public documentary bridge for the print edition
- the current full-book acceptance target is a `96–104` page 6x9 trade-book object

## Canonical Research Flow

Maintain the repo in this order:

1. capture or ingest source
2. normalize source into a note
3. register claims
4. update entities if needed
5. update timeline if needed
6. refresh vector synthesis and chapter bridges
7. update chapter corpus prose
8. update paper, volume, or literary-book prose
9. rebuild exports and rerun QA

Do not reverse the flow. The corpus proves the prose; the prose does not prove the corpus.

## Resume and Audit Responsibilities

When inheriting the repo after a pause, a new thread, or a handoff, the maintainer should first confirm:

- current corpus totals
- current publication outputs
- current QA status
- whether the requested work is evidence intake, synthesis, narrative revision, or publication rebuild

Use the runbook for the quick version:

- [resume_and_republish_runbook.md](/Users/hassan/repos/AI-Empire/docs/resume_and_republish_runbook.md)

Minimum audit pass before making changes:

1. read [papers/appendix/README.md](/Users/hassan/repos/AI-Empire/papers/appendix/README.md)
2. read [build/reviews/publication_qc.md](/Users/hassan/repos/AI-Empire/build/reviews/publication_qc.md)
3. read [publication_completion_audit.md](/Users/hassan/repos/AI-Empire/docs/publication_completion_audit.md)
4. open [build/site/index.html](/Users/hassan/repos/AI-Empire/build/site/index.html)
5. identify the exact layer that needs work

## When To Add a Source

Add a source only if at least one of the following is true:

- it materially strengthens a weak vector
- it adds a new primary or top-tier procedural record
- it sharpens a chapter-level claim already active in the dossier
- it preserves exact-date discipline for a sensitive claim
- it materially strengthens one of the three reform arcs

Leave a candidate in `queue.md` when:

- it is colorful but not structurally useful
- it duplicates stronger material already in the repo
- it supports only guilt by association
- it does not materially improve a claim, vector, chapter, paper, or reform burden

## Evidence Discipline

Every note must state:

- `Factual Summary`
- `Key Quotes or Findings`
- `What It Proves`
- `What It Suggests`
- `What It Does Not Prove`
- `Reliability`
- `Claims It Supports`
- `Risk Label`

Every claim must use one of these labels:

- `Documented Fact`
- `Disputed Fact`
- `Hypothesis / Interpretation`
- `Speculative Narrative Risk`

Do not promote interpretive language into `Documented Fact`. Do not hide weak support inside polished prose.

## When To Update Which Layer

### Update only a vector when:

- new evidence has been ingested but the narrative consequences are not yet stable
- the note/claim/entity/timeline work is still being normalized
- the addition does not yet warrant prose revision

### Update `chapters/` when:

- the vector synthesis has changed enough to affect the narrative argument
- a chapter's factual basis, interpretive boundary, or transition logic changed
- a reform-bearing arc needs stronger traceability

### Update `papers/` when:

- a chapter change affects standalone paper intelligibility
- paper-local citations, notes, or appendices need refresh
- a paper's body or bibliography no longer matches the corpus

### Update `volumes/` when:

- the omnibus needs argument or navigation refresh
- the companion needs registry framing or audit-structure refresh
- counts, crosswalks, or public audit explanations changed

### Update `book/` when:

- a chapter change should reach the public-literary edition
- research-basis notes need to point to a different paper or stronger framing
- visual placement, chapter decks, or transitions need refinement
- GitHub Pages or reader-facing magazine presentation changed

### Update `book/print/` when:

- the trade-book PDFs need better composition or typography
- QR targets, fallback URLs, or chapter-end research notes changed
- the public literary PDFs need different image curation than the web edition
- the canonical GitHub Pages base URL changed

### Update `book/assets/prompts/` when:

- a new cover, illustration, or infographic is required
- prompt wording must be revised to match the brand or avoid generation issues
- the literary visual program changes in scope or direction

### Update `book/assets/asset_manifest.json` when:

- a generated asset is added or replaced
- prompt provenance changes
- a chapter reassigns an asset
- an output file path or notes field changes

## Handling Drift

Drift usually appears in one of four ways:

1. chapter prose changed but paper prose did not
2. paper citations changed but bibliography or appendix did not
3. corpus totals changed but the companion or appendix registry did not
4. manuals still describe a superseded workflow

When drift is detected:

1. fix the highest canonical layer first
2. propagate forward only after the upstream layer is correct
3. rerun export and QA

Never patch a generated PDF or HTML output to hide an upstream inconsistency.

## Rebuild Commands

Rebuild from the repo root with:

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli build-index --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli seed-papers --root /Users/hassan/repos/AI-Empire --overwrite
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli build-master-paper --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli export-papers --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli seed-book --root /Users/hassan/repos/AI-Empire --overwrite
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli generate-book-assets --root /Users/hassan/repos/AI-Empire --kind infographics
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli export-book --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli export-book-print --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli review-book-print --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli build-site --root /Users/hassan/repos/AI-Empire
```

`build-site` is the canonical public-artifact assembly step. It now rebuilds the main Pages root and republishes the story reader subtree at `build/site/website/` in the same pass. The Pages copy intentionally reuses shared public book imagery to keep deployments lighter, while local `website/` remains self-contained for standalone preview.

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli review-publication --root /Users/hassan/repos/AI-Empire
```

For local publication work:

- `export-papers` and the academic shared volumes still use the academic PDF pipeline
- `export-book` now maintains the literary HTML/web layer only
- `export-book-print` is the dedicated 6x9 trade-book PDF pipeline through Typst
- `build-site` is the canonical one-command public rebuild after canonical source layers are updated; it refreshes the papers, shared volumes, literary HTML, literary print PDFs, and the Pages/site bundle together

On a fresh local machine, install what each layer needs:

- for the web/book HTML QA path: Playwright plus Chromium
- for the print-book PDF path: Typst plus the vendored fonts already committed under `book/print/fonts/`

If Playwright-backed HTML review is part of the pass, run:

```bash
playwright install chromium
```

If Tectonic is being used directly or as a fallback in a new environment, it may still need unrestricted bundle download before PDF export succeeds.

If the local Python environment is missing `pypdf`, use the bundled Codex runtime for QA:

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
/Users/hassan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
-m research_cli.cli review-publication --root /Users/hassan/repos/AI-Empire
```

## Republication Lifecycle

Use this sequence whenever a meaningful update needs to go back out as a refreshed publication package:

1. confirm the scope of the evidence change
2. update notes, claims, entities, and timeline as needed
3. refresh vector synthesis
4. refresh affected chapter corpus files
5. refresh affected papers
6. refresh `volumes/` if the omnibus or companion changed
7. refresh `book/` if the public-literary edition changed
8. rebuild indexes and exports
9. rerun publication QA
10. record what changed for the next maintainer

If `book/` changed and you want the public artifacts refreshed reliably from one command, the minimum rebuild set is:

1. `build-site`
2. `review-publication`

If you are iterating only on the literary layer before a final public rebuild, you can still use:

1. `export-book`
2. `export-book-print`

If the change touched literary print composition, also confirm:

1. the full-book front matter still follows the 4-page opening rule
2. standalone chapter PDFs still follow the mirrored 4-page opening rule
3. the dedication page still renders all 13 lines correctly
4. the full-book page count still lands inside the accepted `96–104` range
5. chapter-end QR research notes still resolve under `https://markuriostegui.github.io/childrenofthefeed/`

## What Must Be Checked Before Calling a Publication Pass Complete

- no uncited sensitive claim in chapters, papers, or volumes
- no chapter drift away from the three reforms
- no raw repo path exposed as reader-facing evidence support
- no broken source IDs in papers or volumes
- no stale corpus totals in reader-facing audit surfaces
- no outdated links in bibliography, notes, or public indexes
- no appendix references that point nowhere
- no named-individual material added without structural relevance and risk review
- no manual that still describes a superseded publication model

## Release Notes for the Next Researcher

After a meaningful pass, leave a concise written trace that tells the next maintainer:

- what changed
- which layer changed first
- which chapters or papers were refreshed
- whether counts changed
- whether exports and QA were rerun
- what remains unstable or queued
