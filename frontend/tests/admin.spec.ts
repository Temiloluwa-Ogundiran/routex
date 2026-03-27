import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";

async function grantAdminSession(page: Page) {
  await page.context().addCookies([
    {
      name: "routex_admin_session",
      value: "demo-admin-session",
      url: "http://127.0.0.1:3000",
    },
  ]);
}

async function mockAdminDashboard(page: Page) {
  await page.route("**/api/admin/router", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        summary: {
          total_gateways: 4,
          active_gateways: 3,
          recent_failover_count: 2,
          routed_transaction_count: 31,
        },
        gateway_health: [
          {
            gateway_code: "pstk",
            gateway_name: "Paystack",
            is_active: true,
            supports_collections: true,
            supports_payouts: false,
            priority_weight: 1.0,
            success_rate_5m: 96.2,
            success_rate_1h: 94.8,
            timeout_rate_5m: 1.1,
            p95_latency_ms: 720,
            circuit_state: "closed",
            last_checked_at: "2026-03-25T13:00:00.000Z",
          },
        ],
        recent_transactions: [
          {
            reference: "ROUTEX-ADMIN-1001",
            selected_gateway: "pstk",
            status: "success",
            amount: 42500,
            currency: "NGN",
            created_at: "2026-03-25T12:59:00.000Z",
          },
        ],
        recent_failovers: [
          {
            reference: "ROUTEX-FAILOVER-77",
            selected_gateway: "kora",
            attempt_count: 2,
            fallback_order: ["pstk", "kora"],
            created_at: "2026-03-25T12:48:00.000Z",
          },
        ],
      }),
    });
  });

  await page.route("**/api/admin/router/rules", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          id: 44,
          name: "Latency Shield Rule",
          operation: "collection",
          channel: "card",
          min_amount: 5000,
          max_amount: 50000,
          allow_gateways: ["pstk", "fltw"],
          deny_gateways: ["isw"],
          force_priority_order: ["pstk"],
          enabled: true,
          created_at: "2026-03-25T12:40:00.000Z",
          updated_at: "2026-03-25T12:58:00.000Z",
        },
      ]),
    });
  });
}

test("unauthenticated admin routes redirect to admin login", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/admin");

  await expect(page).toHaveURL(/\/admin\/login(?:\?next=.*)?$/);
  await expect(
    page.getByRole("heading", { name: /sign in to routex admin/i }),
  ).toBeVisible();
});

test("admin login page renders the admin auth form", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/admin/login");

  await expect(
    page.getByRole("heading", { name: /sign in to routex admin/i }),
  ).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByRole("button", { name: /sign in as admin/i })).toBeVisible();
});

test("stale admin cookies do not loop the login page", async ({ page }) => {
  await grantAdminSession(page);
  await page.route("**/api/admin/me", async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Admin authentication required." }),
    });
  });

  await page.goto("http://127.0.0.1:3000/admin/login");

  await expect(page).toHaveURL(/\/admin\/login(?:\?next=.*)?$/);
  await expect(
    page.getByRole("heading", { name: /sign in to routex admin/i }),
  ).toBeVisible();
});

test("admin route shows the router control room when a session cookie exists", async ({
  page,
}) => {
  await grantAdminSession(page);
  await mockAdminDashboard(page);
  await page.goto("http://127.0.0.1:3000/admin");

  await expect(page.locator("body")).toHaveAttribute("data-rx-surface", "ops");
  await expect(page.getByText(/main menu/i)).toBeVisible();
  await expect(page.getByRole("link", { name: /gateway health/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /routing rules/i })).toBeVisible();
  const accountMenuButton = page
    .locator(".ops-topbar")
    .getByRole("button", { name: /open account menu/i });
  await expect(accountMenuButton).toBeVisible();
  await accountMenuButton.click();
  await expect(
    page.locator(".ops-account-menu__panel").getByRole("button", { name: /sign out/i }),
  ).toBeVisible();
  await expect(
    page.locator(".ops-topbar").getByRole("link", { name: /api docs/i }),
  ).toHaveAttribute("target", "_blank");
  await expect(
    page.getByRole("heading", { name: /watch routex move traffic before conversion drops/i }),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Gateway Health" })).toBeVisible();
  await expect(page.getByText("Live").first()).toBeVisible();
  await expect(page.getByText("ROUTEX-ADMIN-1001")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Latency Shield Rule" }),
  ).toBeVisible();
});
