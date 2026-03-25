import { NextRequest, NextResponse } from "next/server";

import { ADMIN_SESSION_COOKIE_NAME } from "../../../../../lib/auth-session";
import { getApiBaseUrl } from "../../../../../lib/runtime-config";

export async function POST(request: NextRequest) {
  const adminToken = request.cookies.get(ADMIN_SESSION_COOKIE_NAME)?.value;
  if (!adminToken) {
    return NextResponse.json({ message: "Admin authentication required." }, { status: 401 });
  }

  const apiBaseUrl = getApiBaseUrl();
  if (!apiBaseUrl) {
    return NextResponse.json(
      { message: "RouteX API base URL is not configured." },
      { status: 500 },
    );
  }

  try {
    const response = await fetch(`${apiBaseUrl}/admin/router/refresh-health`, {
      method: "POST",
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${adminToken}`,
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { message: "Unable to refresh gateway health right now." },
        { status: response.status },
      );
    }

    return NextResponse.json({
      dashboard: await response.json(),
      message: "Health refresh complete.",
    });
  } catch {
    return NextResponse.json(
      { message: "Unable to refresh gateway health right now." },
      { status: 502 },
    );
  }
}
