# Story Reader SPA

This directory is a generated static reader bundle for **Children of the Feed. Servants of the AI God**.

## Regenerate

```bash
PYTHONPATH=/Users/hassan/repos/AI-Empire/apps/research_cli \
python3 -m research_cli.cli build-website --root /Users/hassan/repos/AI-Empire
```

## Structure

- `index.html`: SPA shell
- `assets/css/app.css`: mobile-first cinematic styling
- `assets/js/app.js`: router, reader UI, and local storage state
- `assets/images/`: copied editorial imagery for self-contained runtime use
- `data/chapters.json`: generated chapter/block data contract

`build-site` publishes the same bundle at `build/site/website/`.
`build-website` remains available for targeted local reader rebuilds.
