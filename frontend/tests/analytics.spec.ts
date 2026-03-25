import { expect, test } from "@playwright/test";

test("posthog boots when public analytics env is configured", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000");

  await expect
    .poll(async () =>
      page.evaluate(
        () =>
          typeof (
            window as Window & {
              posthog?: { capture?: unknown };
            }
          ).posthog?.capture === "function",
      ),
    )
    .toBe(true);
});
