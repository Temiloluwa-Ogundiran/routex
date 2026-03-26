import { expect, test } from "@playwright/test";

test("docs root is served by mintlify with curated public content", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/docs");

  await expect(page.getByText("RouteX API Docs")).toBeVisible();
  await expect(page.getByText("What you can build")).toBeVisible();
  await expect(page.getByText("https://routexapi.xoroai.cloud")).toBeVisible();
});

test("docs collections page shows the public initiate contract", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/docs/collections");

  await expect(page.getByRole("heading", { name: "Collections" })).toBeVisible();
  await expect(page.getByText("gateway_code")).toBeVisible();
  await expect(page.getByText("notification_url")).toBeVisible();
  await expect(page.getByText("Example response")).toBeVisible();
});
