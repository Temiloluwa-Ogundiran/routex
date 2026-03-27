import type { Page } from "@playwright/test";
import { expect, test } from "@playwright/test";

async function grantUserSession(page: Page) {
  await page.context().addCookies([
    {
      name: "routex_user_session",
      value: "demo-user-session",
      url: "http://127.0.0.1:3000",
    },
  ]);
}

test("dashboard renders the live merchant overview", async ({ page }) => {
  await grantUserSession(page);
  await page.route("**/api/app/dashboard**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: true,
        data: {
          user: {
            id: "user_123",
            name: "Ada Obi",
            email: "ada@example.com",
            is_verified: true,
          },
          merchants: [
            {
              id: "agg-ab123",
              name: "Ada Stores",
              email: "merchant@example.com",
              is_verified: true,
              is_active: true,
              joined_at: "2026-03-24T10:00:00.000Z",
              test_balance: 120500,
              live_balance: 840000,
              percentage_charge: 1.5,
              flat_charge: 0,
              role: "owner",
            },
          ],
          selected_merchant: {
            id: "agg-ab123",
            name: "Ada Stores",
            email: "merchant@example.com",
            is_verified: true,
            is_active: true,
            joined_at: "2026-03-24T10:00:00.000Z",
            test_balance: 120500,
            live_balance: 840000,
            percentage_charge: 1.5,
            flat_charge: 0,
            role: "owner",
          },
          mode: "test",
          period: "month",
          summary: {
            mode: "test",
            period: "month",
            revenue_metrics: {
              total_revenue: 280000,
              total_transactions: 18,
              total_charges: 4200,
              net_revenue: 275800,
              average_transaction_value: 15555.56,
              success_rate: 94.4,
            },
            transaction_breakdown: {
              successful: 17,
              pending: 1,
              failed: 0,
              total: 18,
            },
            top_currency: {
              currency: "NGN",
              total_revenue: 280000,
              transaction_count: 18,
              total_charges: 4200,
              net_revenue: 275800,
              average_transaction_value: 15555.56,
            },
            wallet_count: 1,
            total_balance: 120500,
            pending_payouts: 2,
            pending_payout_amount: 0,
          },
          wallets: [
            {
              id: 1,
              merchant_id: "agg-ab123",
              currency: "NGN",
              balance: 120500,
              mode: "test",
              percentage_charge: 1.5,
              flat_charge: 0,
              payout_percentage_charge: 0,
              payout_flat_charge: 50,
              is_active: true,
              created_at: "2026-03-24T10:01:00.000Z",
              updated_at: "2026-03-25T09:00:00.000Z",
            },
          ],
          transactions: {
            transactions: [
              {
                id: 11,
                type: "credit",
                mode: "test",
                reference: "ORD_1001",
                status: "success",
                currency: "NGN",
                amount: 25000,
                charge: 375,
                processor_reference: "fltw_001",
                customer: {
                  name: "Jane Doe",
                  email: "jane@example.com",
                  phone_number: null,
                  whatsapp_number: null,
                  merchant_id: "agg-ab123",
                },
                details: null,
                created_at: "2026-03-25T08:00:00.000Z",
              },
            ],
            total_items: 1,
            total_pages: 1,
            current_page: 1,
            page_size: 6,
            filters: {
              wallet_id: null,
              currency: null,
              transaction_type: null,
            },
          },
          payment_links: [
            {
              id: "plink_1",
              reference: "LINK_1001",
              title: "RouteX launch fee",
              merchant_id: "agg-ab123",
              url: "https://pay.example.com/LINK_1001",
              description: "Launch package",
              amount_type: "static",
              mode: "test",
              type: "one_time",
              currency: "NGN",
              amount: 25000,
              max_uses: 10,
              current_uses: 2,
              redirect_url: "https://merchant.example.com/callback",
              expires_at: null,
              _metadata: null,
              is_active: true,
              created_at: "2026-03-24T10:10:00.000Z",
              updated_at: "2026-03-25T08:30:00.000Z",
            },
          ],
          api_tokens: {
            merchant_id: "agg-ab123",
            live: {
              secret: "aggsk_live_123456789_agg-ab123",
              public: "aggpk_live_123456789_agg-ab123",
            },
            test: {
              secret: "aggsk_test_123456789_agg-ab123",
              public: "aggpk_test_123456789_agg-ab123",
            },
          },
          warnings: [],
        },
      }),
    });
  });
  await page.goto("http://127.0.0.1:3000/dashboard");

  await expect(page.locator("body")).toHaveAttribute("data-rx-surface", "ops");
  await expect(page.getByText(/main menu/i)).toBeVisible();
  await expect(page.getByRole("link", { name: /overview/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /transactions/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /^ada stores$/i })).toBeVisible();
  await expect(
    page.getByText(/see your balance, recent payments, and api keys in one place/i),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Log In" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Start Testing" })).toHaveCount(0);
  const accountMenuButton = page
    .locator(".ops-topbar")
    .getByRole("button", { name: /open account menu/i });
  await expect(accountMenuButton).toBeVisible();
  await accountMenuButton.click();
  await expect(page.locator(".ops-account-menu__panel").getByRole("button", { name: "Sign out" })).toBeVisible();
  await expect(page.locator(".ops-topbar").getByRole("link", { name: "API docs" })).toBeVisible();
  await expect(
    page.locator(".ops-topbar").getByRole("link", { name: "API docs" }),
  ).toHaveAttribute("target", "_blank");
  await expect(page.getByRole("link", { name: "Sandbox" })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: /workspace details/i })).toHaveCount(0);
  await expect(page.getByText("NGN 280,000.00")).toBeVisible();
  await expect(page.getByRole("heading", { name: /wallet balances/i })).toBeVisible();
  await expect(page.getByRole("heading", { name: /recent transactions/i })).toBeVisible();
  await expect(page.getByText("ORD_1001")).toBeVisible();
  await expect(page.getByText("RouteX launch fee")).toBeVisible();
  await expect(page.getByRole("heading", { name: /api keys/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /create link/i })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Gateway Controls" })).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Routing Rules" })).toHaveCount(0);
});

