import Link from "next/link";
import type { ReactNode } from "react";

import type { RouterTransactionDetail } from "../../lib/dashboard-api";

type TransactionDetailShellProps = {
  reference: string;
  createdAt?: string | null;
  state:
    | { kind: "success"; detail: RouterTransactionDetail }
    | { kind: "not-found"; message?: string }
    | { kind: "auth-required"; message?: string }
    | { kind: "forbidden"; message?: string }
    | { kind: "error"; message?: string };
};

function formatCurrency(amount: number, currency: string) {
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatGatewayName(gatewayCode: string | null) {
  if (!gatewayCode) {
    return "unassigned";
  }

  if (gatewayCode === "fltw") {
    return "Flutterwave";
  }

  if (gatewayCode === "pstk") {
    return "Paystack";
  }

  if (gatewayCode === "kora") {
    return "Korapay";
  }

  if (gatewayCode === "isw") {
    return "Interswitch";
  }

  return gatewayCode.toUpperCase();
}

function formatStatusLabel(status: string) {
  return status.replaceAll("_", " ");
}

function getStatusTone(status: string) {
  const normalized = status.toLowerCase();

  if (normalized.includes("success")) {
    return "success";
  }

  if (normalized.includes("reconcil")) {
    return "pending";
  }

  if (normalized.includes("fail")) {
    return "failed";
  }

  return "pending";
}

function ScoreBar({
  label,
  score,
}: {
  label: string;
  score: number;
}) {
  return (
    <div className="transaction-detail-score">
      <div className="transaction-detail-score__meta">
        <strong>{formatGatewayName(label)}</strong>
        <span>{score.toFixed(1)}</span>
      </div>
      <div
        aria-hidden="true"
        className="transaction-detail-score__track"
      >
        <span
          className="transaction-detail-score__fill"
          style={{ width: `${Math.min(Math.max(score, 0), 100)}%` }}
        />
      </div>
    </div>
  );
}

function EmptyPill({
  children,
}: {
  children: ReactNode;
}) {
  return <span className="transaction-detail-empty-pill">{children}</span>;
}

export function TransactionDetailShell({
  reference,
  createdAt,
  state,
}: TransactionDetailShellProps) {
  if (state.kind !== "success") {
    const heading =
      state.kind === "not-found"
        ? "Transaction not found"
        : state.kind === "auth-required"
          ? "Authentication required"
          : state.kind === "forbidden"
            ? "Access forbidden"
            : "Unable to load transaction detail";

    return (
      <main className="dashboard-shell">
        <section className="transaction-detail-shell transaction-detail-shell--error">
          <div className="transaction-detail-hero">
            <p className="section-badge">RouteX Observability</p>
            <h1>{heading}</h1>
            <p>
              {state.message ??
                "We could not load this transaction through the admin proxy route."}
            </p>
            <div className="transaction-detail-actions">
              <Link className="push-button push-button--primary" href="/admin">
                Back to dashboard
              </Link>
            </div>
          </div>
        </section>
      </main>
    );
  }

  const { detail } = state;
  const { transaction, routing_decision, attempts, failover_summary, webhook_trace } = detail;
  const statusTone = getStatusTone(transaction.status);
  const scoreEntries = Object.entries(routing_decision.score_breakdown).sort(
    (left, right) => right[1] - left[1],
  );

  return (
    <main className="dashboard-shell">
      <section className="transaction-detail-shell">
        <div className="transaction-detail-hero">
          <p className="section-badge">RouteX Observability</p>
          <h1>{transaction.reference}</h1>
          <div className="transaction-detail-badges">
            <span className={`dashboard-status-chip dashboard-status-chip--${statusTone}`}>
              {formatStatusLabel(transaction.status)}
            </span>
            <span className="transaction-detail-pill">
              {formatGatewayName(transaction.selected_gateway)}
            </span>
            <span className="transaction-detail-pill">
              {formatCurrency(transaction.amount, transaction.currency)}
            </span>
          </div>
          <div className="transaction-detail-meta">
            <span>
              Created {formatDateTime(transaction.created_at)}
            </span>
            <span>
              Updated {formatDateTime(transaction.updated_at)}
            </span>
            {createdAt ? <span>Query created_at {formatDateTime(createdAt)}</span> : null}
          </div>
          <p className="transaction-detail-lead">
            {routing_decision.reason ??
              "No routing reason snapshot was returned for this transaction."}
          </p>
          <div className="transaction-detail-actions">
            <Link className="push-button push-button--secondary" href="/admin">
              Back to dashboard
            </Link>
          </div>
        </div>

        <div className="transaction-detail-grid">
          <article className="transaction-detail-card">
            <p className="transaction-detail-card__eyebrow">Routing decision</p>
            <h2>Why this gateway won</h2>
            <div className="transaction-detail-stack">
              <div className="transaction-detail-copy">
                <span>Fallback order</span>
                <strong>{routing_decision.fallback_order.join(" -> ") || "none"}</strong>
              </div>
              <div className="transaction-detail-copy">
                <span>Rejected gateways</span>
                {Object.keys(routing_decision.rejected_gateways).length > 0 ? (
                  <dl className="transaction-detail-dl">
                    {Object.entries(routing_decision.rejected_gateways).map(
                      ([gateway, reason]) => (
                        <div key={gateway}>
                          <dt>{formatGatewayName(gateway)}</dt>
                          <dd>{String(reason)}</dd>
                        </div>
                      ),
                    )}
                  </dl>
                ) : (
                  <EmptyPill>No gateways rejected</EmptyPill>
                )}
              </div>
            </div>
          </article>

          <article className="transaction-detail-card">
            <p className="transaction-detail-card__eyebrow">Score breakdown</p>
            <h2>Routing scores</h2>
            <div className="transaction-detail-scores">
              {scoreEntries.length > 0 ? (
                scoreEntries.map(([gateway, score]) => (
                  <ScoreBar key={gateway} label={gateway} score={score} />
                ))
              ) : (
                <EmptyPill>Score breakdown unavailable</EmptyPill>
              )}
            </div>
          </article>

          <article className="transaction-detail-card transaction-detail-card--wide">
            <p className="transaction-detail-card__eyebrow">Attempts timeline</p>
            <h2>Attempt history</h2>
            <div className="transaction-detail-timeline">
              {attempts.map((attempt) => (
                <article
                  className="transaction-detail-attempt"
                  key={`${attempt.attempt_no}-${attempt.gateway}-${attempt.created_at}`}
                >
                  <div className="transaction-detail-attempt__topline">
                    <strong>Attempt {attempt.attempt_no}</strong>
                    <span className={`dashboard-status-chip dashboard-status-chip--${getStatusTone(attempt.status)}`}>
                      {formatStatusLabel(attempt.status)}
                    </span>
                  </div>
                  <p>{formatGatewayName(attempt.gateway)}</p>
                  <dl className="transaction-detail-attempt__meta">
                    <div>
                      <dt>Gateway ref</dt>
                      <dd>{attempt.gateway_reference ?? "n/a"}</dd>
                    </div>
                    <div>
                      <dt>Latency</dt>
                      <dd>
                        {attempt.latency_ms !== null ? `${attempt.latency_ms}ms` : "n/a"}
                      </dd>
                    </div>
                    <div>
                      <dt>Created</dt>
                      <dd>{formatDateTime(attempt.created_at)}</dd>
                    </div>
                    <div>
                      <dt>Error</dt>
                      <dd>{attempt.error_message ?? attempt.error_code ?? "none"}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          </article>

          <article className="transaction-detail-card">
            <p className="transaction-detail-card__eyebrow">Failover summary</p>
            <h2>Recovery result</h2>
            <dl className="transaction-detail-dl">
              <div>
                <dt>Did failover</dt>
                <dd>{failover_summary.did_failover ? "Yes" : "No"}</dd>
              </div>
              <div>
                <dt>Failover count</dt>
                <dd>{failover_summary.failover_count}</dd>
              </div>
              <div>
                <dt>Recovered after failover</dt>
                <dd>{failover_summary.recovered_after_failover ? "Yes" : "No"}</dd>
              </div>
            </dl>
          </article>

          <article className="transaction-detail-card">
            <p className="transaction-detail-card__eyebrow">Webhook trace</p>
            <h2>Reconciliation panel</h2>
            <dl className="transaction-detail-dl">
              <div>
                <dt>Last event</dt>
                <dd>{webhook_trace.last_event ?? "none"}</dd>
              </div>
              <div>
                <dt>Last status</dt>
                <dd>{webhook_trace.last_status ?? "none"}</dd>
              </div>
              <div>
                <dt>Last gateway</dt>
                <dd>{formatGatewayName(webhook_trace.last_gateway)}</dd>
              </div>
              <div>
                <dt>Reconciling</dt>
                <dd>{webhook_trace.is_reconciling ? "Yes" : "No"}</dd>
              </div>
            </dl>
          </article>
        </div>
      </section>
    </main>
  );
}
