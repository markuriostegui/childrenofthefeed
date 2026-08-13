# AI Empire Research OS

This repository is a research and publication system for the dossier program on surveillance capitalism, data capture, technical enclosure, and imperial control over AI.

The project is organized around three enforced reforms:

- `Refactor Section 230`
- `AI Weights as Patrimony of Humanity`
- `Limit Government Capture by AI Companies`

## Start Here

If you are new to the repo, begin with:

1. [docs/start_here.md](/Users/hassan/repos/AI-Empire/docs/start_here.md)
2. [docs/project_map.md](/Users/hassan/repos/AI-Empire/docs/project_map.md)
3. [docs/research_workflow.md](/Users/hassan/repos/AI-Empire/docs/research_workflow.md)

If you want the reader-facing publication package, open:

- [build/site/index.html](/Users/hassan/repos/AI-Empire/build/site/index.html)

If you want the academic-local package only, open:

- [build/publication/index.html](/Users/hassan/repos/AI-Empire/build/publication/index.html)

## Publication Package

The repo publishes five coordinated reader-facing outputs:

- standalone chapter papers under `papers/`
- an omnibus dossier volume under `volumes/dossier_omnibus.md`
- a corpus companion / audit volume under `volumes/corpus_companion.md`
- a literary/public edition under `book/` branded as **Children of the Feed. Servants of the AI God**
- a chapter-based story reader SPA published under `build/site/website/`

Generated HTML, TeX, and PDF outputs live under `build/`, including the GitHub Pages bundle under `build/site/`.

## Canonical Layers

- `vectors/`: topic-by-topic evidence buckets
- `sources/`: source catalog and captures
- `claims/`: master claim registry
- `profiles/`: entity registry
- `timelines/`: master event registry
- `chapters/`: canonical narrative corpus and chapter synthesis layer
- `papers/`: canonical standalone paper layer
- `volumes/`: canonical shared-volume source layer
- `book/`: canonical literary/public edition source layer
- `docs/`: methodology, editorial, maintenance, and risk manuals
- `apps/research_cli/`: rebuild and publication tooling

## Workflow Principle

Evidence always moves downstream in this order:

`source -> note -> claim -> entity/timeline -> vector synthesis -> chapter corpus -> papers/volumes -> export/QA`

Do not use polished prose as a substitute for missing corpus work.

## Core Commands

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
python3 -m research_cli.cli build-site --root /Users/hassan/repos/AI-Empire
```

`build-site` is the single public-artifact publication command once the canonical repo content is ready. It reseeds papers, rebuilds paper and volume exports, rebuilds literary HTML, rebuilds the literary print PDFs, and then republishes the Pages bundle plus the story reader at `build/site/website/`.

For targeted local SPA iteration, you can still run:

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli build-website --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli review-publication --root /Users/hassan/repos/AI-Empire
```

If the local Python environment is missing `pypdf`, run the QA command with the bundled Codex runtime instead:

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
/Users/hassan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
-m research_cli.cli review-publication --root /Users/hassan/repos/AI-Empire
```

## Documentation Ladder

- [docs/start_here.md](/Users/hassan/repos/AI-Empire/docs/start_here.md): first-stop orientation
- [docs/project_map.md](/Users/hassan/repos/AI-Empire/docs/project_map.md): canonical vs generated layers
- [docs/research_workflow.md](/Users/hassan/repos/AI-Empire/docs/research_workflow.md): end-to-end flow
- [docs/contributor_manual.md](/Users/hassan/repos/AI-Empire/docs/contributor_manual.md): one bounded contribution
- [docs/maintainer_manual.md](/Users/hassan/repos/AI-Empire/docs/maintainer_manual.md): stewardship, rebuilds, and republication
- [docs/resume_and_republish_runbook.md](/Users/hassan/repos/AI-Empire/docs/resume_and_republish_runbook.md): continue from a fresh conversation or long pause
- [docs/github_pages_release.md](/Users/hassan/repos/AI-Empire/docs/github_pages_release.md): final Pages publication and live-site checks
- [docs/editorial_and_citation_manual.md](/Users/hassan/repos/AI-Empire/docs/editorial_and_citation_manual.md): public writing and citation rules
- [docs/researcher_guide.md](/Users/hassan/repos/AI-Empire/docs/researcher_guide.md): how outside researchers should use the package
- [docs/publication_completion_audit.md](/Users/hassan/repos/AI-Empire/docs/publication_completion_audit.md): what is already proven locally versus what still requires a live Pages run
