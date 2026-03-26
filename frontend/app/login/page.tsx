"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { AuthFormShell } from "../../components/auth/auth-form-shell";
import { PushButton } from "../../components/ui/push-button";
import {
  PendingAuthRecord,
  storePendingAuthRecord,
} from "../../lib/auth-session";

type LoginFormState = {
  email: string;
  password: string;
};

function getSafeRedirectTarget(nextValue: string | null) {
  if (!nextValue || !nextValue.startsWith("/")) {
    return "/dashboard";
  }

  return nextValue;
}

function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formState, setFormState] = useState<LoginFormState>({
    email: "",
    password: "",
  });

  useEffect(() => {
    const rememberedEmail = searchParams.get("email");
    if (rememberedEmail) {
      setFormState((currentState) => ({
        ...currentState,
        email: rememberedEmail,
      }));
    }
  }, [searchParams]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await fetch("/api/auth/login", {
        body: JSON.stringify(formState),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });
      const responseBody = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          responseBody?.detail ?? responseBody?.message ?? "Unable to send OTP",
        );
      }

      const pendingAuthRecord: PendingAuthRecord = {
        email: formState.email,
        mode: "login",
        password: formState.password,
        redirectTo: getSafeRedirectTarget(searchParams.get("next")),
      };
      storePendingAuthRecord(pendingAuthRecord);
      router.push(
        `/verify-otp?mode=login&email=${encodeURIComponent(formState.email)}`,
      );
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to send OTP",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthFormShell
      badge="User access"
      description="Sign in with your email and password to receive your one-time code."
      title="Sign in to RouteX"
    >
      <div className="auth-shell__card-header">
        <div>
          <p className="playground-panel__eyebrow">Welcome back</p>
          <h2>Enter your account details</h2>
        </div>
        <span className="playground-status-chip">Secure OTP</span>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="auth-field">
          <span className="dashboard-control-label">Email</span>
          <input
            className="dashboard-control-input"
            id="login-email"
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
            id="login-password"
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
          {isSubmitting ? "Sending code..." : "Send OTP"}
        </PushButton>
      </form>

      <p className="auth-form__switch">
        New here? <Link href="/signup">Create your RouteX account</Link>
      </p>
    </AuthFormShell>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginPageContent />
    </Suspense>
  );
}
