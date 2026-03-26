import { test, expect } from "@playwright/test";

test("landing page renders RouteX hero shell", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");
  await expect(
    page.getByRole("heading", { name: /route every payment with control/i }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: /read the docs/i })).toBeVisible();
});
