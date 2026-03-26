"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

import { OtpFormShell } from "../../components/auth/otp-form-shell";
import { PushButton } from "../../components/ui/push-button";
import {
  PendingAuthRecord,
  clearPendingAuthRecord,
  readPendingAuthRecord,
} from "../../lib/auth-session";

type OtpFormState = {
  otp: string;
};

function getSafeRedirectTarget(nextValue: string | null) {
  if (!nextValue || !nextValue.startsWith("/")) {
    return "/dashboard";
  }

  return nextValue;
}

function VerifyOtpPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const requestedMode = searchParams.get("mode");
  const requestedEmail = searchParams.get("email");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [pendingAuth, setPendingAuth] = useState<PendingAuthRecord | null>(null);
  const [formState, setFormState] = useState<OtpFormState>({ otp: "" });

  useEffect(() => {
    setPendingAuth(readPendingAuthRecord());
  }, []);

  const effectivePendingAuth = useMemo(() => {
    if (pendingAuth) {
      return pendingAuth;
    }

    return requestedEmail && requestedMode
      ? ({
          email: requestedEmail,
          mode: requestedMode === "signup" ? "signup" : "login",
          name: "",
          password: "",
          redirectTo: getSafeRedirectTarget(searchParams.get("next")),
        } as PendingAuthRecord)
      : null;
  }, [pendingAuth, requestedEmail, requestedMode, searchParams]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    if (!effectivePendingAuth) {
      setErrorMessage("Start from login or signup, then enter the code here.");
      setIsSubmitting(false);
      return;
    }

    try {
      const endpoint =
        effectivePendingAuth.mode === "signup"
          ? "/api/auth/signup/verify-otp"
          : "/api/auth/login/verify-otp";
      const payload =
        effectivePendingAuth.mode === "signup"
          ? {
              email: effectivePendingAuth.email,
              name: effectivePendingAuth.name,
              otp: formState.otp,
              password: effectivePendingAuth.password,
            }
          : {
              email: effectivePendingAuth.email,
              otp: formState.otp,
              password: effectivePendingAuth.password,
            };

      const response = await fetch(endpoint, {
        body: JSON.stringify(payload),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });
      const responseBody = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          responseBody?.detail ?? responseBody?.message ?? "OTP verification failed",
        );
      }

      clearPendingAuthRecord();
      router.replace(effectivePendingAuth.redirectTo ?? "/dashboard");
      router.refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "OTP verification failed",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <OtpFormShell
      badge="Step 2 of 2"
      description="Enter the six-digit code from your inbox to finish signing in."
      title="Verify your one-time code"
    >
      <div className="auth-shell__card-header">
        <div>
          <p className="playground-panel__eyebrow">Verification</p>
          <h2>Enter your email code</h2>
        </div>
        <span className="playground-status-chip">Email OTP</span>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="auth-field">
          <span className="dashboard-control-label">One-time code</span>
          <input
            className="dashboard-control-input"
            id="otp-code"
            inputMode="numeric"
            maxLength={6}
            name="otp"
            onChange={(event) =>
              setFormState({
                otp: event.target.value,
              })
            }
            type="text"
            value={formState.otp}
          />
        </label>

        {errorMessage ? (
          <p className="auth-form__message auth-form__message--error">
            {errorMessage}
          </p>
        ) : null}

        <PushButton disabled={isSubmitting} type="submit">
          {isSubmitting ? "Verifying..." : "Verify code"}
        </PushButton>
      </form>

      <p className="auth-form__switch">
        Need a new code? <Link href="/login">Sign in again</Link>
      </p>
    </OtpFormShell>
  );
}

export default function VerifyOtpPage() {
  return (
    <Suspense fallback={null}>
      <VerifyOtpPageContent />
    </Suspense>
  );
}
