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
export const PENDING_AUTH_STORAGE_KEY = "routex.pending-auth";
const SESSION_MAX_AGE_SECONDS = 60 * 60 * 12;

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

export function createClearedUserSessionCookieOptions() {
  return createSessionCookieOptions(0);
}

export function createClearedAdminSessionCookieOptions() {
  return createSessionCookieOptions(0);
}

export function readPendingAuthRecord(): PendingAuthRecord | null {
  if (typeof window === "undefined") {
    return null;
  }

  const rawRecord = window.sessionStorage.getItem(PENDING_AUTH_STORAGE_KEY);
  if (!rawRecord) {
    return null;
  }

  try {
    const parsedRecord = JSON.parse(rawRecord) as PendingAuthRecord;
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

export function storePendingAuthRecord(record: PendingAuthRecord) {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(PENDING_AUTH_STORAGE_KEY, JSON.stringify(record));
}

export function clearPendingAuthRecord() {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(PENDING_AUTH_STORAGE_KEY);
}
