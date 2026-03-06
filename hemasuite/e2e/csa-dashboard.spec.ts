import { test, expect } from "@playwright/test";

test.describe("CSA Dashboard", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/hpw/phases", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: "[]" })
    );
    await page.route("**/csa/scripts", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          { name: "01_extract.R", path: "/scripts/01_extract.R" },
          { name: "02_validate.R", path: "/scripts/02_validate.R" },
        ]),
      })
    );
    await page.goto("/");
    await page.getByRole("button", { name: "CSA" }).click();
  });

  test("shows script list", async ({ page }) => {
    await expect(page.getByText("01_extract.R")).toBeVisible();
    await expect(page.getByText("02_validate.R")).toBeVisible();
  });

  test("shows run button for each script", async ({ page }) => {
    const buttons = page.locator("button", { hasText: /extract|validate/i });
    await expect(buttons).toHaveCount(2);
  });

  test("shows output after running script", async ({ page }) => {
    await page.route("**/csa/run", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ exit_code: 0, stdout: "Processing complete", stderr: "" }),
      })
    );
    await page.getByText("01_extract.R").click();
    await expect(page.getByText("Processing complete")).toBeVisible();
  });

  test("handles error state", async ({ page }) => {
    await page.route("**/csa/scripts", (route) =>
      route.fulfill({ status: 503, contentType: "application/json", body: '{"detail":"CSA_PATH not configured"}' })
    );
    await page.goto("/");
    await page.getByRole("button", { name: "CSA" }).click();
    await expect(page.getByText(/not configured/i)).toBeVisible();
  });
});
