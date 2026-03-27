import { expect, test } from "@playwright/test";

test("public header renders the brutalist shell and routes guests into docs and signup", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:3000");

  await expect(page.locator(".site-header__ticker")).toBeVisible();
  await expect(page.locator(".site-header__brand")).toContainText("RouteX");
  await expect(page.locator(".site-header__nav")).toContainText("Product");
  await expect(page.locator(".site-header__nav")).toContainText("Why RouteX");
  await expect(page.locator(".site-header__nav")).toContainText("Docs");

  await page.locator(".site-header__nav").getByRole("link", { name: "Docs" }).click();
  await expect(page).toHaveURL("http://127.0.0.1:3001/");

  await page.goto("http://127.0.0.1:3000");
  await page.locator(".site-header").getByRole("link", { name: /get started/i }).click();
  await expect(page).toHaveURL(/\/signup$/);

  await page.goto("http://127.0.0.1:3000");
  await page.locator(".site-header").getByRole("link", { name: /log in/i }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("landing call-to-actions route into docs and signup", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await page.getByRole("link", { name: "Get Started" }).last().click();
  await expect(page).toHaveURL(/\/signup$/);

  await page.goto("http://127.0.0.1:3000");
  await page.getByRole("link", { name: "View Docs" }).first().click();
  await expect(page).toHaveURL("http://127.0.0.1:3001/");
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

test("footer keeps only useful actions and can hand off an email into signup", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:3000");

  const footer = page.locator(".site-footer");

  await expect(footer).toContainText("RouteX");
  await expect(footer.getByRole("link", { name: "Docs" })).toBeVisible();
  await expect(footer.getByRole("link", { name: /admin/i })).toHaveCount(0);

  await footer.getByRole("link", { name: "Docs" }).click();
  await expect(page).toHaveURL("http://127.0.0.1:3001/");

  await page.goto("http://127.0.0.1:3000");
  await footer.getByLabel("Work email").fill("builder@example.com");
  await footer.getByRole("button", { name: /submit/i }).click();
  await expect(page).toHaveURL(/\/signup\?email=builder%40example\.com$/);
});
