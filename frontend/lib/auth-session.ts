export type PendingAuthMode = "login" | "signup";

export type PendingAuthRecord = {
  mode: PendingAuthMode;
  email: string;
  password: string;
  name?: string;
  redirectTo?: string;
};

export const USER_SESSION_COOKIE_NAME = "routex_user_session";
export const ADMIN_SESSION_COOKIE_NAME = "routex_admin_session";
export const PENDING_AUTH_COOKIE_NAME = "routex_pending_auth";
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 12;
const PENDING_AUTH_MAX_AGE_SECONDS = 60 * 15;

function createSessionCookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    maxAge,
    path: "/",
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
  };
}

export function createUserSessionCookieOptions() {
  return createSessionCookieOptions(SESSION_MAX_AGE_SECONDS);
}

export function createAdminSessionCookieOptions() {
  return createSessionCookieOptions(SESSION_MAX_AGE_SECONDS);
}

export function createPendingAuthCookieOptions() {
  return createSessionCookieOptions(PENDING_AUTH_MAX_AGE_SECONDS);
}

export function createClearedUserSessionCookieOptions() {
  return createSessionCookieOptions(0);
}

export function createClearedAdminSessionCookieOptions() {
  return createSessionCookieOptions(0);
}

export function createClearedPendingAuthCookieOptions() {
  return createSessionCookieOptions(0);
}

export function encodePendingAuthRecord(record: PendingAuthRecord) {
  return Buffer.from(JSON.stringify(record), "utf-8").toString("base64url");
}

export function decodePendingAuthRecord(value: string | undefined): PendingAuthRecord | null {
  if (!value) {
    return null;
  }

  try {
    const parsedRecord = JSON.parse(
      Buffer.from(value, "base64url").toString("utf-8"),
    ) as PendingAuthRecord;

    if (
      parsedRecord &&
      (parsedRecord.mode === "login" || parsedRecord.mode === "signup") &&
      typeof parsedRecord.email === "string" &&
      typeof parsedRecord.password === "string"
    ) {
      return parsedRecord;
    }
  } catch {
    return null;
  }

  return null;
}
