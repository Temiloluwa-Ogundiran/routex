"use client";

import Link from "next/link";
import { useState } from "react";

import { AuthFormShell } from "../../components/auth/auth-form-shell";
import { PushButton } from "../../components/ui/push-button";

type ForgotPasswordFormState = {
  email: string;
};

export default function ForgotPasswordPage() {
  const [formState, setFormState] = useState<ForgotPasswordFormState>({
    email: "",
  });
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setStatusMessage(null);
    setErrorMessage(null);

    try {
      const response = await fetch("/api/auth/forgot-password", {
        body: JSON.stringify(formState),
        headers: {
          "Content-Type": "application/json",
        },
        method: "POST",
      });
      const responseBody = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          responseBody?.detail ?? responseBody?.message ?? "Unable to send reset link",
        );
      }

      setStatusMessage("Check your inbox for the password reset link.");
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to send reset link",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthFormShell
      badge="Password help"
      description="Request a password reset email and continue back into RouteX with the same design language as the rest of the app."
      points={[
        "Reset links are delivered by the backend email provider",
        "The page stays public and safe to share",
        "No OTP or token is shown in the response body",
      ]}
      title="Recover your RouteX account"
    >
      <div className="auth-shell__card-header">
        <div>
          <p className="playground-panel__eyebrow">Recovery</p>
          <h2>Request a reset link</h2>
        </div>
        <span className="playground-status-chip">Public flow</span>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        <label className="auth-field">
          <span className="dashboard-control-label">Email</span>
          <input
            className="dashboard-control-input"
            id="forgot-email"
            name="email"
            onChange={(event) =>
              setFormState({
                email: event.target.value,
              })
            }
            type="email"
            value={formState.email}
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
          {isSubmitting ? "Sending..." : "Send reset link"}
        </PushButton>
      </form>

      <p className="auth-form__switch">
        Remembered it? <Link href="/login">Back to sign in</Link>
      </p>
    </AuthFormShell>
  );
}
