# GitHub Pages Release Runbook

This runbook covers the final public-site publication step for the project. It is the last-mile guide for taking the already-built package and shipping it through GitHub Pages.

## Publication Target

The workflow publishes:

- `build/site/`

That artifact contains:

- the standalone academic papers
- the omnibus dossier
- the corpus companion
- the literary/public edition under `book/`
- the story reader SPA under `website/`

The deployment workflow is:

- [.github/workflows/pages.yml](/Users/hassan/repos/AI-Empire/.github/workflows/pages.yml)

## Preconditions

Before treating a push as release-ready, confirm:

1. `build-index` completed if evidence changed.
2. `export-papers` completed successfully.
3. `export-book` completed successfully for the literary HTML/web layer.
4. `export-book-print` completed successfully for the 6x9 trade-book PDFs.
5. `review-book-print` completed successfully.
6. `build-site` completed successfully.
7. `review-publication` completed successfully.
8. [build/site/index.html](/Users/hassan/repos/AI-Empire/build/site/index.html) opens locally and shows the literary card.
9. [build/site/website/index.html](/Users/hassan/repos/AI-Empire/build/site/website/index.html) opens locally and loads the reader shell.
10. [build/book/index.html](/Users/hassan/repos/AI-Empire/build/book/index.html) opens locally and shows the full-book links and 11 chapter cards.
11. [build/reviews/publication_qc.md](/Users/hassan/repos/AI-Empire/build/reviews/publication_qc.md) shows `Site tree status: pass`, `Website bundle status: pass`, and `Forbidden public artifacts: 0`.

If the release includes literary-branch changes, also confirm before publish:

11. `book/assets/asset_manifest.json` is in sync with newly generated visuals.
12. the relevant prompt documents under `book/assets/prompts/` were updated before generation and are committed.
13. if infographic visuals changed, `generate-book-assets --kind infographics` was rerun so the request bundle matches the current manifest and prompt refs.
14. the rebuilt chapter pages under `build/site/book/html/` still render the expected visual density.
15. the QR-note targets still resolve under `https://hassanvfx.github.io/ai-empire/`.
16. the full-book print PDF still opens with cover, title/imprint page, dedication page, and TOC in that order.
17. the full-book print PDF still lands inside the `96–104` page acceptance band.
18. the chapter PDFs still open with chapter opener, chapter imprint page, dedication page, and local TOC in that order.
19. the literary HTML landing page, full-book page, and chapter pages still end with the ceremonial dedication/imprint block.

## Local Release Sequence

Run, in order:

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

`build-site` is the single public-artifact assembly point. It rebuilds `build/site/` from scratch and republishes the story reader at `build/site/website/` as part of the same step. The published reader reuses shared `book/assets/generated/` imagery inside the Pages artifact to reduce deployment size; the local standalone `website/` bundle remains self-contained.

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli review-publication --root /Users/hassan/repos/AI-Empire
```

If the local Python environment is missing `pypdf`, use the bundled Codex runtime for the QA step:

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
/Users/hassan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
-m research_cli.cli review-publication --root /Users/hassan/repos/AI-Empire
```

## Repository Settings Requirements

For the GitHub Pages workflow to publish successfully, confirm in repository settings:

1. `Pages` is enabled.
2. The source is set to `GitHub Actions`.
3. The workflow has permission to publish Pages artifacts.

The workflow already installs:

- `pypdf`
- `pillow`
- `reportlab`
- `pandoc`
- `tectonic`
- `typst`

`typst` is now installed in CI through a pinned prebuilt release download rather than `taiki-e/install-action`, because the generic install-action path stopped inferring the correct binary on GitHub's Linux runner.

The publication split is now explicit:

- `export-book` builds the literary HTML/web layer
- `export-book-print` builds the trade-book 6x9 PDFs through Typst
- the academic paper and volume PDFs keep their own export path

The literary print layer should be treated as a designed book object rather than an HTML printout. Release-ready output preserves:

- the fixed 4-page full-book front matter
- the mirrored 4-page chapter-PDF openings
- chapter-end QR research notes
- the dedication/imprint block in the HTML literary layer
- the near-100-page full-book target, with `96–104` as the working acceptance range

If local HTML preview is part of the pass, a fresh local machine should also have:

- `playwright`
- Chromium installed with `playwright install chromium`

