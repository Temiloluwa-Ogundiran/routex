import { expect, test } from "@playwright/test";

test("sandbox playground renders on the landing page", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await expect(page.getByText("Sandbox only")).toBeVisible();
  await expect(page.getByRole("button", { name: "Send Request" })).toBeVisible();
});

test("verify tab reflects the public api contract", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await page.getByRole("tab", { name: "Verify" }).click();

  await expect(
    page.getByRole("heading", {
      name: "GET /api/v1/transactions/verify",
    }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Send Request" }).click();
  await expect(page.getByText('"method": "GET"')).toBeVisible();
});
