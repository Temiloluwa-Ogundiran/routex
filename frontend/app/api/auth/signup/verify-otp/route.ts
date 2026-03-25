import { NextRequest, NextResponse } from "next/server";

import {
  USER_SESSION_COOKIE_NAME,
  createUserSessionCookieOptions,
} from "../../../../../lib/auth-session";
import { getApiBaseUrl } from "../../../../../lib/runtime-config";

export async function POST(request: NextRequest) {
  const apiBaseUrl = getApiBaseUrl();
  if (!apiBaseUrl) {
    return NextResponse.json(
      { status: false, message: "RouteX API base URL is not configured." },
      { status: 500 },
    );
  }

  const payload = await request.json();
  const backendResponse = await fetch(`${apiBaseUrl}/auth/signup/verify-otp`, {
    body: JSON.stringify(payload),
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  const responseBody = await backendResponse.json().catch(() => ({
    message: "Unable to parse backend response",
    status: false,
  }));

  const response = NextResponse.json(responseBody, {
    status: backendResponse.status,
  });

  if (backendResponse.ok && responseBody?.access_token) {
    response.cookies.set(
      USER_SESSION_COOKIE_NAME,
      String(responseBody.access_token),
      createUserSessionCookieOptions(),
    );
  }

  return response;
}
