import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
const output = fileURLToPath(new URL("../../docs/screenshots/", import.meta.url));
await mkdir(output, { recursive: true });
const api = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";
const base = process.env.E2E_BASE_URL ?? "http://127.0.0.1:3000";
const browser = await chromium.launch({ channel: process.env.E2E_BROWSER_CHANNEL ?? "msedge", headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const inspections = await (await fetch(api + "/inspections")).json();
  const cases = await (await fetch(api + "/incidents")).json();
  const prepared = inspections.find((item) => item.analysis_json && item.status === "ANALYZED");
  const closed = cases.find((item) => item.status === "CLOSED" && item.reinspection_json);
  for (const [name, path, ready] of [
    ["dashboard", "/", ".metric-value"],
    ["inspection", "/inspections", ".inspection-form-panel"],
    ...(prepared ? [["findings", "/inspections?id=" + prepared.id, ".hazard-card"]] : []),
    ...(closed ? [["closed-case", "/incidents/" + closed.id, ".audit-timeline"]] : []),
  ]) {
    await page.goto(base + path);
    await page.locator(ready).first().waitFor();
    await page.screenshot({ path: output + name + ".png", fullPage: true });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(base + "/knowledge");
  await page.locator(".document-card").first().waitFor();
  await page.screenshot({ path: output + "mobile-knowledge.png", fullPage: true });
  console.log("Demo screenshots saved to " + output);
} finally { await browser.close(); }
