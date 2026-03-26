import { expect, test } from "@playwright/test";

test("unauthenticated dashboard redirects to login", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/dashboard");

  await expect(page).toHaveURL(/\/login(?:\?next=.*)?$/);
  await expect(
    page.getByRole("heading", { name: /sign in to routex/i }),
  ).toBeVisible();
});

test("login page renders the auth form", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/login");

  await expect(page.getByRole("heading", { name: /sign in to routex/i })).toBeVisible();
  await expect(page.getByText(/sign in with your email and password/i)).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByRole("button", { name: /continue/i })).toBeVisible();
});

test("signup page renders the registration form", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/signup");

  await expect(page.getByRole("heading", { name: /create your routex account/i })).toBeVisible();
  await expect(page.getByText(/verify your email/i)).toBeVisible();
  await expect(page.getByLabel("Full name")).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByRole("button", { name: /create account/i })).toBeVisible();
});

test("verify otp page renders the otp form", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/verify-otp");

  await expect(page.getByRole("heading", { name: /enter your email code/i })).toBeVisible();
  await expect(page.getByLabel("One-time code")).toBeVisible();
  await expect(page.getByRole("button", { name: /verify code/i })).toBeVisible();
});

test("forgot password page renders the recovery form", async ({ page }) => {
  await page.goto("http://127.0.0.1:3000/forgot-password");

  await expect(page.getByRole("heading", { name: /recover your routex account/i })).toBeVisible();
  await expect(page.getByText(/send a reset code to your inbox/i)).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByRole("button", { name: /send reset link/i })).toBeVisible();
});

test("reset password page renders the reset form", async ({ page }) => {
  await page.goto(
    "http://127.0.0.1:3000/reset-password?email=test%40example.com&code=sample-code",
  );

  await expect(page.getByRole("heading", { name: /reset your password/i })).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Reset code")).toBeVisible();
  await expect(page.getByRole("button", { name: /update password/i })).toBeVisible();
});
