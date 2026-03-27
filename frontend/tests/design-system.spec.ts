import { expect, test } from "@playwright/test";

test("landing shell uses the acid neo-brutalist public system", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  const header = page.getByRole("banner");

  await expect(header.getByText("RouteX", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("heading", {
      name: /orchestrate payments without the psp circus\./i,
    }),
  ).toBeVisible();
  await expect(header.getByRole("link", { name: /get started/i })).toBeVisible();
  await expect(page.locator("body")).toContainText("For builders & breakers");
  await expect(page.locator("body")).not.toContainText("Active gateway score");
});
