"use client";

import Link from "next/link";
import posthog from "posthog-js";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { docsHref, isExternalHref } from "../../lib/docs-url";

type SiteHeaderClientProps = {
  initialAuthHint: "guest" | "user" | "admin";
};

type AuthKind = "guest" | "user" | "admin";

type AuthState = {
  kind: AuthKind;
  resolved: boolean;
};

const BASE_NAV_ITEMS = [
  { label: "Product", href: "/#product" },
  { label: "Why RouteX", href: "/#route" },
  { label: "Docs", href: docsHref() },
];

const TICKER_ITEMS = [
  "RouteX ships loud",
  "Checkout ready",
  "Signed webhooks",
  "Manual override",
  "Failover ready",
  "One merchant contract",
];

async function readJson(response: Response) {
  return response.json().catch(() => null);
}

export function SiteHeaderClient({ initialAuthHint }: SiteHeaderClientProps) {
  const pathname = usePathname();
  const [authState, setAuthState] = useState<AuthState>({
    kind: initialAuthHint,
    resolved: initialAuthHint !== "guest",
  });

  useEffect(() => {
    let cancelled = false;

    async function loadAuthState() {
      const userResponse = await fetch("/api/auth/me", {
        cache: "no-store",
        credentials: "same-origin",
      });

      if (userResponse.ok) {
        await readJson(userResponse);
        if (!cancelled) {
          setAuthState({ kind: "user", resolved: true });
        }
        return;
      }

      const adminResponse = await fetch("/api/admin/me", {
        cache: "no-store",
        credentials: "same-origin",
      });

      if (adminResponse.ok) {
        await readJson(adminResponse);
        if (!cancelled) {
          setAuthState({ kind: "admin", resolved: true });
        }
        return;
      }

      if (!cancelled) {
        setAuthState({ kind: "guest", resolved: true });
      }
    }

    void loadAuthState();

    return () => {
      cancelled = true;
    };
  }, [pathname]);

  const navItems = useMemo(() => {
    if (authState.kind === "user") {
      return BASE_NAV_ITEMS;
    }

    if (authState.kind === "admin") {
      return BASE_NAV_ITEMS;
    }

    return BASE_NAV_ITEMS;
  }, [authState.kind]);

  function renderNavItem(item: { label: string; href: string }) {
    if (isExternalHref(item.href)) {
      return (
        <a className="site-header__link" href={item.href} key={`${item.label}-${item.href}`}>
          {item.label}
        </a>
      );
    }

    return (
      <Link className="site-header__link" href={item.href} key={`${item.label}-${item.href}`}>
        {item.label}
      </Link>
    );
  }

  async function handleSignOut() {
    if (authState.kind === "admin") {
      posthog.reset();
      await fetch("/api/admin/logout", { method: "POST" }).catch(() => null);
      window.location.href = "/admin/login";
      return;
    }

    posthog.reset();
    await fetch("/api/auth/logout", { method: "POST" }).catch(() => null);
    window.location.href = "/";
  }

  function renderActions() {
    if (!authState.resolved) {
      return <div className="site-header__actions site-header__actions--loading" />;
    }

    if (authState.kind === "user") {
      return (
        <div className="site-header__actions">
          <Link className="site-header__login" href="/dashboard">
            Dashboard
          </Link>
          <button className="push-button push-button--primary" onClick={() => void handleSignOut()} type="button">
            Sign out
          </button>
        </div>
      );
    }

    if (authState.kind === "admin") {
      return (
        <div className="site-header__actions">
          <Link className="site-header__login" href="/admin">
            Admin
          </Link>
          <button className="push-button push-button--primary" onClick={() => void handleSignOut()} type="button">
            Sign out
          </button>
        </div>
      );
    }

    return (
      <div className="site-header__actions">
        <Link className="site-header__login" href="/login">
          Log in
        </Link>
        <Link className="push-button push-button--primary" href="/signup">
          Get Started
        </Link>
      </div>
    );
  }

  return (
    <header className="site-header">
      <div aria-hidden="true" className="site-header__ticker">
        <div className="site-header__ticker-track">
          {[...TICKER_ITEMS, ...TICKER_ITEMS].map((item, index) => (
            <span key={`${item}-${index}`}>{item}</span>
          ))}
        </div>
      </div>

      <div className="site-header__bar">
        <Link className="site-header__brand" href="/">
          <span aria-hidden="true" className="site-header__mark">
            R
          </span>
          <span className="site-header__wordmark">RouteX</span>
        </Link>

        <nav aria-label="Primary" className="site-header__nav">
          {navItems.map(renderNavItem)}
        </nav>

        {renderActions()}
      </div>
    </header>
  );
}
