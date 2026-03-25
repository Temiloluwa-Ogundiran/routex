import { NextRequest, NextResponse } from "next/server";

import { getApiBaseUrl } from "../../../../lib/runtime-config";

export async function POST(request: NextRequest) {
  const apiBaseUrl = getApiBaseUrl();
  if (!apiBaseUrl) {
    return NextResponse.json(
      { status: false, message: "RouteX API base URL is not configured." },
      { status: 500 },
    );
  }

  const payload = await request.json();
  const backendResponse = await fetch(`${apiBaseUrl}/auth/forgot-password`, {
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

  return NextResponse.json(responseBody, { status: backendResponse.status });
}
