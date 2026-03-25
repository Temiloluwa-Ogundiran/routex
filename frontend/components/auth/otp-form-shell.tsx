import type { ReactNode } from "react";

type OtpFormShellProps = {
  badge: string;
  children: ReactNode;
  description: string;
  pendingEmail?: string | null;
  title: string;
};

export function OtpFormShell({
  badge,
  children,
  description,
  pendingEmail,
  title,
}: OtpFormShellProps) {
  return (
    <main className="auth-shell auth-shell--otp">
      <section className="auth-shell__intro">
        <p className="section-badge">{badge}</p>
        <h1>{title}</h1>
        <p className="auth-shell__copy">{description}</p>

        <div className="auth-shell__summary">
          <p className="auth-shell__summary-label">Verification target</p>
          <strong>{pendingEmail ?? "No pending session found yet"}</strong>
          <p className="auth-shell__summary-copy">
            Use the same inbox that received the login or signup OTP. The
            pending session is stored locally until verification completes.
          </p>
        </div>
      </section>

      <section className="auth-shell__form">
        <div className="playground-panel auth-shell__card">{children}</div>
      </section>
    </main>
  );
}