GitHub Actions uses Typst for the literary print PDFs and the academic toolchain for the scholarly layers.

The workflow also installs the native Ubuntu packages required by the current `tectonic` install path:

- `pkg-config`
- `libpng-dev`
- `libgraphite2-dev`
- `libharfbuzz-dev`
- `libfontconfig1-dev`
- `libfreetype6-dev`

For the multilingual dedication page in the literary print PDFs, the Typst template is now aligned to CI-safe Noto family names:

- `Noto Sans Hebrew`
- `Noto Sans Devanagari`
- `Noto Naskh Arabic`
- `Noto Sans CJK SC`
- `Noto Sans CJK JP`
- `Noto Sans CJK KR`

This keeps the current publication architecture intact:

- `docs/` remains the internal manuals layer
- `build/site/` remains the public Pages artifact root
- `Settings -> Pages -> Source` should remain `GitHub Actions`

## Live-Site Smoke Checks

After the workflow completes successfully, verify:

1. the public home page loads
2. the literary card opens `book/index.html`
3. the literary landing page shows the full-book HTML link
4. the literary landing page shows the full-book PDF link
5. at least one literary chapter page loads
6. at least one chapter paper PDF downloads correctly
7. the omnibus PDF loads
8. the corpus companion PDF loads
9. at least one literary chapter shows the expected cover + scene + infographic layout
10. the full-book PDF shows the cover, title/imprint, dedication, and TOC in that order
11. one chapter PDF shows its opener, chapter imprint page, dedication page, and local TOC in that order

Recommended pages to test:

- site home page
- `book/index.html`
- `book/html/full_book.html`
- `papers/html/10_three-reform-program_paper.html`
- `volumes/html/dossier_omnibus.html`
- `volumes/html/corpus_companion.html`

## If the Workflow Fails

Use this order:

1. confirm whether the failure is in build or in repository Pages settings
2. inspect the `Build publication package` step first
3. if the failure happens during `Install Tectonic`, inspect whether the action still fell back to a source build and whether the native package install step completed successfully
4. if the failure happens during `Install Typst`, inspect the binary install step and runner PATH
   - confirm the pinned release URL still exists
   - confirm the extracted binary is moved into `/usr/local/bin/typst`
   - confirm `typst --version` succeeds inside the workflow
5. if the failure happens during `export-book-print` before Typst compile begins, inspect Python dependency installation first
   - `book_print.py` currently requires `Pillow`, `pypdf`, and `reportlab`
6. if the failure is font-warning-heavy during the literary print step, inspect the dedication-font family names in `apps/templates/book_print_template.typ` against the Ubuntu Noto packages installed in the workflow
7. if the failure is literary-PDF-related, inspect `book/print/metadata.json`, the vendored fonts, and QR/image asset paths
8. if the failure is academic-PDF-related after Tectonic is installed, inspect `tectonic` output and asset paths
9. if repeated GitHub-runner failures remain isolated to PDF generation, keep the Pages workflow and move temporarily to an `HTML + assets` live-site release while generating PDFs locally for release artifacts
10. if the failure is QA-related, inspect [build/reviews/publication_qc.md](/Users/hassan/repos/AI-Empire/build/reviews/publication_qc.md) locally
11. if the failure is site-shape-related, inspect [build/site/index.html](/Users/hassan/repos/AI-Empire/build/site/index.html) locally before the next push
12. if the failure mentions forbidden artifacts, rebuild the site bundle and confirm that cache, processed, preview, config, Tectonic-home, and `.DS_Store` files are not leaking into `build/site/`

## Fallback Policy

If GitHub-hosted CI remains unstable specifically on the PDF toolchain after the native dependency fix, the preferred simplification is:

1. keep GitHub Pages on `GitHub Actions`
2. keep `build/site/` as the public artifact
3. publish the HTML site and assets through Actions
4. generate PDFs locally as release artifacts until CI PDF generation is made reproducible again

Do not collapse the public site into `/docs` as a workaround. In this project, `/docs` is the maintainer-facing continuity and methodology layer, not the public Pages root.

If the runner keeps surfacing new missing native libraries after this broader dependency set, stop extending the apt package list and replace the current installer with a pinned binary-first Tectonic install path.

## Release Note Habit

After each public release, leave a short note recording:

- what changed materially
- whether corpus totals changed
- whether literary content changed
- whether visuals changed
- whether the Pages deployment completed successfully
