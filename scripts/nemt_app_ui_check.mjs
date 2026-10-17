#!/usr/bin/env node
/**
 * Local-only mobile UI smoke check for NEMT Trade (/trade).
 *
 * Requires:
 * - the API on http://127.0.0.1:8000 (DEMO)
 * - Next.js production server on http://127.0.0.1:3000
 * - Google Chrome installed (override with CHROME_PATH)
 *
 * This script logs into DEMO accounts via the demo endpoint, captures
 * screenshots and verifies basic PWA/security invariants. It must never be
 * pointed at TESTNET/LIVE or a real-money deployment.
 */
import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const CHROME =
  process.env.CHROME_PATH ||
  "C:/Program Files/Google/Chrome/Application/chrome.exe";
const BASE_URL = process.env.NEMT_BASE_URL || "http://127.0.0.1:3000";
const DEBUG_PORT = Number(process.env.NEMT_CHROME_PORT || 9223);
const OUT_DIR = path.resolve("docs/assets/nemt-app");
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

if (process.env.NEMT_APP_MODE && process.env.NEMT_APP_MODE !== "DEMO") {
  console.error("Refusing to run: UI check is DEMO-only.");
  process.exit(1);
}

await fs.mkdir(OUT_DIR, { recursive: true });
const profile = await fs.mkdtemp(path.join(os.tmpdir(), "nemt-ui-"));
const chrome = spawn(
  CHROME,
  [
    "--headless=new",
    `--remote-debugging-port=${DEBUG_PORT}`,
    `--user-data-dir=${profile}`,
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-gpu",
    "--hide-scrollbars",
    "--disable-extensions",
    "--window-size=390,844",
    "about:blank",
  ],
  { stdio: "ignore" }
);

class Cdp {
  constructor(ws) {
    this.ws = ws;
    this.nextId = 1;
    this.pending = new Map();
    this.events = [];
    ws.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) reject(new Error(JSON.stringify(message.error)));
        else resolve(message.result);
      } else if (message.method) {
        this.events.push(message);
      }
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
}

