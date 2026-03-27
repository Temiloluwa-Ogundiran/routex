import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { USER_SESSION_COOKIE_NAME } from "../../../../lib/auth-session";
import { getApiBaseUrl } from "../../../../lib/runtime-config";

export async function POST(request: NextRequest) {
  const requestCookies = await cookies();
  const userToken = requestCookies.get(USER_SESSION_COOKIE_NAME)?.value;
  if (!userToken) {
    return NextResponse.json(
      { status: false, message: "Not authenticated" },
      { status: 401 },
    );
  }

  const apiBaseUrl = getApiBaseUrl();
  if (!apiBaseUrl) {
    return NextResponse.json(
      { status: false, message: "RouteX API base URL is not configured." },
      { status: 500 },
    );
  }

  const payload = await request.json();
  const backendResponse = await fetch(`${apiBaseUrl}/links/`, {
    body: JSON.stringify(payload),
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${userToken}`,
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  const responseBody = await backendResponse.json().catch(() => ({
    detail: "Unable to parse backend response",
    status: false,
  }));

  return NextResponse.json(responseBody, { status: backendResponse.status });
}
