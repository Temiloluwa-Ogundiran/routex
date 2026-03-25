import { NextRequest, NextResponse } from "next/server";

import { ADMIN_SESSION_COOKIE_NAME } from "../../../../lib/auth-session";
import { getApiBaseUrl } from "../../../../lib/runtime-config";

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
    const response = await fetch(`${apiBaseUrl}/analytics/router/dashboard`, {
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${adminToken}`,
      },
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({
        detail: "Unable to load admin router dashboard right now.",
      }));
      return NextResponse.json(payload, { status: response.status });
    }

    return NextResponse.json(await response.json());
  } catch {
    return NextResponse.json(
      { detail: "Unable to load admin router dashboard right now." },
      { status: 502 },
    );
  }
}
