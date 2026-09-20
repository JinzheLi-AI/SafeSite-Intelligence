import { test, expect, type Page } from "@playwright/test";
const source = { kind: "REAL_AI", provider: "openai", model_name: "offline-browser-model", prompt_version: "vision-v1" };
const risk = { severity: 5, exposure: 4, probability: 1, raw_score: 20, final_score: 85, risk_level: "CRITICAL", confidence: .55, requires_human_review: true, policy_version: "risk-v1", overrides: ["Working-at-height minimum score: 85"], formula: "Severity x Exposure x Probability" };
const candidate = { id: 1, hazard_type: "working_at_height", title: "Possible elevated edge exposure", description: "Elevation is partly obscured.", evidence: ["Worker appears beside an elevated slab edge."], confidence: .55, risk_score: 85, risk_level: "CRITICAL", risk_breakdown: risk, recommended_actions: ["Inspect the edge and restrict access."], citations: [], ai_generated: true };
async function prepare(page: Page, uncertain = false, failFirst = false, provider = "openai") {
  let calls = 0;
  const inspection = { id: 9001, project_id: 1, site_id: 1, location_text: "New uploaded site", source_type: "IMAGE", image_path: "/uploads/test.jpg", description: null, status: "CREATED", created_at: new Date().toISOString(), completed_at: null, hazards: [], incident_ids: [], review_notes: null, analysis_json: null, analysis_source: { ...source, provider } };
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace("/api/v1", "");
    if (path === "/health") return route.fulfill({ json: { status: "ok", ai_mode: "real", ai_ready: true, ai_error: null, vision_model: "offline-browser-model" } });
    if (path === "/projects") return route.fulfill({ json: [{ id: 1, name: "Test project", code: "TEST", location: "Test", sites: [{ id: 1, project_id: 1, name: "Test site", zone: "A" }] }] });
    if (path === "/uploads") return route.fulfill({ status: 201, json: { image_path: "/uploads/test.jpg" } });
    if (path === "/inspections" && route.request().method() === "GET") return route.fulfill({ json: [] });
    if (path === "/inspections") return route.fulfill({ status: 201, json: inspection });
    if (path.endsWith("/analyze")) {
      calls++;
      if (failFirst && calls === 1) return route.fulfill({ status: 504, json: { detail: "AI analysis timed out. Please retry; no demo fallback was used." } });
      return route.fulfill({ json: { ...inspection, status: "ANALYZED", hazards: uncertain ? [candidate] : [], analysis_json: { summary: uncertain ? "Limited view of a possible hazard." : "No supported hazard is visually established.", overall_confidence: uncertain ? .55 : .92, requires_human_review: uncertain, reasoning_notes: uncertain ? ["Insufficient evidence: image partly occluded."] : [] } } });
    }
    return route.fulfill({ json: inspection });
  });
  await page.goto("/inspections");
  await expect(page.getByText("REAL AI provider", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Analyze Site", exact: true })).toBeDisabled();
  await page.locator('input[type="file"]').setInputFiles({ name: "brand-new.png", mimeType: "image/png", buffer: Buffer.from("offline browser upload fixture") });
  await page.getByRole("button", { name: "Analyze Site", exact: true }).click();
}
test("real zero-hazard result is honest and has no incident confirmation", async ({ page }) => {
  await prepare(page);
  await expect(page.getByRole("heading", { name: "No supported hazards confidently identified in this image." })).toBeVisible();
  await expect(page.getByText("Analysis source: REAL AI", { exact: true })).toBeVisible();
  await expect(page.getByText("This AI-assisted assessment does not replace a formal safety inspection.", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Confirm Findings", exact: true })).toHaveCount(0);
  await expect(page.getByText("Demo regulation data", { exact: true })).toHaveCount(0);
  await page.screenshot({ path: "test-results/real-zero-offline.png", fullPage: true });
});
test("real uncertain findings preserve evidence, deterministic risk and review", async ({ page }) => {
  await prepare(page, true);
  await expect(page.getByText("Insufficient / uncertain evidence", { exact: true })).toBeVisible();
  await expect(page.getByText(candidate.evidence[0], { exact: true })).toBeVisible();
  await expect(page.getByText(candidate.recommended_actions[0], { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Human Review Required", exact: true })).toBeVisible();
  await expect(page.getByText(risk.overrides[0], { exact: true })).toBeVisible();
  await expect(page.getByText("Demo regulation data", { exact: true })).toHaveCount(0);
  await page.screenshot({ path: "test-results/real-uncertain-offline.png", fullPage: true });
});
test("real provider error can retry the saved inspection without demo fallback", async ({ page }) => {
  await prepare(page, false, true);
  await expect(page.getByText("AI analysis timed out. Please retry; no demo fallback was used.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Run saved inspection analysis", exact: true }).click();
  await expect(page.getByText("Analysis source: REAL AI", { exact: true })).toBeVisible();
});

test("interrupted inspection stays in history and can retry its saved image", async ({ page }) => {
  const saved = { id: 9020, project_id: 1, site_id: 1, location_text: "Interrupted saved site", source_type: "IMAGE", image_path: "/uploads/preserved.jpg", status: "ANALYZING", created_at: new Date().toISOString(), hazards: [], incident_ids: [], analysis_json: null, analysis_source: source };
  await page.route("**/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/health")) return route.fulfill({ json: { ai_mode: "real", ai_ready: true, ai_error: null } });
    if (path.endsWith("/projects")) return route.fulfill({ json: [] });
    if (path.endsWith("/inspections")) return route.fulfill({ json: [saved] });
    if (path.endsWith("/analyze")) return route.fulfill({ json: { ...saved, status: "ANALYZED", analysis_json: { summary: "Recovered saved image.", overall_confidence: .92, requires_human_review: false, reasoning_notes: [] } } });
    return route.fulfill({ json: saved });
  });
  await page.goto("/inspections");
  await page.getByRole("button", { name: /Interrupted saved site/ }).click();
  await expect(page.getByText(/Your uploaded image and context are preserved/)).toBeVisible();
  await expect(page.locator('input[type="file"]')).toHaveCount(0);
  await page.getByRole("button", { name: "Run saved inspection analysis" }).click();
  await expect(page.getByText("Recovered saved image.", { exact: true })).toBeVisible();
  await expect(page.getByText("Analysis source: REAL AI", { exact: true })).toBeVisible();
});


test("DeepSeek provenance displays provider model and prompt", async ({ page }) => {
  await prepare(page, false, false, "deepseek");
  await expect(page.getByText("deepseek / offline-browser-model / vision-v1", { exact: true })).toBeVisible();
});
