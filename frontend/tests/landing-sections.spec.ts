import { expect, test } from "@playwright/test";

test("landing page includes the key product sections", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await expect(
    page.getByRole("heading", { name: "Smart Routing" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /How It Works/i }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "READY TO ROUTE SMARTER?" }),
  ).toBeVisible();
});
