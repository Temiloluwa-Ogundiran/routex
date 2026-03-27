import { expect, test } from "@playwright/test";

test("landing page renders the new brutalist poster hero", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await expect(
    page.getByRole("heading", {
      name: /orchestrate payments without the psp circus\./i,
    }),
  ).toBeVisible();
  await expect(page.getByText(/for builders & breakers/i)).toBeVisible();
  await expect(page.getByRole("link", { name: /view docs/i })).toBeVisible();
  await expect(page.locator(".acid-marquee")).toContainText(
    /routex ships loud.*checkout ready.*signed webhooks.*manual override/i,
  );
  await expect(
    page.getByRole("heading", { name: /choose your route/i }),
  ).toBeVisible();
  await expect(page.locator(".acid-showcase__frame")).toBeVisible();
});
