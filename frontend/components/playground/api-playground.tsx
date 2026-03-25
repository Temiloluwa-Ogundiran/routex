"use client";

import { useState, useTransition } from "react";
import {
  getPlaygroundEndpoint,
  PLAYGROUND_ENDPOINTS,
  type PlaygroundEndpointId,
} from "../../lib/playground-endpoints";
import { PushButton } from "../ui/push-button";
import { SectionBadge } from "../ui/section-badge";
import { RequestPanel } from "./request-panel";
import { ResponsePanel } from "./response-panel";

function formatJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

type ApiPlaygroundProps = {
  mode: "live" | "demo";
};

export function ApiPlayground({ mode }: ApiPlaygroundProps) {
  const [selectedId, setSelectedId] = useState<PlaygroundEndpointId>("initiate");
  const [requestBody, setRequestBody] = useState(
    formatJson(getPlaygroundEndpoint("initiate")?.requestTemplate ?? {}),
  );
  const [responseBody, setResponseBody] = useState(
    formatJson({
      status: "ready",
      message: "Choose an endpoint and send a sandbox request.",
    }),
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const selectedEndpoint = getPlaygroundEndpoint(selectedId);

  function handleEndpointChange(nextId: PlaygroundEndpointId) {
    const endpoint = getPlaygroundEndpoint(nextId);
    setSelectedId(nextId);
    setRequestBody(formatJson(endpoint?.requestTemplate ?? {}));
    setErrorMessage(null);
  }

  function handleSubmit() {
    let parsedBody: unknown;

    try {
      parsedBody = JSON.parse(requestBody);
      setErrorMessage(null);
    } catch {
      setErrorMessage("Request payload must be valid JSON.");
      return;
    }

    startTransition(() => {
      void submitRequest(parsedBody);
    });
  }

  async function submitRequest(parsedBody: unknown) {
    const response = await fetch("/api/playground", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        endpointId: selectedId,
        payload: parsedBody,
      }),
    });

    const json = await response.json();
    setResponseBody(formatJson(json));
  }

  if (!selectedEndpoint) {
    return null;
  }

  return (
    <section className="story-section story-section--playground" id="quickstart">
      <div className="section-heading section-heading--split">
        <div>
          <SectionBadge>Sandbox Console</SectionBadge>
          <h2>Test the API without leaving the landing page.</h2>
          <p>
            Try collections, verification, and payouts with prefilled payloads.
            When sandbox credentials are configured, requests proxy to the
            routed backend; otherwise the branded demo stub stays available.
          </p>
        </div>
        <a className="inline-link" href="/docs">
          Open full API reference
        </a>
      </div>

      <div className="playground-shell">
        <div className="playground-tabs" role="tablist" aria-label="Playground endpoints">
          {PLAYGROUND_ENDPOINTS.map((endpoint) => (
            <button
              aria-selected={endpoint.id === selectedId}
              className={`playground-tab ${
                endpoint.id === selectedId ? "playground-tab--active" : ""
              }`}
              key={endpoint.id}
              onClick={() => handleEndpointChange(endpoint.id)}
              role="tab"
              type="button"
            >
              {endpoint.label}
            </button>
          ))}
        </div>

        <div className="playground-grid">
          <RequestPanel
            body={requestBody}
            description={selectedEndpoint.description}
            endpoint={selectedEndpoint.path}
            method={selectedEndpoint.method}
            statusLabel={mode === "live" ? "Live sandbox" : "Sandbox only"}
            onBodyChange={setRequestBody}
          />
          <ResponsePanel isPending={isPending} responseBody={responseBody} />
        </div>

        <div className="playground-actions">
          <PushButton
            className="playground-send-button"
            disabled={isPending}
            onClick={handleSubmit}
            type="button"
          >
            Send Request
          </PushButton>
        </div>

        {errorMessage ? <p className="playground-error">{errorMessage}</p> : null}
      </div>
    </section>
  );
}
