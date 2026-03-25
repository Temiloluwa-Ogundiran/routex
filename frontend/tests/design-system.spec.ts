import { expect, test } from "@playwright/test";

test("header and CTA use the branded visual system", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  const header = page.getByRole("banner");

  await expect(header.getByText("RouteX", { exact: true })).toBeVisible();
  await expect(
    header.getByRole("button", { name: "Start Testing" }),
  ).toBeVisible();
});
