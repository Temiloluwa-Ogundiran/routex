import { expect, test } from "@playwright/test";

test("docs page shows standard reference sections and payload examples", async ({
  page,
}) => {
  await page.goto("http://127.0.0.1:3000/docs");

  await expect(
    page.getByRole("heading", {
      name: "RouteX API docs built from the live public contract.",
    }),
  ).toBeVisible();
  await expect(page.getByText("OpenAPI source")).toBeVisible();
  await expect(page.getByText("Public API reference unavailable")).toBeVisible();
  await expect(page.getByText("ROUTEX_API_BASE_URL")).toBeVisible();
});
