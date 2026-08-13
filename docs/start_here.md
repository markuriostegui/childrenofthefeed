# Start Here

This is the first-stop document for anyone arriving fresh to the project: a new researcher, a new maintainer, or a new conversation that needs to resume work without relying on prior chat context.

## What This Project Is

AI Empire is a research OS and publication program. It documents a cumulative argument from surveillance capitalism to AI imperialism and organizes that argument into a disciplined evidence system and a professional publication package.

The project is not open-ended. It is investigative first, but it accumulates toward three explicit reforms:

- `Refactor Section 230`
- `AI Weights as Patrimony of Humanity`
- `Limit Government Capture by AI Companies`

## What Is Canonical

Use these layers as the source of truth:

- `vectors/`: evidence collection and synthesis by topic
- `sources/`, `claims/`, `profiles/`, `timelines/`: global registries
- `chapters/`: canonical reference-corpus narrative layer
- `papers/`: canonical standalone paper layer
- `volumes/`: canonical omnibus and corpus companion source layer
- `book/`: canonical literary/public edition source layer

Generated HTML, TeX, and PDF outputs under `build/` are publication artifacts, not the place to edit content. The GitHub Pages bundle lives under `build/site/`.

## How the Publication Package Works

The researcher-facing system has four coordinated outputs:

1. Standalone chapter papers
2. One omnibus dossier volume
3. One corpus companion / audit volume
4. One literary/public edition under **Children of the Feed. Servants of the AI God**

The literary edition now has its own maintainable production stack:

- `book/chapters/` for chapter prose
- `book/print/` for the dedicated trade-book print layer, QR-note manifests, print manuscripts, and vendored fonts
- `book/assets/generated/covers/` for chapter covers
- `book/assets/generated/illustrations/` for narrative scenes
- `book/assets/generated/infographics/` for branded infographic plates
- `book/assets/prompts/` for the prompt-source documents
- `book/assets/asset_manifest.json` for asset provenance and prompt/model traceability

Do not treat the literary branch as a styling layer only. It is now a first-class publication layer with its own content, art direction, web workflow, and separate print-composition workflow.

The print branch has a fixed editorial object model that should be preserved unless the project deliberately changes edition design:

1. the full-book PDF opens with a 4-page front matter sequence
2. page 1 is the full-bleed cover
3. page 2 is the title/imprint page
4. page 3 is the `Ad Magnificam Humanitatem` dedication page
5. page 4 is the full-book TOC
6. each standalone chapter PDF mirrors that logic with its own 4-page opening block before chapter text
7. the full-book print target is a near-100-page 6x9 trade-book object, with a working acceptance band of `96–104` pages

The quickest entry point for published outputs is:

- [build/site/index.html](/Users/hassan/repos/AI-Empire/build/site/index.html)

The academic-only local package is also available at:

- [build/publication/index.html](/Users/hassan/repos/AI-Empire/build/publication/index.html)

## Recommended Reading Order for a New Contributor

1. [project_map.md](/Users/hassan/repos/AI-Empire/docs/project_map.md)
2. [research_workflow.md](/Users/hassan/repos/AI-Empire/docs/research_workflow.md)
3. [contributor_manual.md](/Users/hassan/repos/AI-Empire/docs/contributor_manual.md)
4. [editorial_and_citation_manual.md](/Users/hassan/repos/AI-Empire/docs/editorial_and_citation_manual.md)
5. [maintainer_manual.md](/Users/hassan/repos/AI-Empire/docs/maintainer_manual.md)

If you are resuming after a pause or in a new thread, then read:

- [resume_and_republish_runbook.md](/Users/hassan/repos/AI-Empire/docs/resume_and_republish_runbook.md)

If you are using the work as an outside researcher rather than extending it, read:

- [researcher_guide.md](/Users/hassan/repos/AI-Empire/docs/researcher_guide.md)

If your task is specifically to publish or republish the public site, also read:

- [github_pages_release.md](/Users/hassan/repos/AI-Empire/docs/github_pages_release.md)
- [publication_completion_audit.md](/Users/hassan/repos/AI-Empire/docs/publication_completion_audit.md)

Historical planning and audit documents such as `completion_audit.md`, `next_execution_plan.md`, and `first_collection_run.md` are preserved as checkpoints, not as the current operating manuals.

## First 15 Minutes

If you need to orient fast:

1. Read [project_map.md](/Users/hassan/repos/AI-Empire/docs/project_map.md).
2. Open [build/site/index.html](/Users/hassan/repos/AI-Empire/build/site/index.html).
3. Read [build/reviews/publication_qc.md](/Users/hassan/repos/AI-Empire/build/reviews/publication_qc.md).
4. Check [papers/appendix/README.md](/Users/hassan/repos/AI-Empire/papers/appendix/README.md) for current corpus totals.
5. Read [publication_completion_audit.md](/Users/hassan/repos/AI-Empire/docs/publication_completion_audit.md) for the current locally-proven state versus external deployment state.
6. Use the runbook to decide whether your task is evidence intake, synthesis, revision, or republication.

## Operating Rule

Evidence moves in one direction:

`source -> note -> claim -> entity/timeline -> vector synthesis -> chapter corpus -> papers/volumes -> export/QA`

If something is not stable in the evidence layer, it should not be stabilized in polished prose.
