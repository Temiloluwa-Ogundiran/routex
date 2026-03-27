"use client";

import { useEffect, useState } from "react";
import posthog from "posthog-js";

import type { RouterDashboardData, RouterRule } from "../../lib/dashboard-api";
import { DOCS_LINK_REL, DOCS_LINK_TARGET, docsHref } from "../../lib/docs-url";
import { OpsShell } from "../layout/ops-shell";
import { DashboardConsole } from "../dashboard/dashboard-console";
import { PushButton } from "../ui/push-button";

type LoadState = "idle" | "loading" | "ready" | "error";

type AdminDashboardState = {
  dashboard: RouterDashboardData;
  rules: RouterRule[];
};

async function signOutAdmin() {
  posthog.reset();
  await fetch("/api/admin/logout", {
    method: "POST",
  }).catch(() => null);
  window.location.replace("/admin/login");
}

async function loadAdminDashboardState(): Promise<AdminDashboardState> {
  const [dashboardResponse, rulesResponse] = await Promise.all([
    fetch("/api/admin/router", {
      cache: "no-store",
      credentials: "same-origin",
    }),
    fetch("/api/admin/router/rules", {
      cache: "no-store",
      credentials: "same-origin",
    }),
  ]);

  if (dashboardResponse.status === 401 || rulesResponse.status === 401) {
    window.location.replace("/admin/login");
    throw new Error("Admin authentication required.");
  }

  const dashboardBody = await dashboardResponse.json().catch(() => ({
    detail: "Unable to load admin dashboard data.",
  }));
  const rulesBody = await rulesResponse.json().catch(() => ({
    detail: "Unable to load routing rules.",
  }));

  if (!dashboardResponse.ok || !rulesResponse.ok) {
    const dashboardMessage =
      "detail" in dashboardBody && typeof dashboardBody.detail === "string"
        ? dashboardBody.detail
        : null;
    const rulesMessage =
      "detail" in rulesBody && typeof rulesBody.detail === "string"
        ? rulesBody.detail
        : null;

    throw new Error(
      dashboardMessage ??
        rulesMessage ??
        "Unable to load admin dashboard data right now.",
    );
  }

  return {
    dashboard: dashboardBody as RouterDashboardData,
    rules: rulesBody as RouterRule[],
  };
}

export function AdminDashboardShell() {
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [adminState, setAdminState] = useState<AdminDashboardState | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadState("loading");
    setErrorMessage(null);

    loadAdminDashboardState()
      .then((nextState) => {
        if (cancelled) {
          return;
        }

        setAdminState(nextState);
        setLoadState("ready");
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }

        setAdminState(null);
        setLoadState("error");
        setErrorMessage(
          error instanceof Error
            ? error.message
            : "Unable to load admin dashboard data right now.",
        );
      });

    return () => {
      cancelled = true;
    };
  }, [refreshKey]);

  if (loadState === "loading" || loadState === "idle") {
    return (
      <OpsShell
        homeHref="/admin"
        initials="RA"
        navSections={[
          {
            label: "Main menu",
            items: [
              { href: "/admin", label: "Overview" },
              { href: "#dashboard-gateways", label: "Gateway Health" },
              { href: "#dashboard-controls", label: "Gateway Controls" },
            ],
          },
          {
            label: "Management",
            items: [
              { href: "#dashboard-rules", label: "Routing Rules" },
              { href: "#dashboard-transactions", label: "Transactions" },
            ],
          },
        ]}
        subtitle="Router control"
        title="RouteX Admin"
        accountMenu={
          <button
            className="ops-account-menu__button"
            onClick={() => void signOutAdmin()}
            type="button"
          >
            Sign out
          </button>
        }
        actions={
          <>
            <a
              className="push-button push-button--secondary"
              href={docsHref()}
              rel={DOCS_LINK_REL}
              target={DOCS_LINK_TARGET}
            >
              API docs
            </a>
          </>
        }
      >
        <section className="dashboard-hero">
          <div className="dashboard-hero__copy">
            <p className="section-badge">Router Control Room</p>
            <h1>Loading the RouteX control room</h1>
            <p>We are pulling live router health, failovers, and policy controls.</p>
          </div>
        </section>
      </OpsShell>
    );
  }

  if (loadState === "error" || !adminState) {
    return (
      <OpsShell
        homeHref="/admin"
        initials="RA"
        navSections={[
          {
            label: "Main menu",
            items: [
              { href: "/admin", label: "Overview" },
              { href: "#dashboard-gateways", label: "Gateway Health" },
              { href: "#dashboard-controls", label: "Gateway Controls" },
            ],
          },
          {
            label: "Management",
            items: [
              { href: "#dashboard-rules", label: "Routing Rules" },
              { href: "#dashboard-transactions", label: "Transactions" },
            ],
          },
        ]}
        subtitle="Router control"
        title="RouteX Admin"
        accountMenu={
          <button
            className="ops-account-menu__button"
            onClick={() => void signOutAdmin()}
            type="button"
          >
            Sign out
          </button>
        }
        actions={
          <>
            <a
              className="push-button push-button--secondary"
              href={docsHref()}
              rel={DOCS_LINK_REL}
              target={DOCS_LINK_TARGET}
            >
              API docs
            </a>
          </>
        }
      >
        <section className="dashboard-hero">
          <div className="dashboard-hero__copy">
            <p className="section-badge">Router Control Room</p>
            <h1>We couldn&apos;t load the admin dashboard</h1>
            <p>{errorMessage ?? "Please verify the backend connection and try again."}</p>
            <div className="dashboard-hero__actions">
              <PushButton onClick={() => setRefreshKey((current) => current + 1)}>
                Retry
              </PushButton>
            </div>
          </div>
        </section>
      </OpsShell>
    );
  }

  return (
    <OpsShell
      homeHref="/admin"
      initials="RA"
      navSections={[
        {
          label: "Main menu",
          items: [
            { href: "/admin", label: "Overview" },
            { href: "#dashboard-gateways", label: "Gateway Health" },
            { href: "#dashboard-controls", label: "Gateway Controls" },
          ],
        },
        {
          label: "Management",
          items: [
            { href: "#dashboard-rules", label: "Routing Rules" },
            { href: "#dashboard-transactions", label: "Transactions" },
          ],
        },
      ]}
      subtitle="Router control"
      title="RouteX Admin"
      accountMenu={
        <button
          className="ops-account-menu__button"
          onClick={() => void signOutAdmin()}
          type="button"
        >
          Sign out
        </button>
      }
      actions={
        <>
          <a
            className="push-button push-button--secondary"
            href={docsHref()}
            rel={DOCS_LINK_REL}
            target={DOCS_LINK_TARGET}
          >
            API docs
          </a>
        </>
      }
    >
      <DashboardConsole
        initialDashboard={adminState.dashboard}
        initialRules={adminState.rules}
      />
    </OpsShell>
  );
}
