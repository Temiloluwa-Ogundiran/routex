import { test, expect } from "@playwright/test";

test("landing page renders RouteX hero shell", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");
  await expect(
    page.getByRole("heading", { name: /fluid payments/i }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: /view docs/i })).toBeVisible();
});
