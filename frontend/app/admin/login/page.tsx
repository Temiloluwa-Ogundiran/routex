"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { AuthFormShell } from "../../../components/auth/auth-form-shell";
import { PushButton } from "../../../components/ui/push-button";

type AdminLoginFormState = {
  email: string;
  password: string;
};

function getSafeRedirectTarget(nextValue: string | null) {
  if (!nextValue || !nextValue.startsWith("/admin")) {
    return "/admin";
  }

  return nextValue;
}

function AdminLoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [formState, setFormState] = useState<AdminLoginFormState>({
    email: "",
    password: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/admin/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formState),
      });
      const responseBody = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          responseBody?.detail ?? responseBody?.message ?? "Unable to sign in as admin",
        );
      }

      router.replace(getSafeRedirectTarget(searchParams.get("next")));
      router.refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to sign in as admin",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthFormShell
      badge="Admin access"
      description="Sign in to manage RouteX admin tools."
      title="Sign in to RouteX Admin"
    >
      <div className="auth-shell__card-header">
        <div>
          <p className="playground-panel__eyebrow">Control room</p>
          <h2>Enter your admin credentials</h2>
        </div>
        <span className="playground-status-chip">Admin only</span>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="auth-field">
          <span className="dashboard-control-label">Email</span>
          <input
            className="dashboard-control-input"
            name="email"
            onChange={(event) =>
              setFormState((currentState) => ({
                ...currentState,
                email: event.target.value,
              }))
            }
            type="email"
            value={formState.email}
          />
        </label>

        <label className="auth-field">
          <span className="dashboard-control-label">Password</span>
          <input
            className="dashboard-control-input"
            name="password"
            onChange={(event) =>
              setFormState((currentState) => ({
                ...currentState,
                password: event.target.value,
              }))
            }
            type="password"
            value={formState.password}
          />
        </label>

        {errorMessage ? (
          <p className="auth-form__message auth-form__message--error">
            {errorMessage}
          </p>
        ) : null}

        <PushButton disabled={isSubmitting} type="submit">
          {isSubmitting ? "Signing in..." : "Sign in as admin"}
        </PushButton>
      </form>

      <p className="auth-form__switch">
        Need the merchant app instead? <Link href="/login">Sign in here</Link>
      </p>
    </AuthFormShell>
  );
}

export default function AdminLoginPage() {
  return (
    <Suspense fallback={null}>
      <AdminLoginPageContent />
    </Suspense>
  );
}
