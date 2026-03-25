import { NextResponse } from "next/server";
import {
  getPlaygroundEndpoint,
  type PlaygroundEndpointId,
} from "../../../lib/playground-endpoints";
import { getApiBaseUrl, getPlaygroundSecretKey } from "../../../lib/runtime-config";

type PlaygroundRequestBody = {
  endpointId?: PlaygroundEndpointId;
  payload?: unknown;
};

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function buildSearchParams(payload: unknown) {
  const params = new URLSearchParams();

  if (!isPlainObject(payload)) {
    return params;
  }

  for (const [key, value] of Object.entries(payload)) {
    if (value === undefined || value === null) {
      continue;
    }

    if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      params.set(key, String(value));
      continue;
    }

    params.set(key, JSON.stringify(value));
  }

  return params;
}

async function parseBackendResponse(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return {
    status: response.ok,
    message: await response.text(),
  };
}

function buildMockResponse(endpointId: PlaygroundEndpointId, payload: unknown) {
  if (endpointId === "initiate") {
    return {
      status: true,
      message: "Sandbox collection initialized",
      selected_gateway: "fltw",
      checkout_url: "https://sandbox.routex.dev/checkout/abc123",
      gateway_reference: "fltw_demo_abc123",
      request: payload,
    };
  }

  if (endpointId === "verify") {
    return {
      status: true,
      message: "Sandbox verification complete",
      data: {
        reference: "ORD_1001",
        status: "success",
        selected_gateway: "pstk",
        amount: 25000,
        currency: "NGN",
      },
      request: payload,
    };
  }

  return {
    status: true,
    message: "Sandbox payout accepted",
    selected_gateway: "kora",
    gateway_reference: "kora_demo_9001",
    request: payload,
  };
}

export async function POST(request: Request) {
  const body = (await request.json()) as PlaygroundRequestBody;

  if (!body.endpointId) {
    return NextResponse.json(
      { status: false, message: "endpointId is required" },
      { status: 400 },
    );
  }

  const endpoint = getPlaygroundEndpoint(body.endpointId);

  if (!endpoint) {
    return NextResponse.json(
      { status: false, message: "Unsupported sandbox endpoint" },
      { status: 400 },
    );
  }

  const apiBaseUrl = getApiBaseUrl();
  const secretKey = getPlaygroundSecretKey();

  if (apiBaseUrl && secretKey) {
    const targetUrl = new URL(`${apiBaseUrl}${endpoint.path}`);

    if (endpoint.method === "GET") {
      targetUrl.search = buildSearchParams(body.payload).toString();
    }

    try {
      const response = await fetch(targetUrl.toString(), {
        method: endpoint.method,
        headers: {
          Authorization: `Bearer ${secretKey}`,
          ...(endpoint.method === "POST"
            ? { "Content-Type": "application/json" }
            : {}),
        },
        body:
          endpoint.method === "POST"
            ? JSON.stringify(body.payload ?? {})
            : undefined,
        cache: "no-store",
      });

      return NextResponse.json(
        {
          sandbox: true,
          live: true,
          endpoint: endpoint.path,
          method: endpoint.method,
          result: await parseBackendResponse(response),
        },
        { status: response.status },
      );
    } catch {
      // fall through to demo mode if the backend proxy is unavailable
    }
  }

  return NextResponse.json({
    sandbox: true,
    live: false,
    endpoint: endpoint.path,
    method: endpoint.method,
    result: buildMockResponse(body.endpointId, body.payload),
  });
}
