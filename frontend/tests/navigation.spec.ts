import { expect, test } from "@playwright/test";

test("landing header links route correctly", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await page.locator(".site-header__nav").getByRole("link", { name: "Docs" }).click();
  await expect(page).toHaveURL(/\/docs$/);

  await page.goto("http://127.0.0.1:3000");
  await page
    .locator(".site-header__nav")
    .getByRole("link", { name: "Dashboard" })
    .click();
  await expect(page).toHaveURL(/\/login\?next=%2Fdashboard$/);

  await page.goto("http://127.0.0.1:3000");
  await page.locator(".site-header").getByRole("link", { name: "Log In" }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("landing call-to-actions route correctly", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await page.getByRole("link", { name: "Start Testing" }).click();
  await expect(page).toHaveURL(/\/signup$/);

  await page.goto("http://127.0.0.1:3000");
  await page.getByRole("link", { name: "Try Sandbox" }).first().click();
  await expect(page).toHaveURL(/\/#quickstart$/);

  await page.goto("http://127.0.0.1:3000");
  await page.getByRole("link", { name: "View API Docs" }).first().click();
  await expect(page).toHaveURL(/\/docs$/);
});
