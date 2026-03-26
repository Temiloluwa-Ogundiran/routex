import { expect, test } from "@playwright/test";

test("landing shell uses the hyper-saturated routex visual system", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  const header = page.getByRole("banner");

  await expect(header.getByText("RouteX", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: /route every payment with control/i })).toBeVisible();
  await expect(header.getByRole("link", { name: /get started/i })).toBeVisible();
  await expect(page.locator("body")).toContainText("Collections, payouts, and failover");
});
