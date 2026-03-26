import { expect, test } from "@playwright/test";

test("landing page includes the new fluid product sections", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await expect(
    page.getByRole("heading", {
      name: /one control plane for collections, payouts, and failover/i,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: /built for operators who cannot afford blind spots/i,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: /launch faster with one routex integration/i,
    }),
  ).toBeVisible();
});