test("merchant sidebar keeps the selected merchant and mode in the url", async ({
  page,
}) => {
  await grantUserSession(page);
  await page.route("**/api/app/dashboard**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: true,
        data: {
          user: {
            id: "user_123",
            name: "Ada Obi",
            email: "ada@example.com",
            is_verified: true,
          },
          merchants: [
            {
              id: "agg-ab123",
              name: "Ada Stores",
              email: "merchant@example.com",
              is_verified: true,
              is_active: true,
              joined_at: "2026-03-24T10:00:00.000Z",
              test_balance: 120500,
              live_balance: 840000,
              percentage_charge: 1.5,
              flat_charge: 0,
              role: "owner",
            },
          ],
          selected_merchant: {
            id: "agg-ab123",
            name: "Ada Stores",
            email: "merchant@example.com",
            is_verified: true,
            is_active: true,
            joined_at: "2026-03-24T10:00:00.000Z",
            test_balance: 120500,
            live_balance: 840000,
            percentage_charge: 1.5,
            flat_charge: 0,
            role: "owner",
          },
          mode: "live",
          period: "month",
          summary: {
            mode: "live",
            period: "month",
            revenue_metrics: {
              total_revenue: 280000,
              total_transactions: 18,
              total_charges: 4200,
              net_revenue: 275800,
              average_transaction_value: 15555.56,
              success_rate: 94.4,
            },
            transaction_breakdown: {
              successful: 17,
              pending: 1,
              failed: 0,
              total: 18,
            },
            top_currency: {
              currency: "NGN",
              total_revenue: 280000,
              transaction_count: 18,
              total_charges: 4200,
              net_revenue: 275800,
              average_transaction_value: 15555.56,
            },
            wallet_count: 1,
            total_balance: 840000,
            pending_payouts: 2,
            pending_payout_amount: 0,
          },
          wallets: [],
          transactions: {
            transactions: [],
            total_items: 0,
            total_pages: 0,
            current_page: 1,
            page_size: 6,
            filters: {
              wallet_id: null,
              currency: null,
              transaction_type: null,
            },
          },
          payment_links: [],
          api_tokens: {
            merchant_id: "agg-ab123",
            live: {
              secret: "aggsk_live_123456789_agg-ab123",
              public: "aggpk_live_123456789_agg-ab123",
            },
            test: {
              secret: "aggsk_test_123456789_agg-ab123",
              public: "aggpk_test_123456789_agg-ab123",
            },
          },
          warnings: [],
        },
      }),
    });
  });

  await page.goto(
    "http://127.0.0.1:3000/dashboard?merchantId=agg-ab123&mode=live",
  );

  const overviewLink = page
    .locator(".ops-sidebar")
    .getByRole("link", { name: "Overview" });
  const walletsLink = page
    .locator(".ops-sidebar")
    .getByRole("link", { name: "Wallets" });
  const transactionsLink = page
    .locator(".ops-sidebar")
    .getByRole("link", { name: "Transactions" });

  await expect(overviewLink).toHaveAttribute(
    "href",
    "/dashboard?merchantId=agg-ab123&mode=live",
  );
  await expect(walletsLink).toHaveAttribute(
    "href",
    "/dashboard?merchantId=agg-ab123&mode=live#dashboard-wallets",
  );
  await expect(transactionsLink).toHaveAttribute(
    "href",
    "/dashboard?merchantId=agg-ab123&mode=live#dashboard-transactions",
  );

  await overviewLink.click();

  await expect(page).toHaveURL(
    /\/dashboard\?merchantId=agg-ab123&mode=live$/,
  );
});

