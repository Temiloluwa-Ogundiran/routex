import { expect, test } from "@playwright/test";

test("payment status page renders success state", async ({ page }) => {
  await page.goto(
    "http://127.0.0.1:3000/pay/status?reference=TXN_1&status=success&selected_gateway=isw&gateway_reference=ISW_PROC_001",
  );

  await expect(
    page.getByRole("heading", { name: /payment confirmed/i }),
  ).toBeVisible();
  await expect(page.getByText("TXN_1")).toBeVisible();
  await expect(page.getByLabel("Payment summary").getByText("Interswitch")).toBeVisible();
});

test("payment status page keeps manual continue visible for pending payments", async ({
  page,
}) => {
  await page.goto(
    "http://127.0.0.1:3000/pay/status?reference=TXN_2&status=pending&selected_gateway=isw&gateway_reference=ISW_PROC_002&next=http%3A%2F%2F127.0.0.1%3A3000%2Fdocs",
  );

  await expect(
    page.getByRole("heading", { name: /payment pending/i }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: /continue to merchant/i }),
  ).toHaveAttribute("href", "http://127.0.0.1:3000/docs");
});

test("payment status page auto-forwards successful payments", async ({ page }) => {
  await page.goto(
    "http://127.0.0.1:3000/pay/status?reference=TXN_3&status=success&selected_gateway=isw&gateway_reference=ISW_PROC_003&next=http%3A%2F%2F127.0.0.1%3A3000%2Fdocs",
  );

  await expect(page.getByText(/redirecting you in/i)).toBeVisible();
  await page.waitForURL("http://127.0.0.1:3000/docs");
  await expect(
    page.getByRole("heading", {
      name: /routex api reference/i,
    }),
  ).toBeVisible();
});
