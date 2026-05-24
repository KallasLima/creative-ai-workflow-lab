import { spawn, type ChildProcess } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { chromium } from "playwright-core";

const frontendUrl = "http://127.0.0.1:5173";
const backendUrl = process.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const chromeExecutable =
  process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ??
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(message);
  }
}

async function waitForHttp(url: string, timeoutMs: number) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Keep polling until Vite is ready.
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 200));
  }
  throw new Error(`Timed out waiting for ${url}`);
}

async function assertPortFree() {
  try {
    const response = await fetch(frontendUrl);
    if (response.ok) {
      throw new Error(`${frontendUrl} is already in use`);
    }
  } catch (error) {
    if (error instanceof Error && error.message.includes("already in use")) {
      throw error;
    }
  }
}

function startFrontend(): ChildProcess {
  const viteBin = resolve("node_modules/vite/bin/vite.js");
  assert(existsSync(viteBin), "Vite binary missing; run npm install before visual smoke");

  return spawn(
    process.execPath,
    [viteBin, "--host", "127.0.0.1", "--port", "5173"],
    {
      cwd: process.cwd(),
      env: {
        ...process.env,
        VITE_API_BASE_URL: backendUrl,
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
}

async function assertNoVisibleOverflow(page: import("playwright-core").Page, label: string) {
  const overflow = await page.evaluate(() => {
    const ignoredTags = new Set(["HTML", "BODY"]);
    return Array.from(document.querySelectorAll("body *"))
      .filter((element) => {
        if (ignoredTags.has(element.tagName)) return false;
        const rect = element.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return false;
        return element.scrollWidth > element.clientWidth + 2;
      })
      .map((element) => ({
        tag: element.tagName,
        className: String((element as HTMLElement).className),
        text: (element.textContent ?? "").replace(/\s+/g, " ").trim().slice(0, 80),
      }))
      .filter((item) => item.text.length > 0)
      .slice(0, 10);
  });
  assert(overflow.length === 0, `${label}: Visible text overflow detected: ${JSON.stringify(overflow)}`);
}

async function latestVisibleApplyId(page: import("playwright-core").Page) {
  const text = await page.locator("body").innerText();
  const matches = Array.from(text.matchAll(/(?:^|[^_])(apply_\d{3})/g));
  return matches.at(-1)?.[1];
}

async function waitForNewApplyId(page: import("playwright-core").Page, previousApplyId: string | undefined, label: string) {
  await page.waitForFunction((previous) => {
    const matches = Array.from(document.body.innerText.matchAll(/(?:^|[^_])(apply_\d{3})/g));
    const latest = matches.at(-1)?.[1];
    return Boolean(latest && latest !== previous);
  }, previousApplyId, { timeout: 5_000 });
  const latest = await latestVisibleApplyId(page);
  assert(latest && latest !== previousApplyId, `${label}: apply event should advance`);
  return latest;
}

async function runDemoPath(page: import("playwright-core").Page, label: string) {
  await page.goto(frontendUrl, { waitUntil: "networkidle" });
  const firstViewport = await page.locator("body").innerText();

  assert(firstViewport.includes("Start with Backend sign-in"), `${label}: first viewport should guide the reviewer before sign-in`);
  assert(firstViewport.includes("Awaiting image job"), `${label}: first viewport should show pending image proof`);
  assert(!firstViewport.includes("placeholderOnly: true"), `${label}: first viewport must not claim placeholder proof before image job`);
  await assertNoVisibleOverflow(page, `${label} pre-sign-in`);

  await page.getByRole("button", { name: "Backend sign-in" }).click();
  await page.getByText("Maya Chen").first().waitFor({ timeout: 5_000 });
  const signedInViewport = await page.locator("body").innerText();
  assert(signedInViewport.includes("Session token issued by backend (redacted)"), `${label}: session panel should confirm redacted backend token`);
  assert(!signedInViewport.includes("Authorization: Bearer"), `${label}: session panel must not expose bearer token material`);
  await page.getByText("profile_nova_v3").first().waitFor({ timeout: 5_000 });
  await page.getByText("2 text / 1 image-fill / 0 ignored").first().waitFor({ timeout: 5_000 });
  await assertNoVisibleOverflow(page, `${label} signed-in`);

  await page.getByRole("button", { name: "Generate copy" }).click();
  await page.getByText("usageEventId usage_copy_001").waitFor({ timeout: 5_000 });
  let latestApplyId = await latestVisibleApplyId(page);
  await page.locator(".variant-row").first().click();
  latestApplyId = await waitForNewApplyId(page, latestApplyId, `${label}: copy apply`);

  await page.getByRole("button", { name: "Localization" }).click();
  await page.getByRole("button", { name: "Localize" }).click();
  await page.getByText("usageEventId usage_loc_001").waitFor({ timeout: 5_000 });
  await page.getByText("ko-KR").first().waitFor({ timeout: 5_000 });
  await page.getByRole("button", { name: "Apply fr-FR" }).first().click();
  latestApplyId = await waitForNewApplyId(page, latestApplyId, `${label}: localization apply`);

  await page.getByRole("button", { name: "Image" }).click();
  await page.getByRole("button", { name: "Create image placeholder" }).click();
  await page.getByText("usageEventId usage_img_001").waitFor({ timeout: 8_000 });
  await page.getByText("placeholderOnly: true").first().waitFor({ timeout: 8_000 });
  await page.getByText("1024 x 1024").first().waitFor({ timeout: 8_000 });
  await page.getByRole("button", { name: "Apply image output" }).click();
  latestApplyId = await waitForNewApplyId(page, latestApplyId, `${label}: image apply`);

  await page.getByRole("button", { name: "Report" }).click();
  await page.getByText(new RegExp(`applyEventId ${latestApplyId}`)).waitFor({ timeout: 5_000 });
  await page.getByText(/auditEventId audit_apply_\d{3}/).waitFor({ timeout: 5_000 });
  const reportGrid = await page.locator(".report-grid").innerText();
  assert(reportGrid.includes("Cost") && reportGrid.includes("$"), `${label}: report should show cost evidence`);
  assert(reportGrid.includes("Operations"), `${label}: report should show operation evidence`);
  assert(reportGrid.includes("Applies"), `${label}: report should show apply-event evidence`);
  await assertNoVisibleOverflow(page, `${label} completed report`);
}

async function main() {
  assert(existsSync(chromeExecutable), `Chrome executable not found: ${chromeExecutable}`);
  await assertPortFree();

  const server = startFrontend();
  let serverLog = "";
  server.stdout?.on("data", (chunk) => {
    serverLog += String(chunk);
  });
  server.stderr?.on("data", (chunk) => {
    serverLog += String(chunk);
  });

  try {
    await waitForHttp(frontendUrl, 15_000);

    const browser = await chromium.launch({
      executablePath: chromeExecutable,
      headless: true,
      args: [
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-sync",
        "--no-default-browser-check",
        "--no-first-run",
      ],
    });
    try {
      for (const viewport of [
        { label: "desktop", width: 1440, height: 1000 },
        { label: "tablet", width: 820, height: 1100 },
        { label: "mobile", width: 390, height: 844 },
      ]) {
        const page = await browser.newPage({ viewport: { width: viewport.width, height: viewport.height } });
        try {
          await runDemoPath(page, viewport.label);
        } finally {
          await page.close();
        }
      }
    } finally {
      await browser.close();
    }
  } catch (error) {
    if (serverLog.trim()) {
      console.error(serverLog.trim());
    }
    throw error;
  } finally {
    server.kill("SIGTERM");
  }
}

main()
  .then(() => {
    console.log("frontend-visual-smoke: PASS");
  })
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
