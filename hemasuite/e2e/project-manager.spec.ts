import { test, expect } from "@playwright/test";

test.describe("Project Manager", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/hpw/phases", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: "[]" })
    );
    await page.route("**/projects", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            { slug: "test-project", name: "Test Project", created_at: "2026-01-01" },
          ]),
        });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ slug: "new-project", name: "New Project" }),
      });
    });
    await page.goto("/");
    await page.getByRole("button", { name: "Projects" }).click();
  });

  test("shows project list", async ({ page }) => {
    await expect(page.getByText("Test Project")).toBeVisible();
  });

  test("has create project button", async ({ page }) => {
    await expect(page.getByRole("button", { name: /create|new/i })).toBeVisible();
  });

  test("shows project manager heading", async ({ page }) => {
    await expect(page.getByText(/project/i)).toBeVisible();
  });
});
