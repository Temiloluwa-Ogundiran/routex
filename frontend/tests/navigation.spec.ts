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

test("signed-in public pages show sandbox and sign out actions instead of auth ctas", async ({
  page,
}) => {
  await page.context().addCookies([
    {
      name: "routex_user_session",
      value: "demo-user-session",
      url: "http://127.0.0.1:3000",
    },
  ]);

  await page.route("**/api/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "user_123",
        email: "ada@example.com",
        name: "Ada Obi",
      }),
    });
  });

  await page.goto("http://127.0.0.1:3000/docs");

  await expect(page.getByRole("link", { name: "Log In" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Start Testing" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Dashboard" }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Sandbox" }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
});
