"use client";

import { useEffect, useState, useTransition } from "react";
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

type PlaygroundAvailability = {
  available: boolean;
  message: string;
  statusLabel: string;
};

function buildReadyMessage(isLive: boolean) {
  if (isLive) {
    return {
      status: "ready",
      message: "Choose an endpoint and send a real sandbox request.",
    };
  }

  return {
    status: "unavailable",
    message:
      "Sign in with a merchant account or add a workspace test key to unlock live sandbox requests.",
  };
}

const INITIAL_AVAILABILITY: PlaygroundAvailability = {
  available: false,
  message: "Checking sandbox access for this session.",
  statusLabel: "Checking access",
};

export function ApiPlayground() {
  const [selectedId, setSelectedId] = useState<PlaygroundEndpointId>("initiate");
  const [requestBody, setRequestBody] = useState(
    formatJson(getPlaygroundEndpoint("initiate")?.requestTemplate ?? {}),
  );
  const [availability, setAvailability] = useState<PlaygroundAvailability>(
    INITIAL_AVAILABILITY,
  );
  const [responseBody, setResponseBody] = useState(
    formatJson(buildReadyMessage(false)),
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const selectedEndpoint = getPlaygroundEndpoint(selectedId);
  const isLive = availability.available;

  useEffect(() => {
    let cancelled = false;

    async function loadAvailability() {
      const response = await fetch("/api/playground/status", {
        cache: "no-store",
        credentials: "same-origin",
      }).catch(() => null);

      if (!response) {
        if (!cancelled) {
          setAvailability({
            available: false,
            message: "We could not confirm sandbox access right now.",
            statusLabel: "Connection issue",
          });
          setResponseBody(formatJson(buildReadyMessage(false)));
        }
        return;
      }

      const payload = (await response.json().catch(() => null)) as PlaygroundAvailability | null;
      if (cancelled || !payload) {
        return;
      }

      setAvailability(payload);
      setResponseBody(formatJson(buildReadyMessage(payload.available)));
    }

    void loadAvailability();

    return () => {
      cancelled = true;
    };
  }, []);

  function handleEndpointChange(nextId: PlaygroundEndpointId) {
    const endpoint = getPlaygroundEndpoint(nextId);
    setSelectedId(nextId);
    setRequestBody(formatJson(endpoint?.requestTemplate ?? {}));
    setResponseBody(formatJson(buildReadyMessage(isLive)));
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
      const backendMessage =
        typeof json.message === "string"
          ? json.message
          : typeof json.result?.detail === "string"
            ? json.result.detail
            : typeof json.result?.message === "string"
              ? json.result.message
              : "Sandbox request failed.";
      setErrorMessage(
        backendMessage,
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
          <h2>Run real test-mode requests.</h2>
          <p>
            Use your merchant test key to initialize collections, verify
            transactions, and test payouts against the live RouteX sandbox.
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
            statusLabel={availability.statusLabel}
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

        <p className="playground-hint">{availability.message}</p>

        {errorMessage ? <p className="playground-error">{errorMessage}</p> : null}
      </div>
    </section>
  );
}
