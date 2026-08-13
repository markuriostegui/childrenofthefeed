# Publication Completion Audit

This document records the current completion state of the publication system so a new researcher, maintainer, or fresh conversation can recover the project state without relying on prior chat history.

It distinguishes between:

- what is proven locally inside the repository
- what is generated and validated locally
- what still depends on external GitHub Pages execution

## Scope

This audit covers the current publication architecture:

1. canonical chapter corpus in `chapters/`
2. standalone scholarly papers in `papers/`
3. shared volumes in `volumes/`
4. literary/public edition in `book/`
5. public-site bundle in `build/site/`
6. continuity and methodology documentation in `docs/`
7. GitHub Pages deployment workflow in `.github/workflows/pages.yml`

## Canonical Layers Confirmed

The repo currently preserves the intended canonical separation:

- evidence and synthesis live in `vectors/`, `sources/`, `claims/`, `profiles/`, `timelines/`, and `chapters/`
- scholarly publication sources live in `papers/`
- omnibus and corpus-companion sources live in `volumes/`
- literary/public edition sources live in `book/`
- generated artifacts live under `build/`

This architecture is documented in:

- [start_here.md](/Users/hassan/repos/AI-Empire/docs/start_here.md)
- [project_map.md](/Users/hassan/repos/AI-Empire/docs/project_map.md)
- [research_workflow.md](/Users/hassan/repos/AI-Empire/docs/research_workflow.md)
- [maintainer_manual.md](/Users/hassan/repos/AI-Empire/docs/maintainer_manual.md)

## Corpus Totals Confirmed

The internal registry currently exposes these totals:

- Sources: `127`
- Claims: `475`
- Entities: `62`
- Events: `90`
- Notes: `141`

Primary audit surface:

- [papers/appendix/README.md](/Users/hassan/repos/AI-Empire/papers/appendix/README.md)

## Standalone Papers Confirmed

The standalone paper layer exists under:

- [papers/](/Users/hassan/repos/AI-Empire/papers)

The generated public outputs exist under:

- [build/site/papers/html](/Users/hassan/repos/AI-Empire/build/site/papers/html)
- [build/site/papers/pdf](/Users/hassan/repos/AI-Empire/build/site/papers/pdf)
- [build/site/papers/tex](/Users/hassan/repos/AI-Empire/build/site/papers/tex)

Current local validation confirms:

- required paper sections are present
- PDFs were generated
- external links are embedded in PDFs
- internal PDF navigation exists
- no placeholder leakage was detected in the reviewed papers

Primary QA surface:

- [build/reviews/publication_qc.md](/Users/hassan/repos/AI-Empire/build/reviews/publication_qc.md)

## Shared Volumes Confirmed

The source layer exists under:

- [volumes/dossier_omnibus.md](/Users/hassan/repos/AI-Empire/volumes/dossier_omnibus.md)
- [volumes/corpus_companion.md](/Users/hassan/repos/AI-Empire/volumes/corpus_companion.md)

Generated public outputs exist under:

- [build/site/volumes/html](/Users/hassan/repos/AI-Empire/build/site/volumes/html)
- [build/site/volumes/pdf](/Users/hassan/repos/AI-Empire/build/site/volumes/pdf)
- [build/site/volumes/tex](/Users/hassan/repos/AI-Empire/build/site/volumes/tex)

Local validation confirms:

- omnibus and companion both export successfully
- both volumes pass the current publication QA
- PDF link annotations are present
- internal navigation is present

## Literary Edition Confirmed

The literary/public source layer exists under:

- [book/](/Users/hassan/repos/AI-Empire/book)

Key source surfaces:

- [book/index.md](/Users/hassan/repos/AI-Empire/book/index.md)
- [book/full_book.md](/Users/hassan/repos/AI-Empire/book/full_book.md)
- [book/chapters](/Users/hassan/repos/AI-Empire/book/chapters)
- [book/style/brand_guide.md](/Users/hassan/repos/AI-Empire/book/style/brand_guide.md)
- [book/assets/asset_manifest.json](/Users/hassan/repos/AI-Empire/book/assets/asset_manifest.json)

Generated public outputs exist under:

- [build/site/book/index.html](/Users/hassan/repos/AI-Empire/build/site/book/index.html)
- [build/site/book/html](/Users/hassan/repos/AI-Empire/build/site/book/html)
- [build/site/book/pdf](/Users/hassan/repos/AI-Empire/build/site/book/pdf)

