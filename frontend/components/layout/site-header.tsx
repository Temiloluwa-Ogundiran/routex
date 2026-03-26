import { cookies } from "next/headers";

import { ADMIN_SESSION_COOKIE_NAME, USER_SESSION_COOKIE_NAME } from "../../lib/auth-session";
import { SiteHeaderClient } from "./site-header-client";

export async function SiteHeader() {
  const requestCookies = await cookies();
  const hasUserSession = Boolean(requestCookies.get(USER_SESSION_COOKIE_NAME)?.value);
  const hasAdminSession = Boolean(requestCookies.get(ADMIN_SESSION_COOKIE_NAME)?.value);

  return (
    <SiteHeaderClient initialAuthHint={hasUserSession ? "user" : hasAdminSession ? "admin" : "guest"} />
  );
}
