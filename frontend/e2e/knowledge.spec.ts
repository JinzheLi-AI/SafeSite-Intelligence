import { test, expect, type Page } from "@playwright/test";
const source = {
 id: "official-fixture", document_id: 1, document_title: "Official source UI fixture", authority: "Hong Kong Labour Department",
 jurisdiction: "Hong Kong", document_type: "safety_guide", version: "Fixture edition", effective_date: null,
 verified: true, active: true, is_demo: false, source_url: "https://www.labour.gov.hk/eng/public/os/D/Overview_of_Work_at_Height_Safety.pdf",
 source_reference: "https://www.labour.gov.hk/eng/public/os/D/Overview_of_Work_at_Height_Safety.pdf",
 excerpt: "Offline browser fixture for source presentation.", section: "4.1", chunk_count: 4, indexed_chunk_count: 3,
};
async function prepare(page: Page, status: string) {
 await page.route("**/api/v1/knowledge/**", route => {
  if (route.request().url().includes("/knowledge/context")) return route.continue();
  if (route.request().method() === "GET") return route.fulfill({ json: [source] });
  return route.fulfill({ json: { status, message: status === "success" ? "Relevant official safety guidance retrieved." : status === "no_match" ? "No sufficiently relevant verified safety source was retrieved." : "Verified knowledge index is unavailable for this embedding model.", candidate_count: 4, latency_ms: 12,
    citations: status === "success" ? [{ ...source, id: undefined, chunk_id: 9, page_number: 7, retrieval_score: .76, excerpt: "Fixture passage describing suitable working platforms and edge protection." }] : [] } });
 });
 await page.goto("/knowledge");
 await page.getByLabel("Search official safety passages").fill("fall protection exposed slab edge");
 await page.getByRole("button", { name: "Search verified guidance", exact: true }).click();
}
test("verified source search displays source type, original passage and PDF link", async ({ page }) => {
 await prepare(page, "success");
 const results=page.getByLabel("Verified search results");
 await expect(results.getByText("VERIFIED SOURCE", { exact: true })).toBeVisible();
 await expect(results.getByText("Fixture passage describing suitable working platforms and edge protection.", { exact: true })).toBeVisible();
 await expect(results.getByRole("link", { name: "Open official source" })).toHaveAttribute("href", source.source_url+"#page=7");
 await expect(results.getByText(/safety guide/)).toBeVisible();
 await expect(page.locator(".document-card").getByText("3 indexed / 4 stored", { exact: true })).toBeVisible();
});
test("weak retrieval returns explicit no-evidence state", async ({ page }) => {
 await prepare(page, "no_match");
 await expect(page.getByText("No sufficiently relevant verified safety source was retrieved.", { exact: true })).toBeVisible();
 await expect(page.getByLabel("Verified search results").locator(".citation-card")).toHaveCount(0);
});
test("unavailable index never substitutes a citation", async ({ page }) => {
 await prepare(page, "unavailable");
 await expect(page.getByText("Verified knowledge index is unavailable for this embedding model.", { exact: true })).toBeVisible();
 await expect(page.getByLabel("Verified search results").locator(".citation-card")).toHaveCount(0);
});
