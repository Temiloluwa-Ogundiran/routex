import { NextRequest, NextResponse } from "next/server";
import { cookies } from "next/headers";

import {
  PENDING_AUTH_COOKIE_NAME,
  USER_SESSION_COOKIE_NAME,
  createClearedPendingAuthCookieOptions,
  createUserSessionCookieOptions,
  decodePendingAuthRecord,
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

  const requestCookies = await cookies();
  const pendingAuth = decodePendingAuthRecord(
    requestCookies.get(PENDING_AUTH_COOKIE_NAME)?.value,
  );

  if (!pendingAuth || pendingAuth.mode !== "signup") {
    return NextResponse.json(
      { status: false, message: "Your sign-up code has expired. Start again." },
      { status: 400 },
    );
  }

  const payload = await request.json();
  const backendResponse = await fetch(`${apiBaseUrl}/auth/signup/verify-otp`, {
    body: JSON.stringify({
      email: pendingAuth.email,
      name: pendingAuth.name,
      otp: payload.otp,
      password: pendingAuth.password,
    }),
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
    response.cookies.set(
      PENDING_AUTH_COOKIE_NAME,
      "",
      createClearedPendingAuthCookieOptions(),
    );
  }

  return response;
}
