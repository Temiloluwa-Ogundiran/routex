import { expect, test } from "@playwright/test";

test("unauthenticated dashboard redirects to login", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/dashboard");

  await expect(page).toHaveURL(/\/login(?:\?next=.*)?$/);
  await expect(
    page.getByRole("heading", { name: /^sign in to routex$/i }),
  ).toBeVisible();
});

test("login page renders the auth form", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/login");

  await expect(page.locator("body")).toHaveAttribute("data-rx-surface", "public");
  await expect(
    page.getByRole("heading", { name: /^sign in to routex$/i }),
  ).toBeVisible();
  await expect(page.getByText(/merchant access/i)).toBeVisible();
  await expect(
    page.getByText(/use your email and password to receive your access code\./i),
  ).toBeVisible();
  await expect(page.getByText(/session|jwt|backend auth flow/i)).toHaveCount(0);
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByRole("button", { name: /send code/i })).toBeVisible();
});

test("signup page renders the registration form", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/signup");

  await expect(
    page.getByRole("heading", { name: /open your routex workspace/i }),
  ).toBeVisible();
  await expect(
    page.getByText(/create your team, verify your inbox, and start routing payments\./i),
  ).toBeVisible();
  await expect(page.getByLabel("Full name")).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByRole("button", { name: /create workspace/i })).toBeVisible();
});

test("verify otp page renders the otp form", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/verify-otp");

  await expect(page.getByRole("heading", { name: /enter your code/i })).toBeVisible();
  await expect(
    page.getByText(/drop the six-digit code from your inbox to unlock routex\./i),
  ).toBeVisible();
  await expect(page.getByLabel("One-time code")).toBeVisible();
  await expect(page.getByRole("button", { name: /verify code/i })).toBeVisible();
});

test("forgot password page renders the recovery form", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/forgot-password");

  await expect(
    page.getByRole("heading", { name: /reset your routex access/i }),
  ).toBeVisible();
  await expect(
    page.getByText(/we'll send a reset link to your inbox\./i),
  ).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByRole("button", { name: /send reset link/i })).toBeVisible();
});

test("reset password page renders the reset form", async ({ page }) => {
  await page.goto(
    "http://127.0.0.1:3000/reset-password?email=test%40example.com&code=sample-code",
  );

  await expect(
    page.getByRole("heading", { name: /choose a new password/i }),
  ).toBeVisible();
  await expect(
    page.getByText(/drop in the reset link details and lock your workspace back in\./i),
  ).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Reset code")).toBeVisible();
  await expect(page.getByRole("button", { name: /update password/i })).toBeVisible();
});
