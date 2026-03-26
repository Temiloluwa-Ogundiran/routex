import type { ReactNode } from "react";

type AuthFormShellProps = {
  badge: string;
  children: ReactNode;
  description: string;
  points?: string[];
  title: string;
};

export function AuthFormShell({
  badge,
  children,
  description,
  points,
  title,
}: AuthFormShellProps) {
  return (
    <main className="auth-shell">
      <section className="auth-shell__intro">
        <p className="section-badge">{badge}</p>
        <h1>{title}</h1>
        <p className="auth-shell__copy">{description}</p>
        {points && points.length > 0 ? (
          <ul className="icon-list auth-shell__points">
            {points.map((point) => (
              <li key={point}>
                <span
                  aria-hidden="true"
                  className="icon-list__mark icon-list__mark--solution"
                >
                  +
                </span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="auth-shell__form">
        <div className="playground-panel auth-shell__card">{children}</div>
      </section>
    </main>
  );
}
