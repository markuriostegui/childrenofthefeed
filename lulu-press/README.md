# Lulu Press Interiors

This directory contains the two Lulu Global Distribution interior PDFs only.
Exterior wrap covers, bleed, spine, and barcode placement are intentionally
outside this workflow.

- `en/978-0-557-94877-2-interior.pdf` — English, ISBN `978-0-557-94877-2`
- `es/978-0-557-94875-8-interior.pdf` — Spanish, ISBN `978-0-557-94875-8`

Each rendition is 6 x 9 in and includes full-trim visual title art,
copyright/ISBN, dedication, generated contents, and white-paper manuscript
pages. The full-trim title page is not an exterior-cover bleed file.

## Build and review

The normal English and Spanish print-export commands also refresh their Lulu
renditions. To build one from an existing print PDF:

```text
python -m apps.research_cli.research_cli.cli export-lulu-interior --root . --edition en
python -m apps.research_cli.research_cli.cli export-lulu-interior --root . --edition es
python -m apps.research_cli.research_cli.cli review-lulu-interiors --root .
```

The per-edition `manifest.json` and `preflight.json` record exact source and
output hashes, ISBN/imprint data, title-art provenance, white-source details,
dimensions, and PDF validation results.
