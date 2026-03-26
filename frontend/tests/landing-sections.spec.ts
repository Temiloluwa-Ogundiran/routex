import { expect, test } from "@playwright/test";

test("landing page includes the new fluid product sections", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await expect(
    page.getByRole("heading", {
      name: /fluid payments/i,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: /everything you need\./i,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: /ready to flow\?/i,
    }),
  ).toBeVisible();
});
