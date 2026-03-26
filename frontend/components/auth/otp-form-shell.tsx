import type { ReactNode } from "react";

type OtpFormShellProps = {
  badge: string;
  children: ReactNode;
  description: string;
  title: string;
};

export function OtpFormShell({
  badge,
  children,
  description,
  title,
}: OtpFormShellProps) {
  return (
    <main className="auth-shell auth-shell--otp liquid-auth-shell">
      <section className="auth-shell__intro">
        <span className="auth-shell__eyebrow">{badge}</span>
        <h1>{title}</h1>
        <p className="auth-shell__copy">{description}</p>
      </section>

      <section className="auth-shell__form">
        <div className="auth-shell__card">{children}</div>
      </section>
    </main>
  );
}
