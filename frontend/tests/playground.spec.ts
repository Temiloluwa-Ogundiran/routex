import { expect, test } from "@playwright/test";

test("sandbox route redirects into the mintlify collections docs", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/sandbox");

  await expect(page).toHaveURL("http://127.0.0.1:3001/collections");
  await expect(page.getByRole("heading", { name: "Collections" })).toBeVisible();
});

test("verification docs show the normalized verify endpoint", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/docs/verification");

  await expect(
    page.getByText("GET /api/v1/transactions/verify"),
  ).toBeVisible();
});

test("webhook docs show the normalized merchant signature header", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/docs/webhooks");

  await expect(page.getByText("X-AGGREGATOR-SIGNATURE")).toBeVisible();
  await expect(page.getByText("charge.success")).toBeVisible();
  await expect(page.getByText("notification_url")).toBeVisible();
});
