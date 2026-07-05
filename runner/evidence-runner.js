#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

function printHelp() {
  console.log(`Usage:
  node evidence-runner.js init-session --out <dir> --app-url <url> [--persona <label>] [--viewport 390x844]
  node evidence-runner.js capture --url <url> --out <dir> [--viewport 390x844] [--label mobile] [--wait 1000]

Commands:
  init-session  Create a session manifest skeleton without launching a browser.
  capture       Open a URL with Playwright Chromium and capture evidence.

Notes:
  Playwright is optional. Run "npm install" and "npx playwright install chromium" inside runner/ before capture.
`);
}

function parseArgs(argv) {
  const result = { _: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item.startsWith("--")) {
      const key = item.slice(2);
      const next = argv[index + 1];
      if (!next || next.startsWith("--")) {
        result[key] = true;
      } else {
        result[key] = next;
        index += 1;
      }
    } else {
      result._.push(item);
    }
  }
  return result;
}

function parseViewport(value) {
  const fallback = { width: 1440, height: 900 };
  if (!value) return fallback;
  const match = String(value).match(/^(\d+)x(\d+)$/);
  if (!match) {
    throw new Error(`Invalid viewport "${value}". Use WIDTHxHEIGHT, for example 390x844.`);
  }
  return { width: Number(match[1]), height: Number(match[2]) };
}

function ensureOutDir(rawOut) {
  if (!rawOut) throw new Error("--out is required");
  const outDir = path.resolve(rawOut);
  fs.mkdirSync(outDir, { recursive: true });
  return outDir;
}

function writeJson(file, data) {
  fs.writeFileSync(file, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

function initSession(args) {
  const outDir = ensureOutDir(args.out);
  if (!args["app-url"]) throw new Error("--app-url is required for init-session");
  const manifest = {
    schema_version: "1.0",
    command: "init-session",
    app_url: args["app-url"],
    persona: args.persona || null,
    viewport: parseViewport(args.viewport),
    created_at: new Date().toISOString(),
    notes: []
  };
  const manifestPath = path.join(outDir, "session.json");
  writeJson(manifestPath, manifest);
  console.log(JSON.stringify({ ok: true, session: manifestPath }, null, 2));
}

async function capture(args) {
  const url = args.url;
  if (!url) throw new Error("--url is required for capture");
  const outDir = ensureOutDir(args.out);
  const viewport = parseViewport(args.viewport);
  const label = args.label || `${viewport.width}x${viewport.height}`;
  const waitMs = Number(args.wait || 1000);
  const timestamp = new Date().toISOString();

  let chromium;
  try {
    ({ chromium } = require("playwright"));
  } catch (error) {
    throw new Error("Playwright is not installed. Run `npm install` inside runner/ first.");
  }

  const consoleMessages = [];
  const networkErrors = [];
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport });
  page.on("console", (message) => {
    consoleMessages.push({
      type: message.type(),
      text: message.text()
    });
  });
  page.on("requestfailed", (request) => {
    networkErrors.push({
      url: request.url(),
      method: request.method(),
      failure: request.failure() ? request.failure().errorText : "unknown"
    });
  });
  page.on("response", (response) => {
    if (response.status() >= 400) {
      networkErrors.push({
        url: response.url(),
        method: response.request().method(),
        status: response.status()
      });
    }
  });

  const startedAt = Date.now();
  await page.goto(url, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(Number.isFinite(waitMs) ? waitMs : 1000);
  const screenshotPath = path.join(outDir, `${label}-screenshot.png`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const timings = await page.evaluate(() => {
    const nav = performance.getEntriesByType("navigation")[0];
    const paint = performance.getEntriesByType("paint");
    return {
      navigation: nav ? nav.toJSON() : null,
      paint: paint.map((entry) => entry.toJSON())
    };
  });
  await browser.close();

  const manifest = {
    schema_version: "1.0",
    command: "capture",
    url,
    label,
    viewport,
    captured_at: timestamp,
    elapsed_ms: Date.now() - startedAt,
    screenshot_path: screenshotPath,
    console_messages: consoleMessages,
    network_errors: networkErrors,
    timings
  };
  const manifestPath = path.join(outDir, "manifest.json");
  writeJson(manifestPath, manifest);
  writeJson(path.join(outDir, "console.json"), consoleMessages);
  writeJson(path.join(outDir, "network.json"), networkErrors);
  console.log(JSON.stringify({ ok: true, manifest: manifestPath, screenshot: screenshotPath }, null, 2));
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || args.h || args._.length === 0) {
    printHelp();
    return;
  }
  const command = args._[0];
  if (command === "init-session") {
    initSession(args);
    return;
  }
  if (command === "capture") {
    await capture(args);
    return;
  }
  throw new Error(`Unknown command "${command}". Run --help.`);
}

main().catch((error) => {
  console.error(JSON.stringify({ ok: false, error: error.message }, null, 2));
  process.exit(1);
});

