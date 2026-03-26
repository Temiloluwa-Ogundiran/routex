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
  mode: "live" | "disabled";
};

function buildReadyMessage(mode: ApiPlaygroundProps["mode"]) {
  if (mode === "live") {
    return {
      status: "ready",
      message: "Choose an endpoint and send a real sandbox request.",
    };
  }

  return {
    status: "unavailable",
    message:
      "Sandbox access will appear here as soon as this deployment is fully connected.",
  };
}

export function ApiPlayground({ mode }: ApiPlaygroundProps) {
  const [selectedId, setSelectedId] = useState<PlaygroundEndpointId>("initiate");
  const [requestBody, setRequestBody] = useState(
    formatJson(getPlaygroundEndpoint("initiate")?.requestTemplate ?? {}),
  );
  const [responseBody, setResponseBody] = useState(
    formatJson(buildReadyMessage(mode)),
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const selectedEndpoint = getPlaygroundEndpoint(selectedId);
  const isLive = mode === "live";

  function handleEndpointChange(nextId: PlaygroundEndpointId) {
    const endpoint = getPlaygroundEndpoint(nextId);
    setSelectedId(nextId);
    setRequestBody(formatJson(endpoint?.requestTemplate ?? {}));
    setResponseBody(formatJson(buildReadyMessage(mode)));
    setErrorMessage(null);
  }

  function handleSubmit() {
    if (!isLive) {
      setErrorMessage(
        "Sandbox access is not available yet on this deployment.",
      );
      return;
    }

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

    if (!response.ok) {
      setErrorMessage(
        typeof json.message === "string"
          ? json.message
          : "Sandbox request failed.",
      );
      return;
    }

    setErrorMessage(null);
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
            Inspect the real request payloads for collections, verification, and
            payouts. When sandbox access is ready, requests run against the live
            test environment. Until then, the console stays read-only.
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
            statusLabel={isLive ? "Live sandbox" : "Sandbox unavailable"}
            onBodyChange={setRequestBody}
          />
          <ResponsePanel
            isAvailable={isLive}
            isPending={isPending}
            responseBody={responseBody}
          />
        </div>

        <div className="playground-actions">
          <PushButton
            className="playground-send-button"
            disabled={isPending || !isLive}
            onClick={handleSubmit}
            type="button"
          >
            {isLive ? "Send Request" : "Sandbox Unavailable"}
          </PushButton>
        </div>

        {!isLive ? (
          <p className="playground-hint">
            Sandbox requests are temporarily unavailable on this deployment.
          </p>
        ) : null}

        {errorMessage ? <p className="playground-error">{errorMessage}</p> : null}
      </div>
    </section>
  );
}
