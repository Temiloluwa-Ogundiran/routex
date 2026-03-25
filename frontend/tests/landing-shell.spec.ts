import { test, expect } from "@playwright/test";

test("landing page renders RouteX hero shell", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");
  await expect(page.getByText("ROUTE EVERY PAYMENT")).toBeVisible();
});
