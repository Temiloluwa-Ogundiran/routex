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
    <main className="auth-shell auth-shell--otp">
      <section className="auth-shell__intro">
        <div className="auth-shell__intro-copy">
          <span className="auth-shell__eyebrow">{badge}</span>
          <h1>{title}</h1>
          <span aria-hidden="true" className="auth-shell__underline" />
          <p className="auth-shell__copy">{description}</p>
        </div>
      </section>

      <section className="auth-shell__form">
        <div className="auth-shell__card">{children}</div>
      </section>
    </main>
  );
}
