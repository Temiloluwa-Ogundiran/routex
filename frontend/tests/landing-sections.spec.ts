import { expect, test } from "@playwright/test";

test("landing page includes the new brutalist section stack", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await expect(
    page.getByRole("heading", {
      name: /orchestrate payments without the psp circus\./i,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: /choose your route/i,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: /built to ship hard\./i,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: /ready to route\?/i,
    }),
  ).toBeVisible();
  await expect(page.getByText(/active gateway score/i)).toHaveCount(0);
  await expect(page.getByText(/hosted collections/i).first()).toBeVisible();
  await expect(page.getByText(/webhook relay/i).first()).toBeVisible();
});
