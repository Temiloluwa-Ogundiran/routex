import { NextResponse } from "next/server";

import {
  USER_SESSION_COOKIE_NAME,
  createClearedUserSessionCookieOptions,
} from "../../../../lib/auth-session";

export async function POST() {
  const response = NextResponse.json({
    message: "Logged out successfully",
    status: true,
  });

  response.cookies.set(
    USER_SESSION_COOKIE_NAME,
    "",
    createClearedUserSessionCookieOptions(),
  );

  return response;
}
