"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { AuthFormShell } from "../../components/auth/auth-form-shell";
import { PushButton } from "../../components/ui/push-button";

type ResetPasswordFormState = {
  email: string;
  newPassword: string;
  resetCode: string;
};

function ResetPasswordPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [formState, setFormState] = useState<ResetPasswordFormState>({
    email: "",
    newPassword: "",
    resetCode: "",
  });
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    setFormState((currentState) => ({
      ...currentState,
      email: searchParams.get("email") ?? currentState.email,
      resetCode: searchParams.get("code") ?? currentState.resetCode,
    }));
  }, [searchParams]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setStatusMessage(null);
    setErrorMessage(null);

    try {
      const response = await fetch("/api/auth/reset-password", {
        body: JSON.stringify({
          email: formState.email,
          new_password: formState.newPassword,
          token: formState.resetCode,
        }),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });
      const responseBody = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          responseBody?.detail ??
            responseBody?.message ??
            "Unable to reset password",
        );
      }

      setStatusMessage("Password updated. Redirecting you to the dashboard.");
      router.replace("/dashboard");
      router.refresh();
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to reset password",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthFormShell
      badge="Reset password"
      description="Drop in the reset link details and lock your workspace back in."
      points={[
        "Use the email and reset code from your inbox, then set a fresh password.",
      ]}
      title="Choose a new password"
    >
      <div className="auth-shell__card-header">
        <div>
          <p className="playground-panel__eyebrow">Secure reset</p>
          <h2>Update your password</h2>
        </div>
        <span className="playground-status-chip">Email link</span>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="auth-field">
          <span className="dashboard-control-label">Email</span>
          <input
            className="dashboard-control-input"
            id="reset-email"
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
          <span className="dashboard-control-label">Reset code</span>
          <input
            className="dashboard-control-input"
            id="reset-code"
            name="token"
            onChange={(event) =>
              setFormState((currentState) => ({
                ...currentState,
                resetCode: event.target.value,
              }))
            }
            type="text"
            value={formState.resetCode}
          />
        </label>

        <label className="auth-field">
          <span className="dashboard-control-label">New password</span>
          <input
            className="dashboard-control-input"
            id="reset-password"
            name="new_password"
            onChange={(event) =>
              setFormState((currentState) => ({
                ...currentState,
                newPassword: event.target.value,
              }))
            }
            type="password"
            value={formState.newPassword}
          />
        </label>

        {statusMessage ? (
          <p className="auth-form__message auth-form__message--success">
            {statusMessage}
          </p>
        ) : null}
        {errorMessage ? (
          <p className="auth-form__message auth-form__message--error">
            {errorMessage}
          </p>
        ) : null}

        <PushButton disabled={isSubmitting} type="submit">
          {isSubmitting ? "Updating..." : "Update password"}
        </PushButton>
      </form>

      <p className="auth-form__switch">
        <Link href="/login">Back to sign in</Link>
      </p>
    </AuthFormShell>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetPasswordPageContent />
    </Suspense>
  );
}