Local validation confirms:

- all literary chapter pages export
- full-book HTML and PDF export
- chapter cards and full-book links exist on the literary landing page
- current site-tree validation reports no broken local HTML targets

## Public Site Bundle Confirmed

The public-site bundle exists under:

- [build/site/index.html](/Users/hassan/repos/AI-Empire/build/site/index.html)

The bundle currently contains:

- academic standalone papers
- omnibus volume
- corpus companion
- literary/public edition

Current local validation confirms:

- `build/site/index.html` exists
- the literary branch is linked from the public index
- relative site links resolve locally
- the site-tree validator reports `0` missing local targets
- the site-tree validator reports `0` forbidden public artifacts
- `.nojekyll` is present

## Methodology and Continuity Confirmed

The project now includes a full newcomer-to-maintainer ladder:

- [start_here.md](/Users/hassan/repos/AI-Empire/docs/start_here.md)
- [project_map.md](/Users/hassan/repos/AI-Empire/docs/project_map.md)
- [research_workflow.md](/Users/hassan/repos/AI-Empire/docs/research_workflow.md)
- [contributor_manual.md](/Users/hassan/repos/AI-Empire/docs/contributor_manual.md)
- [maintainer_manual.md](/Users/hassan/repos/AI-Empire/docs/maintainer_manual.md)
- [editorial_and_citation_manual.md](/Users/hassan/repos/AI-Empire/docs/editorial_and_citation_manual.md)
- [resume_and_republish_runbook.md](/Users/hassan/repos/AI-Empire/docs/resume_and_republish_runbook.md)
- [researcher_guide.md](/Users/hassan/repos/AI-Empire/docs/researcher_guide.md)
- [github_pages_release.md](/Users/hassan/repos/AI-Empire/docs/github_pages_release.md)

These documents now explain:

- what is canonical versus generated
- how to resume from zero context
- how evidence flows through the system
- how to rebuild outputs
- how to republish the site
- how an outside researcher should use the package

## GitHub Pages Workflow Confirmed

The repository includes a Pages workflow at:

- [.github/workflows/pages.yml](/Users/hassan/repos/AI-Empire/.github/workflows/pages.yml)

The workflow currently:

- checks out the repo
- sets up Python
- installs `pillow` and `pypdf`
- installs `pandoc`
- installs `tectonic`
- runs the full publication build
- uploads `build/site/` as the Pages artifact
- deploys to GitHub Pages

This means the repository is locally prepared for clean Pages publication.

## What Is Fully Proven Locally

The following statements are currently proven inside the local repository:

1. The publication architecture exists in the intended four-layer shape: papers, volumes, book, and site bundle.
2. The corpus totals are visible and documented.
3. Standalone papers export to HTML, TeX, and PDF.
4. The omnibus and corpus companion export to HTML, TeX, and PDF.
5. The literary/public edition exports to HTML and PDF.
6. The public site bundle is assembled at `build/site/`.
7. Publication QA currently passes.
8. The methodology and maintenance documentation is strong enough for a fresh researcher to resume work without chat-history dependence.
9. The GitHub Pages workflow exists and targets the correct artifact root.

## What Is Not Fully Proven Locally

The following statement is not fully proven by local repository inspection alone:

- that GitHub has already executed the workflow successfully and is serving the resulting site live from Pages

That final state depends on:

- repository Pages settings
- workflow permissions in GitHub
- a successful remote Actions run
- post-deploy live-site verification

## Required Final External Check

To move from `locally publication-ready` to `externally published`, a maintainer must confirm:

1. GitHub Pages is enabled for the repository
2. the Pages source is set to `GitHub Actions`
3. the `Publish Pages` workflow completes successfully
4. the live Pages URL loads the public home page
5. the live Pages URL opens the literary landing page
6. at least one paper PDF, one omnibus PDF, and one companion PDF load correctly from the live site

Use:

- [github_pages_release.md](/Users/hassan/repos/AI-Empire/docs/github_pages_release.md)

## Recommended Release Status Language

Until the live GitHub Pages run is confirmed, the safest description is:

`The repository is locally publication-ready, export-validated, and GitHub-Pages-configured, with final live deployment confirmation still dependent on one successful external Pages run.`
