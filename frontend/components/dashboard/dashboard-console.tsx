"use client";

import { useEffect, useEffectEvent, useState } from "react";
import posthog from "posthog-js";

import type {
  RouterDashboardData,
  RouterGatewayHealth,
  RouterRule,
} from "../../lib/dashboard-api";
import { FailoverFeed } from "./failover-feed";
import { GatewayControlPanel } from "./gateway-control-panel";
import { GatewayHealthGrid } from "./gateway-health-grid";
import { RecentTransactions } from "./recent-transactions";
import { RoutingRulesPanel } from "./routing-rules-panel";
import { ScoreBreakdownCard } from "./score-breakdown-card";
import { PushButton } from "../ui/push-button";

function StatCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "yellow" | "sage" | "dark";
}) {
  return (
    <article
      aria-label={label}
      className={`dashboard-stat-card dashboard-stat-card--${tone}`}
    >
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}

function rebuildSummary(
  gateways: RouterGatewayHealth[],
  current: RouterDashboardData["summary"],
) {
  return {
    ...current,
    total_gateways: gateways.length,
    active_gateways: gateways.filter((gateway) => gateway.is_active).length,
  };
}

function getLastRefreshedAt(gateways: RouterGatewayHealth[]) {
  const timestamps = gateways
    .map((gateway) => gateway.last_checked_at)
    .filter((value): value is string => Boolean(value))
    .sort((left, right) => new Date(right).getTime() - new Date(left).getTime());

  return timestamps[0] ?? null;
}

function formatLastRefreshed(lastRefreshedAt: string | null) {
  if (!lastRefreshedAt) {
    return "Last refreshed: waiting for first snapshot";
  }

  return `Last refreshed: ${new Date(lastRefreshedAt).toLocaleTimeString("en-NG", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })}`;
}

async function signOutAdmin() {
  posthog.reset();
  await fetch("/api/admin/logout", {
    method: "POST",
  }).catch(() => null);
  window.location.href = "/admin/login";
}

type DashboardConsoleProps = {
  initialDashboard: RouterDashboardData;
  initialRules: RouterRule[];
};

export function DashboardConsole({
  initialDashboard,
  initialRules,
}: DashboardConsoleProps) {
  const [dashboard, setDashboard] = useState(initialDashboard);
  const [rules, setRules] = useState(initialRules);
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  function handleGatewayUpdated(updatedGateway: RouterGatewayHealth) {
    setDashboard((current) => {
      const gatewayHealth = current.gateway_health.map((gateway) =>
        gateway.gateway_code === updatedGateway.gateway_code
          ? updatedGateway
          : gateway,
      );

      return {
        ...current,
        gateway_health: gatewayHealth,
        summary: rebuildSummary(gatewayHealth, current.summary),
      };
    });
  }

  const syncDashboard = useEffectEvent(async () => {
    try {
      const response = await fetch("/api/admin/router", {
        method: "GET",
        cache: "no-store",
      });
      if (!response.ok) {
        return;
      }

      const nextDashboard = (await response.json()) as RouterDashboardData;
      setDashboard(nextDashboard);
      setRefreshMessage("Live dashboard synced from the latest health snapshots.");
    } catch {
      setRefreshMessage("Live dashboard sync failed.");
    }
  });

  useEffect(() => {
    const interval = window.setInterval(() => {
      void syncDashboard();
    }, 30000);

    return () => window.clearInterval(interval);
  }, [syncDashboard]);

  async function handleRefreshNow() {
    setIsRefreshing(true);
    try {
      const response = await fetch("/api/admin/router/refresh-health", {
        method: "POST",
      });
      const payload = (await response.json()) as {
        dashboard?: RouterDashboardData;
        message?: string;
      };

      if (!response.ok || !payload.dashboard) {
        setRefreshMessage(payload.message ?? "Unable to refresh gateway health right now.");
        return;
      }

      setDashboard(payload.dashboard);
      setRefreshMessage(payload.message ?? "Health refresh complete.");
    } catch {
      setRefreshMessage("Unable to refresh gateway health right now.");
    } finally {
      setIsRefreshing(false);
    }
  }

  const lastRefreshedAt = getLastRefreshedAt(dashboard.gateway_health);

  return (
    <main className="dashboard-shell">
      <section className="dashboard-hero">
        <div className="dashboard-hero__copy">
          <p className="section-badge">Router Control Room</p>
          <h1>Watch RouteX move traffic before conversion drops.</h1>
          <p>
            This control room surfaces gateway health, routed transactions,
            failover recoveries, and manual override controls in one
            neo-brutalist operations view backed by the live admin APIs.
          </p>
        </div>

        <div className="dashboard-hero__actions">
          <button
            className="push-button push-button--primary"
            disabled={isRefreshing}
            onClick={() => void handleRefreshNow()}
            type="button"
          >
            Refresh Health Now
          </button>
          <PushButton onClick={() => void signOutAdmin()} variant="secondary">
            Sign out
          </PushButton>
          <div className="dashboard-hero__refresh-meta">
            <p>{formatLastRefreshed(lastRefreshedAt)}</p>
            <span className="dashboard-status-pill dashboard-status-pill--accent">
              Auto-refresh: 30s
            </span>
          </div>
        </div>
        {refreshMessage ? (
          <p className="dashboard-refresh-feedback">{refreshMessage}</p>
        ) : null}

        <div className="dashboard-hero__stats">
          <StatCard
            label="Total Gateways"
            value={String(dashboard.summary.total_gateways)}
            tone="yellow"
          />
          <StatCard
            label="Active Routes"
            value={String(dashboard.summary.active_gateways)}
            tone="sage"
          />
          <StatCard
            label="Recent Failovers"
            value={String(dashboard.summary.recent_failover_count)}
            tone="dark"
          />
          <StatCard
            label="Routed Transactions"
            value={String(dashboard.summary.routed_transaction_count)}
            tone="yellow"
          />
        </div>
      </section>

      <GatewayHealthGrid gateways={dashboard.gateway_health} />
      <GatewayControlPanel
        gateways={dashboard.gateway_health}
        onGatewayUpdated={handleGatewayUpdated}
      />
      <RoutingRulesPanel
        onRuleCreated={(rule) =>
          setRules((currentRules) => [rule, ...currentRules])
        }
        onRuleUpdated={(updatedRule) =>
          setRules((currentRules) =>
            currentRules.map((rule) =>
              rule.id === updatedRule.id ? updatedRule : rule,
            ),
          )
        }
        rules={rules}
      />
      <RecentTransactions transactions={dashboard.recent_transactions} />

      <section className="dashboard-split">
        <FailoverFeed failovers={dashboard.recent_failovers} />
        <ScoreBreakdownCard gateways={dashboard.gateway_health} />
      </section>
    </main>
  );
}
