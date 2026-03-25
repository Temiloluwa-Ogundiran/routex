import { NextRequest, NextResponse } from "next/server";

import { ADMIN_SESSION_COOKIE_NAME } from "../../../../../lib/auth-session";
import {
  type RouterRuleCreatePayload,
} from "../../../../../lib/dashboard-api";
import { getApiBaseUrl } from "../../../../../lib/runtime-config";

function validateCreatePayload(payload: Partial<RouterRuleCreatePayload>) {
  if (!payload.name?.trim()) {
    return "Rule name is required.";
  }

  if (!payload.operation?.trim()) {
    return "Operation is required.";
  }

  if (
    payload.min_amount !== undefined &&
    payload.min_amount !== null &&
    !Number.isFinite(payload.min_amount)
  ) {
    return "Minimum amount must be a valid number.";
  }

  if (
    payload.max_amount !== undefined &&
    payload.max_amount !== null &&
    !Number.isFinite(payload.max_amount)
  ) {
    return "Maximum amount must be a valid number.";
  }

  if (
    payload.min_amount !== undefined &&
    payload.max_amount !== undefined &&
    payload.min_amount !== null &&
    payload.max_amount !== null &&
    payload.min_amount > payload.max_amount
  ) {
    return "Minimum amount cannot be greater than maximum amount.";
  }

  return null;
}

async function readErrorPayload(response: Response) {
  const fallback = { detail: "Unable to process routing rules right now." };
  return response.json().catch(() => fallback);
}

export async function GET(request: NextRequest) {
  const adminToken = request.cookies.get(ADMIN_SESSION_COOKIE_NAME)?.value;
  if (!adminToken) {
    return NextResponse.json({ detail: "Admin authentication required." }, { status: 401 });
  }

  const apiBaseUrl = getApiBaseUrl();
  if (!apiBaseUrl) {
    return NextResponse.json(
      { detail: "RouteX API base URL is not configured." },
      { status: 500 },
    );
  }

  try {
    const response = await fetch(`${apiBaseUrl}/admin/router/rules`, {
      headers: {
        Authorization: `Bearer ${adminToken}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      return NextResponse.json(await readErrorPayload(response), {
        status: response.status,
      });
    }

    return NextResponse.json(await response.json());
  } catch {
    return NextResponse.json(
      { detail: "Unable to process routing rules right now." },
      { status: 502 },
    );
  }
}

export async function POST(request: NextRequest) {
  const adminToken = request.cookies.get(ADMIN_SESSION_COOKIE_NAME)?.value;
  if (!adminToken) {
    return NextResponse.json({ detail: "Admin authentication required." }, { status: 401 });
  }

  const payload = (await request.json()) as Partial<RouterRuleCreatePayload>;
  const validationMessage = validateCreatePayload(payload);

  if (validationMessage) {
    return NextResponse.json({ detail: validationMessage }, { status: 400 });
  }

  const apiBaseUrl = getApiBaseUrl();
  if (!apiBaseUrl) {
    return NextResponse.json(
      { detail: "RouteX API base URL is not configured." },
      { status: 500 },
    );
  }

  try {
    const response = await fetch(`${apiBaseUrl}/admin/router/rules`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${adminToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    if (!response.ok) {
      return NextResponse.json(await readErrorPayload(response), {
        status: response.status,
      });
    }

    return NextResponse.json({
      rule: await response.json(),
    });
  } catch {
    return NextResponse.json(
      { detail: "Unable to process routing rules right now." },
      { status: 502 },
    );
  }
}
