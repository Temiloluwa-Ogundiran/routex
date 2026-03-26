import { expect, test } from "@playwright/test";

test("sandbox playground shows a disabled state when sandbox wiring is missing", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:3000");

  await expect(page.getByText("Setup required", { exact: true })).toBeVisible();
  await expect(
    page.getByText(/sandbox access is not configured on this deployment yet/i),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Sandbox Unavailable" }),
  ).toBeDisabled();
});

test("verify tab reflects the public api contract", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await page.getByRole("tab", { name: "Verify" }).click();

  await expect(
    page.getByRole("heading", {
      name: "GET /api/v1/transactions/verify",
    }),
  ).toBeVisible();
});

test("playground api returns a clear configuration error when sandbox wiring is missing", async ({
  request,
}) => {
  const response = await request.post("http://127.0.0.1:3000/api/playground", {
    data: {
      endpointId: "initiate",
      payload: {
        reference: "ORD_1001",
      },
    },
  });

  expect(response.status()).toBe(503);
  await expect(response.json()).resolves.toMatchObject({
    live: false,
    sandbox: true,
  });
});

test("signed-in merchants see the sandbox as available when status wiring resolves", async ({
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

  await page.route("**/api/playground/status", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        available: true,
        statusLabel: "Merchant sandbox",
        message: "Signed in with your RouteX test workspace.",
      }),
    });
  });

  await page.goto("http://127.0.0.1:3000");

  await expect(page.getByRole("button", { name: "Send Request" })).toBeEnabled();
  await expect(page.getByText("Signed in with your RouteX test workspace.")).toBeVisible();
});
