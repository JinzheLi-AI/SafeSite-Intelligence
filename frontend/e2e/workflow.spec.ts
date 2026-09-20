import { test, expect } from "@playwright/test";
import path from "node:path";
test("human-controlled inspection-to-closure persists across refreshes", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Safety, in clear view." })).toBeVisible();
  await expect(page.getByText("Resolved Incidents", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/dashboard.png", fullPage: true });
  await page.getByRole("link", { name: "New AI inspection", exact: true }).click();
  await expect(page.getByRole("button", { name: "Analyze Site", exact: true })).toBeEnabled();
  await page.screenshot({ path: "test-results/inspection.png", fullPage: true });
  await page.locator('input[type="file"]').setInputFiles(path.resolve("../evaluation/fixtures/vision_v2/development/fbfd230b416044a7919c81f26bf501e8867a90ff9b24be50a4bf0f6cfa54ebdf.jpg"));
  await page.getByRole("button", { name: "Analyze Site", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Human Review Required" })).toBeVisible();
  await expect(page.getByText("Demo regulation data").first()).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Human Review Required" })).toBeVisible();
  await page.screenshot({ path: "test-results/findings.png", fullPage: true });
  await page.getByRole("button", { name: "Confirm Findings", exact: true }).click();
  await page.getByRole("link", { name: "Open primary incident" }).click();
  await expect(page.getByRole("heading", { name: "Working at Height", exact: true }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Close Case" })).toHaveCount(0);
  await page.getByRole("button", { name: "Start Rectification" }).click();
  const actions = page.locator(".corrective-item input");
  for (let index = 0; index < await actions.count(); index++) {
    await expect(actions.nth(index)).toBeEnabled();
    await actions.nth(index).check();
  }
  await page.getByLabel("Use simulated rectification evidence for this demo").check();
  await page.getByRole("button", { name: "Run Reinspection", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Hazard Mitigated" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Close Case" })).toBeEnabled();
  await page.reload();
  await expect(page.getByRole("button", { name: "Close Case" })).toBeEnabled();
  await expect(page.getByText("Case closed by human decision.", { exact: true })).toHaveCount(0);
  await page.screenshot({ path: "test-results/reinspection.png", fullPage: true });
  await page.getByRole("button", { name: "Close Case" }).click();
  await expect(page.getByText("Case closed by human decision.", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText("Case closed by human decision.", { exact: true })).toBeVisible();
  await expect(page.locator(".audit-timeline").getByText("Case Closed By Human", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/closed-case.png", fullPage: true });
  expect(errors).toEqual([]);
});

test("knowledge demo previews and analyst metrics are functional", async ({ page }) => {
  await page.goto("/knowledge");
  await expect(page.locator('.document-card[data-demo="true"]')).toHaveCount(3);
  await page.getByLabel("Search documents").fill("Edge protection");
  await expect(page.locator(".document-card")).toHaveCount(1);
  await page.getByRole("button", { name: "View sample document" }).click();
  await expect(page.getByRole("region", { name: "Sample document preview" })).toBeVisible();
  await page.goto("/analyst");
  await page.getByRole("button", { name: "What is our incident closure rate?" }).click();
  await expect(page.getByRole("region", { name: "Safety analytics result" })).toBeVisible();
  await expect(page.getByText("Database query \u00b7 no LLM", { exact: true })).toBeVisible();
});

test("mobile navigation and laptop layout have no page overflow", async ({ page }) => {
  await page.setViewportSize({ width: 1366, height: 768 });
  for (const path of ["/", "/inspections", "/incidents", "/analyst", "/knowledge"]) {
    await page.goto(path);
    await expect(page.locator("h1")).toBeVisible();
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Safety, in clear view." })).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("navigation").getByRole("link", { name: "Knowledge Base" }).click();
  await expect(page.locator("h1")).toHaveText("Good decisions need grounded evidence.");
  await expect(page.locator('.document-card[data-demo="true"]')).toHaveCount(3);
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/mobile-knowledge.png", fullPage: true });
});


test("uploaded ambiguous scene can be rejected without creating incidents", async ({ page }) => {
  await page.goto("/inspections");
  await page.locator('input[type="file"]').setInputFiles(path.resolve("../evaluation/fixtures/live_smoke/03_ambiguous.jpg"));
  await page.getByRole("button", { name: "Analyze Site", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Human Review Required" })).toBeVisible();
  await expect(page.getByText("Demo regulation data").first()).toBeVisible();
  await page.getByLabel("Review notes / rejection reason").fill("Offline demo: fixed mock findings are unsupported for this photograph; request qualified review, no safety conclusion.");
  await page.getByRole("button", { name: "Reject Findings", exact: true }).click();
  await expect(page.getByText("Findings rejected by human review. No incidents were created.", { exact: false })).toBeVisible();
  await expect(page.getByRole("link", { name: "Open primary incident" })).toHaveCount(0);
  await page.reload();
  await expect(page.getByText("Findings rejected by human review. No incidents were created.", { exact: false })).toBeVisible();
});
