import type {
  ApiReferenceEndpoint,
  ApiReferenceField,
  ApiReferenceGroup,
  ApiReferenceResponse,
} from "../../lib/openapi";
import { CopyButton } from "../ui/copy-button";
import { SectionBadge } from "../ui/section-badge";

type ReferenceShellProps = {
  baseUrl: string | null;
  groups: ApiReferenceGroup[];
  sourceMode: "live" | "unavailable";
  unavailableReason: string | null;
};

function FieldTable({
  title,
  fields,
}: {
  title: string;
  fields: ApiReferenceField[];
}) {
  if (fields.length === 0) {
    return null;
  }

  return (
    <section className="docs-subsection">
      <div className="docs-subsection__header">
        <h4>{title}</h4>
        <span>{fields.length} fields</span>
      </div>
      <div className="docs-table-shell">
        <div className="docs-table docs-table--header">
          <span>Field</span>
          <span>Type</span>
          <span>Required</span>
          <span>Notes</span>
        </div>
        {fields.map((field) => (
          <div className="docs-table" key={`${field.location}-${field.name}`}>
            <span className="docs-table__field">{field.name}</span>
            <span>{field.type}</span>
            <span>{field.required ? "Yes" : "No"}</span>
            <span>{field.description}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

function ResponseCards({ responses }: { responses: ApiReferenceResponse[] }) {
  return (
    <section className="docs-subsection">
      <div className="docs-subsection__header">
        <h4>Responses</h4>
        <span>{responses.length} variants</span>
      </div>
      <div className="docs-response-grid">
        {responses.map((response) => (
          <article className="docs-response-card" key={`${response.statusCode}-${response.title}`}>
            <div className="docs-response-card__header">
              <div className="docs-response-card__badge-group">
                <span className="docs-endpoint__method">HTTP {response.statusCode}</span>
                <strong>{response.title}</strong>
              </div>
              <CopyButton value={response.body} />
            </div>
            <p>{response.description}</p>
            <pre className="docs-code-block">{response.body}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}

function EndpointCard({ endpoint }: { endpoint: ApiReferenceEndpoint }) {
  return (
    <article className="docs-endpoint-card" id={endpoint.id}>
      <div className="docs-endpoint-card__hero">
        <div className="docs-endpoint-card__headline">
          <div className="docs-endpoint-card__badges">
            <span className="docs-endpoint__method">{endpoint.method}</span>
            <span className="docs-endpoint__auth">{endpoint.auth}</span>
          </div>
          <h3>{endpoint.title}</h3>
          <code>{endpoint.path}</code>
        </div>
        <p>{endpoint.description}</p>
      </div>

      <div className="docs-endpoint-card__grid">
        <div className="docs-endpoint-card__stack">
          <FieldTable title="Query parameters" fields={endpoint.queryParameters} />
          <FieldTable title="Request body" fields={endpoint.requestFields} />

          {endpoint.requestExample ? (
            <section className="docs-subsection">
              <div className="docs-subsection__header">
                <h4>Request payload</h4>
                <div className="docs-subsection__actions">
                  <span>JSON</span>
                  <CopyButton value={endpoint.requestExample} />
                </div>
              </div>
              <pre className="docs-code-block">{endpoint.requestExample}</pre>
            </section>
          ) : null}
        </div>

        <div className="docs-endpoint-card__stack">
          <section className="docs-subsection">
            <div className="docs-subsection__header">
              <h4>cURL</h4>
              <div className="docs-subsection__actions">
                <span>Ready to copy</span>
                <CopyButton value={endpoint.curlExample} />
              </div>
            </div>
            <pre className="docs-code-block">{endpoint.curlExample}</pre>
          </section>

          <ResponseCards responses={endpoint.responses} />
        </div>
      </div>
    </article>
  );
}

export function ReferenceShell({
  baseUrl,
  groups,
  sourceMode,
  unavailableReason,
}: ReferenceShellProps) {
  return (
    <section className="docs-shell">
      <div className="docs-shell__hero">
        <SectionBadge>API Reference</SectionBadge>
        <h1>Build on RouteX with three core merchant endpoints.</h1>
        <p>
          Use the public RouteX test-mode endpoints with concise payload examples,
          copy-ready requests, and normalized response samples.
        </p>
        <div className="docs-shell__meta">
          <span>Base URL</span>
          <code>{baseUrl ?? "Not configured"}</code>
          <span className="playground-status-chip">
            {sourceMode === "live" ? "Test mode" : "Spec unavailable"}
          </span>
        </div>
      </div>

      {sourceMode !== "live" ? (
        <section className="docs-unavailable">
          <h2>Public API reference unavailable</h2>
          <p>{unavailableReason}</p>
        </section>
      ) : (
        groups.map((group) => (
          <section className="docs-group" key={group.title}>
            <div className="docs-group__header">
              <p className="docs-card__eyebrow">{group.title}</p>
              <h2>{group.description}</h2>
              <p className="docs-group__copy">
                Clean request shapes on the left, copyable request and response examples on the right.
              </p>
            </div>
            <div className="docs-group__stack">
              {group.endpoints.map((endpoint) => (
                <EndpointCard endpoint={endpoint} key={endpoint.id} />
              ))}
            </div>
          </section>
        ))
      )}
    </section>
  );
}
