import { expect, test } from "@playwright/test";

test("sandbox playground shows a disabled state when sandbox wiring is missing", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:3000");

  await expect(page.getByText("Sandbox unavailable", { exact: true })).toBeVisible();
  await expect(
    page.getByText(/sandbox requests are disabled until routex_api_base_url/i),
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