test("api keys sidebar target lands on the api keys card", async ({ page }) => {
  await grantUserSession(page);
  await page.route("**/api/app/dashboard**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: true,
        data: {
          user: {
            id: "user_123",
            name: "Ada Obi",
            email: "ada@example.com",
            is_verified: true,
          },
          merchants: [
            {
              id: "agg-ab123",
              name: "Ada Stores",
              email: "merchant@example.com",
              is_verified: true,
              is_active: true,
              joined_at: "2026-03-24T10:00:00.000Z",
              test_balance: 120500,
              live_balance: 840000,
              percentage_charge: 1.5,
              flat_charge: 0,
              role: "owner",
            },
          ],
          selected_merchant: {
            id: "agg-ab123",
            name: "Ada Stores",
            email: "merchant@example.com",
            is_verified: true,
            is_active: true,
            joined_at: "2026-03-24T10:00:00.000Z",
            test_balance: 120500,
            live_balance: 840000,
            percentage_charge: 1.5,
            flat_charge: 0,
            role: "owner",
          },
          mode: "test",
          period: "month",
          summary: {
            mode: "test",
            period: "month",
            revenue_metrics: {
              total_revenue: 280000,
              total_transactions: 18,
              total_charges: 4200,
              net_revenue: 275800,
              average_transaction_value: 15555.56,
              success_rate: 94.4,
            },
            transaction_breakdown: {
              successful: 17,
              pending: 1,
              failed: 0,
              total: 18,
            },
            top_currency: {
              currency: "NGN",
              total_revenue: 280000,
              transaction_count: 18,
              total_charges: 4200,
              net_revenue: 275800,
              average_transaction_value: 15555.56,
            },
            wallet_count: 1,
            total_balance: 120500,
            pending_payouts: 2,
            pending_payout_amount: 0,
          },
          wallets: [
            {
              id: 1,
              merchant_id: "agg-ab123",
              currency: "NGN",
              balance: 120500,
              mode: "test",
              percentage_charge: 1.5,
              flat_charge: 0,
              payout_percentage_charge: 0,
              payout_flat_charge: 50,
              is_active: true,
              created_at: "2026-03-24T10:01:00.000Z",
              updated_at: "2026-03-25T09:00:00.000Z",
            },
          ],
          transactions: {
            transactions: [],
            total_items: 0,
            total_pages: 0,
            current_page: 1,
            page_size: 6,
            filters: {
              wallet_id: null,
              currency: null,
              transaction_type: null,
            },
          },
          payment_links: [],
          api_tokens: {
            merchant_id: "agg-ab123",
            live: {
              secret: "aggsk_live_123456789_agg-ab123",
              public: "aggpk_live_123456789_agg-ab123",
            },
            test: {
              secret: "aggsk_test_123456789_agg-ab123",
              public: "aggpk_test_123456789_agg-ab123",
            },
          },
          warnings: [],
        },
      }),
    });
  });

  await page.goto("http://127.0.0.1:3000/dashboard");

  await expect(
    page.locator("#dashboard-api-keys").getByRole("heading", { name: "API keys" }),
  ).toBeVisible();
});

test("dashboard transaction detail redirects back to the user dashboard", async ({ page }) => {
  await grantUserSession(page);
  await page.route("**/api/app/dashboard**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: true,
        data: {
          user: {
            id: "user_123",
            name: "Ada Obi",
            email: "ada@example.com",
            is_verified: true,
          },
          merchants: [],
          selected_merchant: null,
          mode: "test",
          period: "month",
          summary: null,
          wallets: [],
          transactions: {
            transactions: [],
            total_items: 0,
            total_pages: 0,
            current_page: 1,
            page_size: 6,
            filters: {
              wallet_id: null,
              currency: null,
              transaction_type: null,
            },
          },
          payment_links: [],
          api_tokens: null,
          warnings: [],
        },
      }),
    });
  });
  await page.goto("http://127.0.0.1:3000/dashboard/transactions/UNKNOWN_REF");

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: /create your first merchant workspace/i })).toBeVisible();
});
