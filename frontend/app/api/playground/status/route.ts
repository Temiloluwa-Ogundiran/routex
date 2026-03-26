import { NextResponse } from "next/server";

import { resolvePlaygroundAccess } from "../../../../lib/playground-access";

export async function GET() {
  const access = await resolvePlaygroundAccess();

  return NextResponse.json({
    available: access.available,
    message: access.message,
    statusLabel: access.statusLabel,
  });
}
