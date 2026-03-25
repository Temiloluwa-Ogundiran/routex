import { NextRequest, NextResponse } from "next/server";

import {
  ADMIN_SESSION_COOKIE_NAME,
  USER_SESSION_COOKIE_NAME,
} from "./lib/auth-session";

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/admin")) {
    if (pathname === "/admin/login") {
      return NextResponse.next();
    }

    const adminSessionToken = request.cookies.get(ADMIN_SESSION_COOKIE_NAME)?.value;
    if (adminSessionToken) {
      return NextResponse.next();
    }

    const adminLoginUrl = new URL("/admin/login", request.url);
    adminLoginUrl.searchParams.set("next", pathname + request.nextUrl.search);
    return NextResponse.redirect(adminLoginUrl);
  }

  if (!pathname.startsWith("/dashboard")) {
    return NextResponse.next();
  }

  const userSessionToken = request.cookies.get(USER_SESSION_COOKIE_NAME)?.value;
  if (userSessionToken) {
    return NextResponse.next();
  }

  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("next", pathname + request.nextUrl.search);

  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: ["/admin/:path*", "/dashboard/:path*"],
};
