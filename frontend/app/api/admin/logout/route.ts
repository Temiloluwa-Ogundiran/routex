import { NextResponse } from "next/server";

import {
  ADMIN_SESSION_COOKIE_NAME,
  createClearedAdminSessionCookieOptions,
} from "../../../../lib/auth-session";

export async function POST() {
  const response = NextResponse.json({
    message: "Logged out successfully",
    status: true,
  });

  response.cookies.set(
    ADMIN_SESSION_COOKIE_NAME,
    "",
    createClearedAdminSessionCookieOptions(),
  );

  return response;
}
