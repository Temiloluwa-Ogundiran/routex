"use client";

import { usePathname } from "next/navigation";
import posthog from "posthog-js";
import { useEffect, useRef, type MutableRefObject } from "react";

type AnalyticsScope = "admin" | "user";

type IdentityPayload = {
  email?: string | null;
  id?: number | string | null;
  is_verified?: boolean | null;
  name?: string | null;
  role?: string | null;
};

type IdentityResponse = {
  data?: IdentityPayload;
  status?: boolean;
};

function getAnalyticsScope(pathname: string | null): AnalyticsScope | null {
  if (!pathname) {
    return null;
  }

  if (pathname === "/dashboard" || pathname.startsWith("/dashboard/")) {
    return "user";
  }

  if (
    pathname === "/admin" ||
    (pathname.startsWith("/admin/") && !pathname.startsWith("/admin/login"))
  ) {
    return "admin";
  }

  return null;
}

function isAnalyticsConfigured() {
  return Boolean(
    process.env.NEXT_PUBLIC_POSTHOG_KEY && process.env.NEXT_PUBLIC_POSTHOG_HOST,
  );
}

function buildDistinctId(scope: AnalyticsScope, id: number | string) {
  return `${scope}:${String(id)}`;
}

function resetIdentity(currentIdentityRef: MutableRefObject<string | null>) {
  if (!currentIdentityRef.current) {
    return;
  }

  posthog.reset();
  currentIdentityRef.current = null;
}

export function PostHogIdentityBridge() {
  const pathname = usePathname();
  const currentIdentityRef = useRef<string | null>(null);

  useEffect(() => {
    if (!isAnalyticsConfigured()) {
      return;
    }

    const scope = getAnalyticsScope(pathname);
    if (!scope) {
      return;
    }
    const resolvedScope: AnalyticsScope = scope;

    let cancelled = false;

    async function syncIdentity() {
      try {
        const response = await fetch(
          resolvedScope === "admin" ? "/api/admin/me" : "/api/auth/me",
          {
            cache: "no-store",
            credentials: "same-origin",
          },
        );

        if (cancelled) {
          return;
        }

        if (!response.ok) {
          resetIdentity(currentIdentityRef);
          return;
        }

        const payload = (await response.json().catch(() => null)) as
          | IdentityResponse
          | null;
        const identity = payload?.data;
        if (!identity?.id) {
          resetIdentity(currentIdentityRef);
          return;
        }

        const distinctId = buildDistinctId(resolvedScope, identity.id);
        if (currentIdentityRef.current === distinctId) {
          return;
        }

        posthog.identify(distinctId, {
          email: identity.email ?? null,
          is_verified: identity.is_verified ?? null,
          name: identity.name ?? null,
          role: identity.role ?? (resolvedScope === "admin" ? "admin" : "user"),
        });
        currentIdentityRef.current = distinctId;
      } catch {
        if (cancelled) {
          return;
        }

        resetIdentity(currentIdentityRef);
      }
    }

    void syncIdentity();

    return () => {
      cancelled = true;
    };
  }, [pathname]);

  return null;
}
