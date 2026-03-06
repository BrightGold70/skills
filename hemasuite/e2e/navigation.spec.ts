import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses to avoid needing live sidecar
    await page.route("**/hpw/phases", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { id: 1, name: "Topic Development", module: "phase1_topic" },
          { id: 2, name: "Research & Literature", module: "phase2_research" },
        ]),
      })
    );
    await page.route("**/csa/scripts", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      })
    );
    await page.goto("/");
  });

  test("shows tab bar with all tabs", async ({ page }) => {
    await expect(page.getByRole("button", { name: "HPW" })).toBeVisible();
    await expect(page.getByRole("button", { name: "CSA" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Pipeline" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Projects" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Settings" })).toBeVisible();
  });

  test("switches tabs on click", async ({ page }) => {
    await page.getByRole("button", { name: "CSA" }).click();
    await expect(page.getByText("Statistical Analysis")).toBeVisible();
  });

  test("HPW tab is active by default", async ({ page }) => {
    await expect(page.getByText("Manuscript Editor")).toBeVisible();
  });
});
