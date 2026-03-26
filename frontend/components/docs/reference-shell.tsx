import Link from "next/link";

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

function splitFields(fields: ApiReferenceField[]) {
  return {
    optional: fields.filter((field) => !field.required),
    required: fields.filter((field) => field.required),
  };
}

function FieldList({
  fields,
  title,
}: {
  fields: ApiReferenceField[];
  title: string;
}) {
  if (fields.length === 0) {
    return null;
  }

  return (
    <section className="docs-subsection">
      <div className="docs-subsection__header">
        <h4>{title}</h4>
        <span>{fields.length} field{fields.length === 1 ? "" : "s"}</span>
      </div>
      <div className="docs-field-list">
        {fields.map((field) => (
          <article className="docs-field-card" key={`${field.location}-${field.name}`}>
            <div className="docs-field-card__topline">
              <strong>{field.name}</strong>
              <span className="docs-field-card__type">{field.type}</span>
            </div>
            {field.description ? <p>{field.description}</p> : null}
            {field.example ? (
              <code className="docs-field-card__example">{field.example}</code>
            ) : null}
          </article>
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
        <span>{responses.length} example{responses.length === 1 ? "" : "s"}</span>
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
            {response.description ? <p>{response.description}</p> : null}
            <pre className="docs-code-block">{response.body}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}

function EndpointCard({ endpoint }: { endpoint: ApiReferenceEndpoint }) {
  const requestFields = splitFields(endpoint.requestFields);
  const queryFields = splitFields(endpoint.queryParameters);

  return (
    <article className="docs-endpoint-card" id={endpoint.id}>
      <div className="docs-endpoint-card__hero">
        <div className="docs-endpoint-card__headline">
          <div className="docs-endpoint-card__badges">
            <span className="docs-endpoint__method">{endpoint.method}</span>
            <span className="docs-endpoint__auth">{endpoint.auth}</span>
          </div>
          <h3>{endpoint.title}</h3>
          <div className="docs-endpoint-card__path-row">
            <code>{endpoint.path}</code>
            <CopyButton value={endpoint.path} />
          </div>
        </div>
        <p>{endpoint.description}</p>
      </div>

      <div className="docs-endpoint-card__grid">
        <div className="docs-endpoint-card__stack">
          <FieldList fields={queryFields.required} title="Required query parameters" />
          <FieldList fields={queryFields.optional} title="Optional query parameters" />
          <FieldList fields={requestFields.required} title="Required body fields" />
          <FieldList fields={requestFields.optional} title="Optional body fields" />
        </div>

        <div className="docs-endpoint-card__stack">
          {endpoint.requestExample ? (
            <section className="docs-subsection">
              <div className="docs-subsection__header">
                <h4>Request example</h4>
                <CopyButton value={endpoint.requestExample} />
              </div>
              <pre className="docs-code-block">{endpoint.requestExample}</pre>
            </section>
          ) : null}

          <section className="docs-subsection">
            <div className="docs-subsection__header">
              <h4>cURL</h4>
              <CopyButton value={endpoint.curlExample} />
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
        <h1>RouteX API reference</h1>
        <p>
          Clean request examples for the core merchant endpoints you need to
          collect payments, verify transactions, and trigger payouts in test mode.
        </p>
        <div className="docs-shell__meta">
          <span>Base URL</span>
          <code>{baseUrl ?? "Not configured"}</code>
          {baseUrl ? <CopyButton value={baseUrl} /> : null}
          <span className="playground-status-chip">
            {sourceMode === "live" ? "Test mode" : "Spec unavailable"}
          </span>
        </div>
        <div className="docs-shell__actions">
          <Link className="push-button push-button--primary" href="/sandbox">
            Open sandbox
          </Link>
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
