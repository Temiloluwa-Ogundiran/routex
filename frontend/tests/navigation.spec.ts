import { expect, test } from "@playwright/test";

test("public header routes guests into docs and signup", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await page.locator(".site-header__nav").getByRole("link", { name: "Docs" }).click();
  await expect(page).toHaveURL(/\/docs$/);

  await page.goto("http://127.0.0.1:3000");
  await page.locator(".site-header").getByRole("link", { name: /get started/i }).click();
  await expect(page).toHaveURL(/\/signup$/);

  await page.goto("http://127.0.0.1:3000");
  await page.locator(".site-header").getByRole("link", { name: "Log in" }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("landing call-to-actions route into docs and signup", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await page.getByRole("link", { name: /get started/i }).first().click();
  await expect(page).toHaveURL(/\/signup$/);

  await page.goto("http://127.0.0.1:3000");
  await page.getByRole("link", { name: /open docs/i }).first().click();
  await expect(page).toHaveURL(/\/docs$/);
});

test("signed-in users see product actions instead of guest auth ctas", async ({
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

  await page.goto("http://127.0.0.1:3000");

  const header = page.locator(".site-header");
  await expect(header.getByRole("link", { name: "Log in" })).toHaveCount(0);
  await expect(header.getByRole("link", { name: /get started/i })).toHaveCount(0);
  await expect(header.getByRole("link", { name: "Dashboard" })).toBeVisible();
  await expect(header.getByRole("link", { name: "Docs" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
});

test("signed-in users are redirected away from auth pages", async ({ page }) => {
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

  await page.goto("http://127.0.0.1:3000/login");
  await expect(page).toHaveURL(/\/dashboard$/);
});

test("footer routes to docs instead of a standalone sandbox app", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await page.getByRole("link", { name: "Docs" }).last().click();
  await expect(page).toHaveURL(/\/docs$/);
});
