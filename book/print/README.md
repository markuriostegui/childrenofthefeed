# Print Layer

This directory contains the dedicated source layer for the 6x9 trade-book PDF pipeline.

## Purpose

This layer exists so the public literary PDFs are composed as print artifacts, not as browser-print exports of the HTML edition.

It is responsible for:

- chapter-end QR research notes
- print-sized image derivatives
- vendored fonts for deterministic composition
- Typst wrappers for the full book and standalone chapter PDFs

## Key Files

- `publication_config.json`: canonical public base URL and print-format configuration
- `metadata.json`: generated print-build manifest
- `qr_manifest.json`: generated QR target registry
- `manuscripts/`: derived print markdown and Pandoc-to-Typst intermediates
- `assets/qrcodes/`: scannable chapter-end QR assets
- `assets/images/`: print-sized image derivatives
- `typst/`: final wrapper sources compiled by Typst

## Commands

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli build-book-print --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli export-book-print --root /Users/hassan/repos/AI-Empire
```

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli review-book-print --root /Users/hassan/repos/AI-Empire
```
