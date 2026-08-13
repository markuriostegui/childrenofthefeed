# Browser Worker

This worker is intended for use from the Codex in-app browser when a page depends on JavaScript.

## Flow

1. Create a job:

```bash
python3 -m apps.research_cli.research_cli.cli capture-browser --root /Users/hassan/repos/AI-Empire --source-id example --vector-id 01_surveillance_capitalism --url https://example.com --capture-screenshot
```

2. Run the worker from the browser runtime:

```js
const { capturePageFromJob } = await import("file:///Users/hassan/repos/AI-Empire/apps/browser_worker/capture_page.mjs");
await capturePageFromJob("/Users/hassan/repos/AI-Empire/sources/browser_jobs/example.json");
```
