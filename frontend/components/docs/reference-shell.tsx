import type { ApiReferenceGroup } from "../../lib/openapi";
import { SectionBadge } from "../ui/section-badge";

type ReferenceShellProps = {
  groups: ApiReferenceGroup[];
  sourceLabel: string;
  sourceMode: "live" | "fallback";
};

export function ReferenceShell({
  groups,
  sourceLabel,
  sourceMode,
}: ReferenceShellProps) {
  return (
    <section className="docs-shell">
      <div className="docs-shell__hero">
        <SectionBadge>API Reference</SectionBadge>
        <h1>Build once. Route across every supported gateway.</h1>
        <p>
          The docs shell mirrors the RouteX brand and builds from the sanitized
          public OpenAPI export whenever the backend is available.
        </p>
        <div className="docs-shell__meta">
          <span>OpenAPI source</span>
          <code>{sourceLabel}</code>
          <span className="playground-status-chip">
            {sourceMode === "live" ? "Live spec" : "Fallback catalog"}
          </span>
        </div>
      </div>

      <div className="docs-shell__grid">
        {groups.map((group) => (
          <section className="docs-card" key={group.title}>
            <p className="docs-card__eyebrow">{group.title}</p>
            <p className="docs-card__copy">{group.description}</p>
            <div className="docs-card__list">
              {group.endpoints.map((endpoint) => (
                <article className="docs-endpoint" key={endpoint.id}>
                  <div className="docs-endpoint__method">{endpoint.method}</div>
                  <div>
                    <strong>{endpoint.path}</strong>
                    <p>{endpoint.description}</p>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}
