import { NextRequest, NextResponse } from "next/server";

import {
  ADMIN_SESSION_COOKIE_NAME,
  USER_SESSION_COOKIE_NAME,
} from "./lib/auth-session";

function buildNextTarget(pathname: string, search: string) {
  return `${pathname}${search}`;
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const userSessionToken = request.cookies.get(USER_SESSION_COOKIE_NAME)?.value;
  const adminSessionToken = request.cookies.get(ADMIN_SESSION_COOKIE_NAME)?.value;

  if (pathname.startsWith("/admin")) {
    if (pathname === "/admin/login") {
      if (adminSessionToken) {
        const adminUrl = new URL("/admin", request.url);
        return NextResponse.redirect(adminUrl);
      }
      return NextResponse.next();
    }

    if (adminSessionToken) {
      return NextResponse.next();
    }

    const adminLoginUrl = new URL("/admin/login", request.url);
    adminLoginUrl.searchParams.set(
      "next",
      buildNextTarget(pathname, request.nextUrl.search),
    );
    return NextResponse.redirect(adminLoginUrl);
  }

  if (
    pathname === "/login" ||
    pathname === "/signup" ||
    pathname === "/verify-otp"
  ) {
    if (!userSessionToken) {
      return NextResponse.next();
    }

    const nextTarget = request.nextUrl.searchParams.get("next");
    const destination =
      nextTarget && nextTarget.startsWith("/") ? nextTarget : "/dashboard";
    return NextResponse.redirect(new URL(destination, request.url));
  }

  if (!pathname.startsWith("/dashboard")) {
    return NextResponse.next();
  }

  if (userSessionToken) {
    return NextResponse.next();
  }

  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set(
    "next",
    buildNextTarget(pathname, request.nextUrl.search),
  );

  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    "/admin/:path*",
    "/dashboard/:path*",
    "/login",
    "/signup",
    "/verify-otp",
  ],
};
