import fs from "node:fs/promises";
import path from "node:path";

const PLUGIN_ROOT = "file:///Users/hassan/.codex/plugins/cache/openai-bundled/browser/26.623.81905/scripts/browser-client.mjs";

async function ensureBrowser() {
  if (globalThis.agent?.browsers == null) {
    const { setupBrowserRuntime } = await import(PLUGIN_ROOT);
    await setupBrowserRuntime({ globals: globalThis });
  }
  const browser = await globalThis.agent.browsers.get("iab");
  return browser;
}

export async function capturePage({ sourceId, url, outputDir, captureScreenshot = false }) {
  const browser = await ensureBrowser();
  const tab = await browser.tabs.new();
  await tab.goto(url);
  try {
    await tab.playwright.waitForLoadState({ state: "networkidle", timeoutMs: 30000 });
  } catch {}
  const title = await tab.title();
  const currentUrl = await tab.url();
  const dom = await tab.playwright.domSnapshot();
  await fs.mkdir(outputDir, { recursive: true });
  const base = path.join(outputDir, sourceId);
  await fs.writeFile(base + ".dom.txt", dom, "utf8");
  let screenshotPath = null;
  if (captureScreenshot) {
    const screenshot = await tab.screenshot({ fullPage: true });
    screenshotPath = base + ".png";
    await fs.writeFile(screenshotPath, Buffer.from(screenshot));
  }
  const manifest = {
    source_id: sourceId,
    url: currentUrl,
    requested_url: url,
    title,
    captured_at: new Date().toISOString(),
    output_dir: outputDir,
    screenshot_path: screenshotPath,
    dom_path: base + ".dom.txt"
  };
  await fs.writeFile(base + ".capture.json", JSON.stringify(manifest, null, 2));
  return manifest;
}

export async function capturePageFromJob(jobPath) {
  const job = JSON.parse(await fs.readFile(jobPath, "utf8"));
  return capturePage({
    sourceId: job.source_id,
    url: job.url,
    outputDir: job.output_dir,
    captureScreenshot: Boolean(job.capture_screenshot)
  });
}
