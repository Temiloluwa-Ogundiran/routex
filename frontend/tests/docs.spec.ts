import { expect, test } from "@playwright/test";

test("docs page shows the public verify endpoint contract", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/docs");

  await expect(page.getByText("OpenAPI source")).toBeVisible();
  await expect(page.getByText("/public/openapi.json")).toBeVisible();
  await expect(page.getByText("/api/v1/transactions/verify")).toBeVisible();
  await expect(page.getByText("GET")).toBeVisible();
});
