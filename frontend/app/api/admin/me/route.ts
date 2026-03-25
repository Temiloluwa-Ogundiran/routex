import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { ADMIN_SESSION_COOKIE_NAME } from "../../../../lib/auth-session";
import { getApiBaseUrl } from "../../../../lib/runtime-config";

export async function GET() {
  const requestCookies = await cookies();
  const adminSessionToken = requestCookies.get(ADMIN_SESSION_COOKIE_NAME)?.value;
  if (!adminSessionToken) {
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

  const backendResponse = await fetch(`${apiBaseUrl}/admin/me`, {
    cache: "no-store",
    headers: {
      Authorization: `Bearer ${adminSessionToken}`,
    },
  });

  const responseBody = await backendResponse.json().catch(() => ({
    message: "Unable to parse backend response",
    status: false,
  }));

  return NextResponse.json(responseBody, { status: backendResponse.status });
}
