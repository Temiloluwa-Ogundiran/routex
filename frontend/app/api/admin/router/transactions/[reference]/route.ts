import { NextRequest, NextResponse } from "next/server";

import { ADMIN_SESSION_COOKIE_NAME } from "../../../../../../lib/auth-session";
import { getApiBaseUrl } from "../../../../../../lib/runtime-config";

type RouteContext = {
  params: Promise<{
    reference: string;
  }>;
};

export async function GET(request: NextRequest, { params }: RouteContext) {
  const adminToken = request.cookies.get(ADMIN_SESSION_COOKIE_NAME)?.value;
  if (!adminToken) {
    return NextResponse.json({ detail: "Admin authentication required." }, { status: 401 });
  }

  const createdAt = request.nextUrl.searchParams.get("created_at");
  const { reference } = await params;
  const apiBaseUrl = getApiBaseUrl();

  if (!apiBaseUrl) {
    return NextResponse.json(
      { detail: "RouteX API base URL is not configured." },
      { status: 500 },
    );
  }

  try {
    const detailUrl = new URL(
      `/analytics/router/transactions/${encodeURIComponent(reference)}`,
      apiBaseUrl,
    );

    if (createdAt) {
      detailUrl.searchParams.set("created_at", createdAt);
    }

    const response = await fetch(detailUrl.toString(), {
      headers: {
        Authorization: `Bearer ${adminToken}`,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({
        detail: "Unable to load transaction detail right now.",
      }));
      return NextResponse.json(body, { status: response.status });
    }

    return NextResponse.json(await response.json());
  } catch {
    return NextResponse.json(
      { detail: "Unable to load transaction detail right now." },
      { status: 502 },
    );
  }
}
