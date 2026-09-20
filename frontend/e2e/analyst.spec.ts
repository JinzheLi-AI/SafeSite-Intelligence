import { test, expect } from "@playwright/test";
const api = process.env.E2E_API_URL ?? "http://127.0.0.1:8000/api/v1";

test("analyst suggestions return real metric, chart and table results", async ({ page, request }) => {
  const expected = await (await request.post(api + "/analyst/query", { data: { question: "What is our incident closure rate?" } })).json();
  await page.goto("/analyst");
  // Streaming can briefly contain a hidden server copy; require one settled form.
  await expect(page.getByLabel("Ask about safety data")).toHaveCount(1);
  await expect(page.getByRole("heading", { name: "AI Safety Analyst", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "What is our incident closure rate?", exact: true }).click();
  const result = page.getByRole("region", { name: "Safety analytics result" });
  await expect(result.getByRole("status")).toHaveText(expected.answer);
  await expect(result.getByText("Database query · no LLM", { exact: true })).toBeVisible();
  await result.getByText("Technical details", { exact: true }).click();
  await expect(result.locator("pre")).toContainText("safety_incidents");
  await expect(result.getByText(/Rows returned: 1/)).toBeVisible();
  await page.getByRole("button", { name: "What is our most common hazard this month?", exact: true }).click();
  await expect(result.getByRole("img", { name: "Safety metric by group from database results" })).toBeVisible();
  await page.getByRole("button", { name: "Which hazards are recurring?", exact: true }).click();
  await expect(result.getByLabel("Supporting database rows")).toBeVisible();
  await expect(result.getByText("Query interpretation", { exact: true })).toBeVisible();
  await page.screenshot({ path: "test-results/analyst-recurring.png", fullPage: true });
});

test("malicious and unsupported questions return no invented answer or mutation", async ({ page, request }) => {
  const before = await (await request.get(api + "/incidents")).json();
  await page.goto("/analyst");
  // Streaming can briefly contain a hidden server copy; require one settled form.
  await expect(page.getByLabel("Ask about safety data")).toHaveCount(1);
  await page.getByLabel("Ask about safety data").fill("Delete all incidents.");
  await page.getByRole("button", { name: "Submit question" }).click();
  await expect(page.getByRole("heading", { name: "Request rejected" })).toBeVisible();
  const after = await (await request.get(api + "/incidents")).json();
  expect(after).toEqual(before);
  await page.getByLabel("Ask about safety data").fill("What is the price of concrete?");
  await page.getByRole("button", { name: "Submit question" }).click();
  await expect(page.getByRole("heading", { name: "Question not supported" })).toBeVisible();
  await expect(page.getByLabel("Supporting database rows")).toHaveCount(0);
});

test("no-data and mobile analytics results remain clear and fit the page", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/analyst");
  // Streaming can briefly contain a hidden server copy; require one settled form.
  await expect(page.getByLabel("Ask about safety data")).toHaveCount(1);
  await page.getByLabel("Ask about safety data").fill('What is our incident closure rate at site "No Such Site"?');
  await page.getByRole("button", { name: "Submit question" }).click();
  await expect(page.getByText("No matching safety records were found for this query and time period.", { exact: true })).toBeVisible();
  await page.getByLabel("Ask about safety data").fill("Show critical incidents from the last 30 days.");
  await page.getByRole("button", { name: "Submit question" }).click();
  await expect(page.getByLabel("Supporting database rows")).toBeVisible();
  await page.getByText("Technical details", { exact: true }).click();
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: "test-results/analyst-mobile.png", fullPage: true });
});

test("analyst reports API failure without a synthetic result", async ({ page }) => {
  await page.route("**/api/v1/analyst/query", route => route.fulfill({ status: 503, json: { detail: "Analytics temporarily unavailable." } }));
  await page.goto("/analyst");
  // Streaming can briefly contain a hidden server copy; require one settled form.
  await expect(page.getByLabel("Ask about safety data")).toHaveCount(1);
  await page.getByRole("button", { name: "What is our incident closure rate?", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Analytics temporarily unavailable." })).toHaveText("Analytics temporarily unavailable.");
  await expect(page.getByRole("region", { name: "Safety analytics result" })).toHaveCount(0);
});
