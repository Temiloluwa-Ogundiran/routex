import { NextRequest, NextResponse } from "next/server";

import { ADMIN_SESSION_COOKIE_NAME } from "../../../../../../lib/auth-session";
import { getApiBaseUrl } from "../../../../../../lib/runtime-config";

type GatewayUpdateRequest = {
  gateway_name?: string;
  is_active?: boolean;
  priority_weight?: number;
  supports_collections?: boolean;
  supports_payouts?: boolean;
};

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ gatewayCode: string }> },
) {
  const adminToken = request.cookies.get(ADMIN_SESSION_COOKIE_NAME)?.value;
  if (!adminToken) {
    return NextResponse.json({ message: "Admin authentication required." }, { status: 401 });
  }

  const { gatewayCode } = await context.params;
  const body = (await request.json()) as GatewayUpdateRequest;

  if (body.is_active === undefined && body.priority_weight === undefined) {
    return NextResponse.json(
      { message: "Provide is_active or priority_weight to update a gateway." },
      { status: 400 },
    );
  }

  if (
    body.priority_weight !== undefined &&
    (!Number.isFinite(body.priority_weight) || body.priority_weight < 0)
  ) {
    return NextResponse.json(
      { message: "priority_weight must be a non-negative number." },
      { status: 400 },
    );
  }

  const apiBaseUrl = getApiBaseUrl();
  if (!apiBaseUrl) {
    return NextResponse.json(
      { message: "RouteX API base URL is not configured." },
      { status: 500 },
    );
  }

  try {
    const response = await fetch(
      `${apiBaseUrl}/admin/router/gateways/${gatewayCode}`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${adminToken}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          is_active: body.is_active,
          priority_weight: body.priority_weight,
        }),
        cache: "no-store",
      },
    );

    const payload = await response.json().catch(() => ({
      message: "Unable to reach the backend admin router.",
    }));

    if (!response.ok) {
      return NextResponse.json(payload, { status: response.status });
    }

    return NextResponse.json({
      gateway: payload,
    });
  } catch {
    return NextResponse.json(
      { message: "Unable to reach the backend admin router." },
      { status: 502 },
    );
  }
}
