"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { AuthFormShell } from "../../components/auth/auth-form-shell";
import { PushButton } from "../../components/ui/push-button";

type SignupFormState = {
  email: string;
  name: string;
  password: string;
};

function getSafeRedirectTarget(nextValue: string | null) {
  if (!nextValue || !nextValue.startsWith("/")) {
    return "/dashboard";
  }

  return nextValue;
}

function SignupPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formState, setFormState] = useState<SignupFormState>({
    email: "",
    name: "",
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

  useEffect(() => {
    let cancelled = false;

    async function redirectIfAuthenticated() {
      const response = await fetch("/api/auth/me", {
        cache: "no-store",
        credentials: "same-origin",
      }).catch(() => null);

      if (!response?.ok || cancelled) {
        return;
      }

      router.replace(getSafeRedirectTarget(searchParams.get("next")));
      router.refresh();
    }

    void redirectIfAuthenticated();

    return () => {
      cancelled = true;
    };
  }, [router, searchParams]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const nextTarget = getSafeRedirectTarget(searchParams.get("next"));
      const response = await fetch("/api/auth/signup", {
        body: JSON.stringify({
          ...formState,
          redirectTo: nextTarget,
        }),
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

      router.push(
        `/verify-otp?mode=signup&email=${encodeURIComponent(formState.email)}&next=${encodeURIComponent(nextTarget)}`,
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
      badge="Create account"
      description="Create your account and confirm your email to open your RouteX workspace."
      title="Create your RouteX account"
    >
      <div className="auth-shell__card-header">
        <div>
          <p className="playground-panel__eyebrow">Get started</p>
          <h2>Set up your account details</h2>
        </div>
        <span className="playground-status-chip">Verified email</span>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="auth-field">
          <span className="dashboard-control-label">Full name</span>
          <input
            className="dashboard-control-input"
            id="signup-name"
            name="name"
            onChange={(event) =>
              setFormState((currentState) => ({
                ...currentState,
                name: event.target.value,
              }))
            }
            type="text"
            value={formState.name}
          />
        </label>

        <label className="auth-field">
          <span className="dashboard-control-label">Email</span>
          <input
            className="dashboard-control-input"
            id="signup-email"
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
            id="signup-password"
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
          {isSubmitting ? "Sending code..." : "Create account"}
        </PushButton>
      </form>

      <p className="auth-form__switch">
        Already have an account? <Link href="/login">Sign in instead</Link>
      </p>
    </AuthFormShell>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={null}>
      <SignupPageContent />
    </Suspense>
  );
}
