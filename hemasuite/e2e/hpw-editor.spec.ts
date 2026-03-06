import { test, expect } from "@playwright/test";

test.describe("HPW Editor", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/hpw/phases", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { id: 1, name: "Topic Development", module: "phase1_topic" },
          { id: 2, name: "Research & Literature", module: "phase2_research" },
          { id: 3, name: "Journal Selection", module: "phase3_journal" },
        ]),
      })
    );
    await page.route("**/hpw/manuscript/**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ content: "" }),
      })
    );
    await page.goto("/");
  });

  test("renders phase cards", async ({ page }) => {
    await expect(page.getByText("Topic Development")).toBeVisible();
    await expect(page.getByText("Research & Literature")).toBeVisible();
    await expect(page.getByText("Journal Selection")).toBeVisible();
  });

  test("clicking phase card opens editor", async ({ page }) => {
    await page.getByText("Topic Development").click();
    await expect(page.getByText("Phase 1: Topic Development")).toBeVisible();
    await expect(page.getByText("Back to phases")).toBeVisible();
  });

  test("editor has Insert CSA Results button", async ({ page }) => {
    await page.getByText("Topic Development").click();
    await expect(page.getByRole("button", { name: /insert csa results/i })).toBeVisible();
  });

  test("back button returns to phase grid", async ({ page }) => {
    await page.getByText("Topic Development").click();
    await page.getByText("Back to phases").click();
    await expect(page.getByText("Research & Literature")).toBeVisible();
  });
});
