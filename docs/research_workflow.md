# Research Workflow

This is the canonical end-to-end process document for the project.

If you are new, read this after:

1. [start_here.md](/Users/hassan/repos/AI-Empire/docs/start_here.md)
2. [project_map.md](/Users/hassan/repos/AI-Empire/docs/project_map.md)

## Workflow Principle

The project is built as a one-directional evidence system. Work should move in this order:

`source -> note -> claim -> entity/timeline -> vector synthesis -> chapter corpus -> papers/volumes -> export/QA`

This order exists to stop the prose layer from outrunning the evidence layer.

## Work Modes

Most tasks belong to one of four modes:

### 1. Evidence Intake

Use when new material is being added to the corpus.

You should:

1. select the correct vector
2. add or capture the source
3. normalize it into a note
4. register claims
5. update entities and timeline if needed

### 2. Analytical Synthesis

Use when the evidence already exists but the vector logic is weak or incomplete.

You should:

1. update vector summaries
2. refresh local claim indexes
3. update chapter bridges
4. confirm overclaim boundaries

### 3. Narrative Revision

Use when the corpus is stable enough to change the argument layer.

You should:

1. update `chapters/` first
2. then update affected `papers/`
3. then update `volumes/` if the omnibus or companion source should change
4. then update `book/` if the public-literary edition should reflect the change

### 4. Literary / Visual Revision

Use when the research-backed literary edition, chapter pacing, or generated visual program needs work.

You should:

1. update `book/chapters/` for literary prose changes
2. update `book/assets/prompts/` before generating any new visual
3. if the change affects infographics, update `book/assets/prompts/v3_infographic_text_prompts.md`
4. rerun `generate-book-assets --kind infographics` so the request bundle matches the current manifest and prompt refs
5. generate or replace the asset
6. register the output in `book/assets/asset_manifest.json`
7. rerun `export-book` so the HTML literary edition is current
8. if the public trade-book PDFs changed, rerun `export-book-print`
9. rerun `build-site`
10. rerun `review-publication`

### 5. Publication Rebuild

Use when the source layers are already correct and the deliverable needs regeneration.

You should:

1. rebuild indexes if evidence changed
2. reseed paper derivatives if needed
3. rebuild the master volume layer
4. export publication artifacts
5. rerun QA

For local PDF regeneration:

- `export-papers` and the shared academic volumes still depend on the academic export pipeline
- `export-book` is the literary HTML/web export only
- `export-book-print` is the dedicated 6x9 trade-book PDF export through Typst
- `build-site` is the canonical one-command public rebuild once canonical sources are ready; it refreshes papers, volumes, literary HTML, literary print PDFs, and the site bundle in one pass

The literary print branch is not a browser print of the HTML edition. It is a separate editorial composition system with these expectations:

- the full-book PDF begins with the fixed 4-page front matter sequence
- each standalone chapter PDF begins with its own mirrored 4-page opening sequence
- chapter-end QR research notes remain part of the print artifact
- the literary HTML layer keeps the ceremonial dedication/imprint block at the end of the landing page, the full book, and every chapter page
- the full-book print target is a deliberate near-100-page object, not a minimal fit export

## Detailed Flow

### Step 1. Collect and Register a Source

Add a source only when it materially strengthens a vector, clarifies a chapter-level claim, or improves one of the three reform arcs.

Always preserve:

- exact date
- exact URL
- correct source tier
- correct source type
- vector assignment

### Step 2. Normalize Into a Note

Every source must become a note before it becomes an argument.

Each note should clearly state:

- `Factual Summary`
- `Key Quotes or Findings`
- `What It Proves`
- `What It Suggests`
- `What It Does Not Prove`
- `Reliability`
- `Claims It Supports`
- `Risk Label`

### Step 3. Register Claims

Claims must stay tied to what the note genuinely supports.

Allowed labels:

- `Documented Fact`
- `Disputed Fact`
- `Hypothesis / Interpretation`
- `Speculative Narrative Risk`

### Step 4. Update Entities and Timelines

Only add entities and events that materially help the explanatory structure of the dossier.

Use timelines for:

- dated turning points
- procedural milestones
- policy changes
- corporate or institutional decisions

### Step 5. Refresh Vector Synthesis

Before touching prose, make sure the vector reflects the new evidence.

Typical vector updates:

- local claim index
- local timeline index
- vector report or summary
- `chapter_bridge.md`

### Step 6. Update the Chapter Corpus

`chapters/` is the canonical narrative development layer.

Use it to:

- consolidate the best evidence into prose
- preserve reform-bearing transitions
- distinguish fact from interpretation
- anchor strong factual paragraphs to source IDs

### Step 7. Update Papers and Volumes

After `chapters/` is correct:

- revise the relevant standalone paper in `papers/`
- revise `volumes/dossier_omnibus.md` if the continuous argument changed
- revise `volumes/corpus_companion.md` only when the audit presentation or corpus registry framing changed
- revise the relevant `book/chapters/*.md` files if the literary/public edition should reflect the update
- if the literary chapter requires new art, add or revise the prompt-source document first, then update the asset manifest after generation

### Step 8. Export and QA

Use the CLI to regenerate derived outputs.

Canonical commands:

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

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli review-publication --root /Users/hassan/repos/AI-Empire
```

## Literary Branch Maintenance Rules

For the `book/` layer:

- chapter prose is canonical in `book/chapters/`, not in `build/book/`
- prompt design happens before image generation and must be preserved in `book/assets/prompts/`
- every generated visual used in the book should be present in `book/assets/asset_manifest.json`
- chapter placement of images should be controlled from the markdown chapter source, not by hand-editing exported HTML
- `book/print/` is the dedicated print-composition layer for the literary edition
- the canonical public base URL for QR research notes lives in `book/print/publication_config.json`
- rebuilds should be treated as required after any prose, prompt, asset, or public-URL change

## Reform Alignment Check

The workflow is not neutral about destination. Every mature update should strengthen one or more of these arcs:

- `01` and `02` -> `Refactor Section 230`
- `04`, `05`, `06` -> `AI Weights as Patrimony of Humanity`
- `07`, `08` -> `Limit Government Capture by AI Companies`
- `09` -> explains why all three reforms are necessary together
- `10` -> states the reforms directly

If a contribution does not improve a documented arc, it usually should remain queued or peripheral.

## Related Manuals

- [contributor_manual.md](/Users/hassan/repos/AI-Empire/docs/contributor_manual.md)
- [maintainer_manual.md](/Users/hassan/repos/AI-Empire/docs/maintainer_manual.md)
- [editorial_and_citation_manual.md](/Users/hassan/repos/AI-Empire/docs/editorial_and_citation_manual.md)
- [resume_and_republish_runbook.md](/Users/hassan/repos/AI-Empire/docs/resume_and_republish_runbook.md)