async function waitForEndpoint() {
  for (let attempt = 0; attempt < 60; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${DEBUG_PORT}/json/version`);
      if (response.ok) return;
    } catch {
      /* not ready */
    }
    await sleep(200);
  }
  throw new Error("Chrome DevTools endpoint did not start");
}

async function main() {
  await waitForEndpoint();
  const response = await fetch(
    `http://127.0.0.1:${DEBUG_PORT}/json/new?${encodeURIComponent(`${BASE_URL}/trade`)}`,
    { method: "PUT" }
  );
  const target = await response.json();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", reject, { once: true });
  });
  const cdp = new Cdp(ws);
  const failures = [];
  const notes = [];

  async function evaluate(expression) {
    const result = await cdp.send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
      userGesture: true,
    });
    if (result.exceptionDetails) {
      throw new Error(
        result.exceptionDetails.exception?.description ||
          result.exceptionDetails.text ||
          "Runtime.evaluate failed"
      );
    }
    return result.result.value;
  }

  async function shot(name) {
    const { data } = await cdp.send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
    });
    const file = path.join(OUT_DIR, name);
    await fs.writeFile(file, Buffer.from(data, "base64"));
    console.log("screenshot", path.relative(process.cwd(), file));
  }

  async function reload(waitMs = 3000) {
    await cdp.send("Page.reload", { ignoreCache: false });
    await sleep(waitMs);
  }

  async function clickButton(label) {
    const clicked = await evaluate(`(() => {
      const target = [...document.querySelectorAll("button")]
        .find((button) => button.textContent && button.textContent.trim() === ${JSON.stringify(label)});
      if (!target) return false;
      target.click();
      return true;
    })()`);
    if (!clicked) throw new Error(`Button not found: ${label}`);
    await sleep(900);
  }

  async function loginDemo(account) {
    const status = await evaluate(
      `fetch("/api/v1/auth/demo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ account: ${JSON.stringify(account)} })
      }).then(async (response) => ({ status: response.status, body: await response.text() }))`
    );
    if (status.status !== 200) {
      throw new Error(`Demo login failed (${status.status}): ${status.body.slice(0, 200)}`);
    }
    await reload(3200);
  }

  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Network.enable");
  await cdp.send("Log.enable");
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: 390,
    height: 844,
    deviceScaleFactor: 2,
    mobile: true,
    screenWidth: 390,
    screenHeight: 844,
  });
  await reload(4000);

  const loginText = await evaluate("document.body.innerText");
  if (!loginText.includes("NEMT TRADE")) {
    failures.push("Login screen did not render");
  }
  await shot("login.png");

  await loginDemo("demo");
  const overviewText = await evaluate("document.body.innerText");
  if (!overviewText.includes("DEMO 演示环境")) {
    failures.push("DEMO overview did not render");
  }
  if (!overviewText.includes("BTC/USDT")) {
    failures.push("Market symbol missing from overview");
  }
  await shot("overview.png");

  await clickButton("行情");
  await sleep(1800);
  const marketText = await evaluate("document.body.innerText");
  const hasChart = await evaluate(
    `Boolean(document.querySelector('svg[aria-label="BTCUSDT K 线图"]'))`
  );
  if (!hasChart) failures.push("Candlestick chart not rendered");
  if (marketText.includes("undefined")) failures.push("Market tab contains undefined text");
  await shot("market.png");

  await clickButton("交易");
  const tradeText = await evaluate("document.body.innerText");
  if (!tradeText.includes("预览订单")) failures.push("Trade form did not render");
  await shot("trade.png");

  await clickButton("订单");
  await clickButton("全部 (1)").catch(() => notes.push("No order history to select"));
  await sleep(600);
  await shot("orders.png");

  await clickButton("设置");
  await shot("settings-trader.png");

  await loginDemo("admin");
  await clickButton("设置");
  const adminText = await evaluate("document.body.innerText");
  if (!adminText.includes("管理员控制")) failures.push("Admin controls not visible for admin");
  await shot("settings-admin.png");
  await evaluate(`(() => {
    const heading = [...document.querySelectorAll("h2")]
      .find((element) => element.textContent && element.textContent.includes("管理员控制"));
    if (heading) heading.scrollIntoView({ block: "center" });
    return Boolean(heading);
  })()`);
  await sleep(700);
  await shot("settings-admin-controls.png");

  const pwa = await evaluate(`(async () => {
    const registrations = await navigator.serviceWorker.getRegistrations();
    return {
      manifest: document.querySelector('link[rel="manifest"]')?.getAttribute("href") || null,
      sw: registrations.map((item) => ({ scope: item.scope, active: Boolean(item.active) })),
      controller: Boolean(navigator.serviceWorker.controller),
      overflow: document.documentElement.scrollWidth - window.innerWidth,
      storageKeys: Object.keys(localStorage),
    };
  })()`);
  notes.push(`PWA ${JSON.stringify(pwa)}`);
  if (!pwa.manifest) failures.push("Manifest link missing");
  if (!pwa.sw.length || !pwa.sw.some((item) => item.active)) {
    notes.push("Service worker is not active yet");
  }
  if (pwa.overflow > 1) failures.push(`Horizontal overflow: ${pwa.overflow}px`);
  if (pwa.storageKeys.some((key) => /binance|secret|key/i.test(key))) {
    failures.push("Suspicious exchange key in localStorage");
  }

  // Offline: the app must not pretend an order succeeded.
  await cdp.send("Network.emulateNetworkConditions", {
    offline: true,
    latency: 0,
    downloadThroughput: 0,
    uploadThroughput: 0,
  });
  try {
    await cdp.send("Page.reload", { ignoreCache: false });
    await sleep(2500);
    const offlineText = await evaluate("document.body.innerText");
    await shot("offline.png");
    notes.push(`Offline body: ${offlineText.slice(0, 120).replace(/\n/g, " | ")}`);
    if (!/离线|网络|无法连接|重新连接/.test(offlineText)) {
      notes.push("Offline state did not expose a clear disconnected message");
    }
  } catch (error) {
    notes.push(`Offline check could not inspect DOM: ${error.message}`);
    await shot("offline.png").catch(() => {});
  }
  await cdp.send("Network.emulateNetworkConditions", {
    offline: false,
    latency: 0,
    downloadThroughput: -1,
    uploadThroughput: -1,
  });
  await reload(2500);
  await loginDemo("demo");

  // Desktop viewport sanity check.
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: 1280,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false,
    screenWidth: 1280,
    screenHeight: 900,
  });
  await cdp.send("Page.navigate", { url: `${BASE_URL}/trade` });
  await sleep(2800);
  await shot("desktop-overview.png");
  const desktopOverflow = await evaluate(
    "document.documentElement.scrollWidth - window.innerWidth"
  );
  if (desktopOverflow > 1) failures.push(`Desktop horizontal overflow: ${desktopOverflow}px`);

  const errors = cdp.events
    .filter(
      (event) =>
        (event.method === "Runtime.exceptionThrown") ||
        (event.method === "Log.entryAdded" && event.params.entry.level === "error")
    )
    .map((event) =>
      event.method === "Runtime.exceptionThrown"
        ? event.params.exceptionDetails.text
        : event.params.entry.text
    )
    .filter((text) => !/favicon|ERR_INTERNET_DISCONNECTED|Failed to fetch/.test(text));
  if (errors.length) notes.push(`Console errors: ${JSON.stringify(errors.slice(0, 5))}`);

  console.log("NOTES", JSON.stringify(notes, null, 2));
  if (failures.length) {
    console.error("FAILURES", JSON.stringify(failures, null, 2));
    process.exitCode = 1;
  } else {
    console.log("UI CHECK PASSED");
  }

  ws.close();
  chrome.kill();
  await fs.rm(profile, { recursive: true, force: true }).catch(() => {});
}

main().catch(async (error) => {
  console.error("UI CHECK ERROR", error);
  chrome.kill();
  await fs.rm(profile, { recursive: true, force: true }).catch(() => {});
  process.exit(1);
});
