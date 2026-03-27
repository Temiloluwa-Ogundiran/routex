"use client";

import type { FormEvent } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import posthog from "posthog-js";
import { startTransition, useEffect, useMemo, useState } from "react";

import {
  maskApiKey,
  normalizeMode,
  type MerchantDashboardData,
  type MerchantDashboardResponse,
  type MerchantWorkspaceMerchant,
  type MerchantWorkspacePaymentLink,
} from "../../lib/app-dashboard";
import { DOCS_LINK_REL, DOCS_LINK_TARGET, docsHref } from "../../lib/docs-url";
import { OpsShell } from "../layout/ops-shell";
import { PushButton } from "../ui/push-button";

type LoadState = "idle" | "loading" | "ready" | "error";

function formatCurrency(amount: number, currency = "NGN") {
  const formattedAmount = new Intl.NumberFormat("en-NG", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);

  return `${currency} ${formattedAmount}`;
}

function formatDate(value: string | null | undefined) {
  if (!value) {
    return "Unavailable";
  }

  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) {
    return "Unavailable";
  }

  return new Intl.DateTimeFormat("en-NG", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(parsedDate);
}

function formatRelativeDateTime(value: string | null | undefined) {
  if (!value) {
    return "Unavailable";
  }

  const parsedDate = new Date(value);
  if (Number.isNaN(parsedDate.getTime())) {
    return "Unavailable";
  }

  return new Intl.DateTimeFormat("en-NG", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsedDate);
}

function getInitials(value: string | null | undefined) {
  if (!value) {
    return "RX";
  }

  const parts = value
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2);

  if (parts.length === 0) {
    return "RX";
  }

  return parts.map((part) => part[0]?.toUpperCase() ?? "").join("");
}

function getGatewayDisplayName(gatewayCode: string | null | undefined) {
  switch ((gatewayCode ?? "").trim().toLowerCase()) {
    case "kora":
      return "Kora";
    case "pstk":
      return "Paystack";
    case "fltw":
      return "Flutterwave";
    case "isw":
      return "Interswitch";
    default:
      return "Automatic";
  }
}

function buildDashboardUrl(
  merchantId: string | null,
  mode: "test" | "live",
  currentSearchParams?: URLSearchParams,
) {
  const params = currentSearchParams
    ? new URLSearchParams(currentSearchParams.toString())
    : new URLSearchParams();

  if (merchantId) {
    params.set("merchantId", merchantId);
  } else {
    params.delete("merchantId");
  }
  params.set("mode", mode);

  const query = params.toString();
  return query ? `/dashboard?${query}` : "/dashboard";
}

function buildDashboardSectionUrl(
  merchantId: string | null,
  mode: "test" | "live",
  sectionId: string,
  currentSearchParams?: URLSearchParams,
) {
  return `${buildDashboardUrl(merchantId, mode, currentSearchParams)}#${sectionId}`;
}

async function readDashboardData(
  merchantId: string | null,
  mode: "test" | "live",
): Promise<MerchantDashboardResponse> {
  const params = new URLSearchParams();
  if (merchantId) {
    params.set("merchantId", merchantId);
  }
  params.set("mode", mode);

  const response = await fetch(`/api/app/dashboard?${params.toString()}`, {
    cache: "no-store",
    credentials: "same-origin",
  });

  const responseBody = (await response.json().catch(() => ({
    message: "We could not parse the dashboard response.",
    status: false,
  }))) as MerchantDashboardResponse;

  if (response.status === 401) {
    window.location.replace("/login");
    return {
      status: false,
      message: "Please sign in again.",
    };
  }

  if (!response.ok) {
    return {
      status: false,
      message:
        responseBody.message ?? "We could not load your merchant workspace.",
    };
  }

  return responseBody;
}

async function signOutUser() {
  posthog.reset();
  await fetch("/api/auth/logout", {
    method: "POST",
  }).catch(() => null);
  window.location.href = "/login";
}

async function copyToClipboard(value: string | null | undefined) {
  if (!value) {
    return false;
  }

  if (!navigator.clipboard?.writeText) {
    return false;
  }

  await navigator.clipboard.writeText(value);
  return true;
}

export function MerchantDashboardShell() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const merchantId = searchParams.get("merchantId");
  const mode = normalizeMode(searchParams.get("mode"));

  const [dashboard, setDashboard] = useState<MerchantDashboardData | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [createMerchantState, setCreateMerchantState] = useState<{
    submitting: boolean;
    message: string | null;
    error: string | null;
  }>({
    submitting: false,
    message: null,
    error: null,
  });
  const [copiedLabel, setCopiedLabel] = useState<string | null>(null);
  const [paymentLinkState, setPaymentLinkState] = useState<{
    open: boolean;
    submitting: boolean;
    message: string | null;
    error: string | null;
  }>({
    open: false,
    submitting: false,
    message: null,
    error: null,
  });

  useEffect(() => {
    let cancelled = false;
    setLoadState("loading");
    setErrorMessage(null);

    readDashboardData(merchantId, mode)
      .then((response) => {
        if (cancelled) {
          return;
        }

        if (!response.status || !response.data) {
          setDashboard(null);
          setLoadState("error");
          setErrorMessage(
            response.message ?? "We could not load your merchant workspace.",
          );
          return;
        }

        setDashboard(response.data);
        setLoadState("ready");
      })
      .catch(() => {
        if (cancelled) {
          return;
        }

        setDashboard(null);
        setLoadState("error");
        setErrorMessage("We could not load your merchant workspace.");
      });

    return () => {
      cancelled = true;
    };
  }, [merchantId, mode, refreshKey]);

  const selectedMerchant = dashboard?.selected_merchant ?? null;
  const selectedModeBalance = useMemo(() => {
    if (!selectedMerchant) {
      return 0;
    }

    return mode === "live"
      ? selectedMerchant.live_balance
      : selectedMerchant.test_balance;
  }, [mode, selectedMerchant]);
  const selectedMerchantId = selectedMerchant?.id ?? merchantId ?? null;
  const dashboardHomeHref = useMemo(
    () => buildDashboardUrl(selectedMerchantId, mode, searchParams),
    [searchParams, selectedMerchantId, mode],
  );
  const opsNavSections = useMemo(
    () => [
      {
        label: "Main menu",
        items: [
          { href: dashboardHomeHref, label: "Overview" },
          {
            href: buildDashboardSectionUrl(
              selectedMerchantId,
              mode,
              "dashboard-wallets",
              searchParams,
            ),
            label: "Wallets",
          },
          {
            href: buildDashboardSectionUrl(
              selectedMerchantId,
              mode,
              "dashboard-transactions",
              searchParams,
            ),
            label: "Transactions",
          },
        ],
      },
      {
        label: "Management",
        items: [
          {
            href: buildDashboardSectionUrl(
              selectedMerchantId,
              mode,
              "dashboard-api-keys",
              searchParams,
            ),
            label: "API Keys",
          },
          {
            href: buildDashboardSectionUrl(
              selectedMerchantId,
              mode,
              "dashboard-payment-links",
              searchParams,
            ),
            label: "Payment Links",
          },
        ],
      },
    ],
    [dashboardHomeHref, searchParams, selectedMerchantId, mode],
  );

  async function handleCreateMerchant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const merchantName = String(formData.get("name") ?? "").trim();
    const merchantEmail = String(formData.get("email") ?? "").trim();

    if (!merchantName || !merchantEmail) {
      setCreateMerchantState({
        submitting: false,
        message: null,
        error: "Merchant name and support email are required.",
      });
      return;
    }

    setCreateMerchantState({
      submitting: true,
      message: null,
      error: null,
    });

    const response = await fetch("/api/app/merchants", {
      body: JSON.stringify({
        email: merchantEmail,
        name: merchantName,
        role: "owner",
      }),
      headers: {
        "Content-Type": "application/json",
      },
      method: "POST",
    });

    const responseBody = (await response.json().catch(() => ({
      detail: "We could not create your merchant workspace.",
    }))) as {
      detail?: string;
      id?: string;
      message?: string;
    };

    if (!response.ok) {
      setCreateMerchantState({
        submitting: false,
        message: null,
        error:
          responseBody.detail ??
          responseBody.message ??
          "We could not create your merchant workspace.",
      });
      return;
    }

    setCreateMerchantState({
      submitting: false,
      message: "Merchant workspace created successfully.",
      error: null,
    });

    const nextMerchantId = responseBody.id ?? null;
    startTransition(() => {
      router.replace(buildDashboardUrl(nextMerchantId, "test", searchParams));
    });
    setRefreshKey((currentValue) => currentValue + 1);
  }

  function handleModeChange(nextMode: "test" | "live") {
    if (mode === nextMode && selectedMerchant?.id === merchantId) {
      return;
    }

    startTransition(() => {
      router.replace(
        buildDashboardUrl(selectedMerchant?.id ?? merchantId, nextMode, searchParams),
      );
    });
  }

  function handleMerchantChange(nextMerchantId: string) {
    startTransition(() => {
      router.replace(buildDashboardUrl(nextMerchantId || null, mode, searchParams));
    });
  }

  async function handleCopy(label: string, value: string | null | undefined) {
    const copied = await copyToClipboard(value);
    setCopiedLabel(copied ? label : "Copy unavailable");
    window.setTimeout(() => {
      setCopiedLabel((currentLabel) =>
        currentLabel === label || currentLabel === "Copy unavailable"
          ? null
          : currentLabel,
      );
    }, 1800);
  }

  async function handleCreatePaymentLink(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedMerchant) {
      return;
    }

    const formData = new FormData(event.currentTarget);
    const title = String(formData.get("title") ?? "").trim();
    const amountValue = Number(String(formData.get("amount") ?? ""));
    const gatewayCode = String(formData.get("gateway_code") ?? "")
      .trim()
      .toLowerCase();

    if (!title) {
      setPaymentLinkState((currentState) => ({
        ...currentState,
        error: "Add a short title for the payment link.",
        message: null,
      }));
      return;
    }

    if (!Number.isFinite(amountValue) || amountValue <= 0) {
      setPaymentLinkState((currentState) => ({
        ...currentState,
        error: "Enter a valid amount greater than zero.",
        message: null,
      }));
      return;
    }

    setPaymentLinkState((currentState) => ({
      ...currentState,
      submitting: true,
      error: null,
      message: null,
    }));

    const response = await fetch("/api/app/payment-links", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        merchant_id: selectedMerchant.id,
        title,
        description: gatewayCode
          ? `Pinned to ${getGatewayDisplayName(gatewayCode)}`
          : null,
        amount_type: "static",
        mode,
        type: "recurring",
        currency: "NGN",
        amount: amountValue,
        gateway_code: gatewayCode || null,
      }),
    });

    const responseBody = (await response.json().catch(() => ({
      detail: "We could not create the payment link.",
    }))) as MerchantWorkspacePaymentLink & {
      detail?: string;
      message?: string;
    };

    if (!response.ok) {
      setPaymentLinkState((currentState) => ({
        ...currentState,
        submitting: false,
        error:
          responseBody.detail ??
          responseBody.message ??
          "We could not create the payment link.",
        message: null,
      }));
      return;
    }

    setDashboard((currentDashboard) => {
      if (!currentDashboard) {
        return currentDashboard;
      }

      return {
        ...currentDashboard,
        payment_links: [responseBody, ...currentDashboard.payment_links],
      };
    });

    event.currentTarget.reset();
    setPaymentLinkState({
      open: false,
      submitting: false,
      error: null,
      message: "Payment link created successfully.",
    });
  }

  if (loadState === "loading" || loadState === "idle") {
    return (
      <OpsShell
        homeHref={dashboardHomeHref}
        initials={getInitials(selectedMerchant?.name ?? dashboard?.user.name)}
        navSections={opsNavSections}
        subtitle="Merchant workspace"
        title="RouteX Ops"
      >
        <section className="dashboard-hero">
          <div className="dashboard-hero__copy">
            <p className="section-badge">Merchant Workspace</p>
            <h1>Loading your RouteX workspace</h1>
            <p>
              We are pulling your merchant profile, balances, transactions, and
              API keys.
            </p>
          </div>
        </section>
      </OpsShell>
    );
  }

  if (loadState === "error" || !dashboard) {
    return (
      <OpsShell
        homeHref={dashboardHomeHref}
        initials={getInitials(selectedMerchant?.name ?? dashboard?.user.name)}
        navSections={opsNavSections}
        subtitle="Merchant workspace"
        title="RouteX Ops"
      >
        <section className="dashboard-hero">
          <div className="dashboard-hero__copy">
            <p className="section-badge">Merchant Workspace</p>
            <h1>We couldn&apos;t load your merchant workspace</h1>
            <p>
              {errorMessage ?? "Please check your backend connection and try again."}
            </p>
            <div className="dashboard-hero__actions">
              <PushButton onClick={() => setRefreshKey((currentValue) => currentValue + 1)}>
                Retry
              </PushButton>
              <a
                className="push-button push-button--secondary"
                href={docsHref()}
                rel={DOCS_LINK_REL}
                target={DOCS_LINK_TARGET}
              >
                Review docs
              </a>
            </div>
          </div>
        </section>
      </OpsShell>
    );
  }

  if (!selectedMerchant) {
    return (
      <OpsShell
        homeHref={dashboardHomeHref}
        initials={getInitials(dashboard.user.name)}
        navSections={opsNavSections}
        subtitle="Merchant workspace"
        title="RouteX Ops"
        accountMenu={
          <button
            className="ops-account-menu__button"
            onClick={() => void signOutUser()}
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
            <p className="section-badge">Merchant Workspace</p>
            <h1>Create your first merchant workspace</h1>
            <p>Your account is ready. Create a workspace to start taking payments.</p>
          </div>

          <form
            className="dashboard-create-form dashboard-card"
            onSubmit={(event) => void handleCreateMerchant(event)}
          >
            <label className="auth-field">
              <span className="dashboard-control-label">Merchant name</span>
              <input
                className="dashboard-control-input"
                defaultValue=""
                name="name"
                placeholder="Ada Stores"
                required
                type="text"
              />
            </label>

            <label className="auth-field">
              <span className="dashboard-control-label">Support email</span>
              <input
                className="dashboard-control-input"
                defaultValue={dashboard.user.email}
                name="email"
                placeholder="merchant@example.com"
                required
                type="email"
              />
            </label>

            {createMerchantState.error ? (
              <p className="auth-form__message auth-form__message--error">
                {createMerchantState.error}
              </p>
            ) : null}
            {createMerchantState.message ? (
              <p className="auth-form__message auth-form__message--success">
                {createMerchantState.message}
              </p>
            ) : null}

            <div className="dashboard-hero__actions">
              <PushButton disabled={createMerchantState.submitting} type="submit">
                {createMerchantState.submitting
                  ? "Creating workspace..."
                  : "Create merchant workspace"}
              </PushButton>
              <a
                className="push-button push-button--secondary"
                href={docsHref()}
                rel={DOCS_LINK_REL}
                target={DOCS_LINK_TARGET}
              >
                Review API docs
              </a>
            </div>
          </form>
        </section>
      </OpsShell>
    );
  }

  return (
    <OpsShell
      homeHref={dashboardHomeHref}
      initials={getInitials(selectedMerchant.name)}
      navSections={opsNavSections}
      subtitle="Merchant workspace"
      title={selectedMerchant.name}
      accountMenu={
        <button
          className="ops-account-menu__button"
          onClick={() => void signOutUser()}
          type="button"
        >
          Sign out
        </button>
      }
      actions={
        <>
          {dashboard.merchants.length > 1 ? (
            <label className="dashboard-select-field dashboard-select-field--inline">
              <span className="dashboard-control-label">Merchant</span>
              <select
                className="dashboard-control-input"
                onChange={(event) => handleMerchantChange(event.target.value)}
                value={selectedMerchant.id}
              >
                {dashboard.merchants.map((merchant: MerchantWorkspaceMerchant) => (
                  <option key={merchant.id} value={merchant.id}>
                    {merchant.name}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <div className="dashboard-mode-toggle dashboard-mode-toggle--inline">
            <span className="dashboard-control-label">Mode</span>
            <div className="dashboard-mode-toggle__buttons">
              <button
                className={`dashboard-toggle-button${mode === "test" ? " dashboard-toggle-button--active" : ""}`}
                onClick={() => handleModeChange("test")}
                type="button"
              >
                Test
              </button>
              <button
                className={`dashboard-toggle-button${mode === "live" ? " dashboard-toggle-button--active" : ""}`}
                onClick={() => handleModeChange("live")}
                type="button"
              >
                Live
              </button>
            </div>
          </div>
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
      <section className="dashboard-hero" id="dashboard-overview">
        <div className="dashboard-hero__copy">
          <p className="section-badge">Merchant Workspace</p>
          <h1>{selectedMerchant.name}</h1>
          <p>
            Welcome back, {dashboard.user.name}. See revenue, balances, keys,
            and payment activity in one place.
          </p>
          <div className="dashboard-card__meta">
            <span>{selectedMerchant.is_verified ? "Live enabled" : "Verification pending"}</span>
            <span>{selectedMerchant.is_active ? "Active" : "Paused"}</span>
            <span>Joined {formatDate(selectedMerchant.joined_at)}</span>
          </div>
        </div>

        {dashboard.warnings.length > 0 ? (
          <div className="dashboard-warning-stack">
            {dashboard.warnings.map((warning) => (
              <p className="dashboard-warning" key={warning}>
                {warning}
              </p>
            ))}
          </div>
        ) : null}

        <div className="dashboard-hero__stats">
          <article className="dashboard-stat-card dashboard-stat-card--yellow">
            <p>Total revenue</p>
            <strong>
              {formatCurrency(
                dashboard.summary?.revenue_metrics.total_revenue ?? 0,
                dashboard.summary?.top_currency?.currency ?? "NGN",
              )}
            </strong>
          </article>
          <article className="dashboard-stat-card dashboard-stat-card--sage">
            <p>Total transactions</p>
            <strong>{dashboard.summary?.revenue_metrics.total_transactions ?? 0}</strong>
          </article>
          <article className="dashboard-stat-card dashboard-stat-card--dark">
            <p>Success rate</p>
            <strong>{`${dashboard.summary?.revenue_metrics.success_rate?.toFixed(1) ?? "0.0"}%`}</strong>
          </article>
          <article className="dashboard-stat-card dashboard-stat-card--yellow">
            <p>{mode === "live" ? "Live balance" : "Test balance"}</p>
            <strong>{formatCurrency(selectedModeBalance, "NGN")}</strong>
          </article>
        </div>
      </section>

      <section className="dashboard-card-grid dashboard-section" id="dashboard-wallets">
        <article className="dashboard-card">
          <div className="dashboard-card__topline">
            <div>
              <p className="dashboard-card__eyebrow">Wallet balances</p>
              <h3>Wallet balances</h3>
            </div>
            <span className="dashboard-status-pill dashboard-status-pill--accent">
              {dashboard.wallets.length} wallet{dashboard.wallets.length === 1 ? "" : "s"}
            </span>
          </div>
          <dl className="dashboard-stat-list">
            {dashboard.wallets.length > 0 ? (
              dashboard.wallets.map((wallet) => (
                <div key={wallet.id}>
                  <dt>{`${wallet.currency} ${wallet.mode}`}</dt>
                  <dd>{formatCurrency(wallet.balance, wallet.currency)}</dd>
                </div>
              ))
            ) : (
              <div>
                <dt>No wallets yet</dt>
                <dd>{mode === "live" ? "Activate live processing to create live wallets." : "Wallets will appear as soon as transactions start flowing."}</dd>
              </div>
            )}
          </dl>
        </article>

        <article className="dashboard-card" id="dashboard-api-keys">
          <div className="dashboard-card__topline">
            <div>
              <p className="dashboard-card__eyebrow">API keys</p>
              <h3>API keys</h3>
            </div>
            <span className="dashboard-status-pill dashboard-status-pill--maintenance">
              Merchant {selectedMerchant.id}
            </span>
          </div>
          <div className="dashboard-key-grid">
            <div className="dashboard-key-card">
              <span className="dashboard-control-label">Test secret</span>
              <strong>{maskApiKey(dashboard.api_tokens?.test.secret)}</strong>
              <button
                className="dashboard-inline-button"
                onClick={() =>
                  void handleCopy("Copied test secret key", dashboard.api_tokens?.test.secret)
                }
                type="button"
              >
                Copy
              </button>
            </div>
            <div className="dashboard-key-card">
              <span className="dashboard-control-label">Test public</span>
              <strong>{maskApiKey(dashboard.api_tokens?.test.public)}</strong>
              <button
                className="dashboard-inline-button"
                onClick={() =>
                  void handleCopy("Copied test public key", dashboard.api_tokens?.test.public)
                }
                type="button"
              >
                Copy
              </button>
            </div>
            <div className="dashboard-key-card">
              <span className="dashboard-control-label">Live secret</span>
              <strong>{maskApiKey(dashboard.api_tokens?.live.secret)}</strong>
              <button
                className="dashboard-inline-button"
                onClick={() =>
                  void handleCopy("Copied live secret key", dashboard.api_tokens?.live.secret)
                }
                type="button"
              >
                Copy
              </button>
            </div>
            <div className="dashboard-key-card">
              <span className="dashboard-control-label">Live public</span>
              <strong>{maskApiKey(dashboard.api_tokens?.live.public)}</strong>
              <button
                className="dashboard-inline-button"
                onClick={() =>
                  void handleCopy("Copied live public key", dashboard.api_tokens?.live.public)
                }
                type="button"
              >
                Copy
              </button>
            </div>
          </div>
          <p className="dashboard-copy-feedback">
            {copiedLabel ?? "Copy your keys here, then move into the docs when you are ready to build."}
          </p>
        </article>
      </section>

      <section className="dashboard-table-shell dashboard-section" id="dashboard-transactions">
        <div className="dashboard-panel__header dashboard-table-shell__header">
          <div>
            <p className="dashboard-panel__eyebrow">Transactions</p>
            <h3>Recent transactions</h3>
          </div>
          <span className="dashboard-status-pill dashboard-status-pill--accent">
            {dashboard.transactions.total_items} total
          </span>
        </div>
        <div className="dashboard-table dashboard-table--header">
          <span>Recent transactions</span>
          <span>Status</span>
          <span>Customer</span>
          <span>Amount</span>
          <span>Created</span>
        </div>
        {dashboard.transactions.transactions.length > 0 ? (
          dashboard.transactions.transactions.map((transaction) => (
            <div className="dashboard-table" key={transaction.reference}>
              <span>{transaction.reference}</span>
              <span>
                <span
                  className={`dashboard-status-chip ${
                    transaction.status === "success"
                      ? "dashboard-status-chip--success"
                      : transaction.status === "failed"
                        ? "dashboard-status-chip--failed"
                        : "dashboard-status-chip--pending"
                  }`}
                >
                  {transaction.status}
                </span>
              </span>
              <span>{transaction.customer?.email ?? "No customer email"}</span>
              <span>{formatCurrency(transaction.amount, transaction.currency)}</span>
              <time>{formatRelativeDateTime(transaction.created_at)}</time>
            </div>
          ))
        ) : (
          <div className="dashboard-table">
            <span>No transactions yet</span>
            <span>Pending</span>
            <span>Transactions will show here after your first collection or payout.</span>
            <span>{formatCurrency(0)}</span>
            <time>Waiting for activity</time>
          </div>
        )}
      </section>

      <section className="dashboard-split">
        <article className="dashboard-panel dashboard-panel--dark" id="dashboard-payment-links">
          <div className="dashboard-panel__header">
            <div>
              <p className="dashboard-panel__eyebrow">Payment links</p>
              <h3>Payment links</h3>
            </div>
            <div className="dashboard-app-actions">
              <button
                className="dashboard-inline-button"
                onClick={() =>
                  setPaymentLinkState((currentState) => ({
                    ...currentState,
                    open: !currentState.open,
                    error: null,
                    message: null,
                  }))
                }
                type="button"
              >
                {paymentLinkState.open ? "Close form" : "Create link"}
              </button>
              <a
                className="inline-link"
                href={docsHref("/collections")}
                rel={DOCS_LINK_REL}
                target={DOCS_LINK_TARGET}
              >
                Endpoint guide
              </a>
            </div>
          </div>
          {paymentLinkState.open ? (
            <form
              className="dashboard-control-form dashboard-control-card dashboard-payment-link-form"
              onSubmit={(event) => void handleCreatePaymentLink(event)}
            >
              <label className="auth-field">
                <span className="dashboard-control-label">Title</span>
                <input
                  className="dashboard-control-input"
                  name="title"
                  placeholder="Deposit"
                  required
                  type="text"
                />
              </label>
              <label className="auth-field">
                <span className="dashboard-control-label">Amount</span>
                <input
                  className="dashboard-control-input"
                  inputMode="decimal"
                  min="1"
                  name="amount"
                  placeholder="2500"
                  required
                  step="0.01"
                  type="number"
                />
              </label>
              <label className="auth-field">
                <span className="dashboard-control-label">Gateway</span>
                <select className="dashboard-control-input" name="gateway_code">
                  <option value="">Automatic</option>
                  <option value="kora">Kora</option>
                  <option value="pstk">Paystack</option>
                  <option value="fltw">Flutterwave</option>
                  <option value="isw">Interswitch</option>
                </select>
              </label>
              <div className="dashboard-control-actions">
                <PushButton disabled={paymentLinkState.submitting} type="submit">
                  {paymentLinkState.submitting ? "Saving..." : "Save payment link"}
                </PushButton>
              </div>
              {paymentLinkState.error ? (
                <p className="dashboard-control-feedback">{paymentLinkState.error}</p>
              ) : null}
            </form>
          ) : null}
          {paymentLinkState.message ? (
            <p className="dashboard-control-feedback">{paymentLinkState.message}</p>
          ) : null}
          <div className="dashboard-feed">
            {dashboard.payment_links.length > 0 ? (
              dashboard.payment_links.map((paymentLink) => (
                <article className="dashboard-feed__item" key={paymentLink.reference}>
                  <div className="dashboard-card__topline">
                    <div>
                      <p className="dashboard-feed__eyebrow">{paymentLink.reference}</p>
                      <strong>{paymentLink.title}</strong>
                    </div>
                    <span
                      className={`dashboard-status-pill ${
                        paymentLink.is_active
                          ? "dashboard-status-pill--closed"
                          : "dashboard-status-pill--maintenance"
                      }`}
                    >
                      {paymentLink.is_active ? "active" : "inactive"}
                    </span>
                  </div>
                  <p>
                    {paymentLink.amount
                      ? `${formatCurrency(paymentLink.amount, paymentLink.currency)} - ${paymentLink.current_uses} uses`
                      : `${paymentLink.current_uses} uses so far`}
                  </p>
                  <div className="dashboard-card__meta">
                    <span>{getGatewayDisplayName(paymentLink.gateway_code)}</span>
                    <span>{paymentLink.mode}</span>
                  </div>
                </article>
              ))
            ) : (
              <p className="dashboard-feed__empty">
                You have not created any payment links yet.
              </p>
            )}
          </div>
        </article>

        <article className="dashboard-panel">
          <div className="dashboard-panel__header">
            <div>
              <p className="dashboard-panel__eyebrow">Performance snapshot</p>
              <h3>Mode summary</h3>
            </div>
            <button
              className="dashboard-inline-button"
              onClick={() => setRefreshKey((currentValue) => currentValue + 1)}
              type="button"
            >
              Refresh
            </button>
          </div>
          <dl className="dashboard-stat-list">
            <div>
              <dt>Net revenue</dt>
              <dd>
                {formatCurrency(
                  dashboard.summary?.revenue_metrics.net_revenue ?? 0,
                  dashboard.summary?.top_currency?.currency ?? "NGN",
                )}
              </dd>
            </div>
            <div>
              <dt>Average ticket</dt>
              <dd>
                {formatCurrency(
                  dashboard.summary?.revenue_metrics.average_transaction_value ?? 0,
                  dashboard.summary?.top_currency?.currency ?? "NGN",
                )}
              </dd>
            </div>
            <div>
              <dt>Pending payouts</dt>
              <dd>{dashboard.summary?.pending_payouts ?? 0}</dd>
            </div>
            <div>
              <dt>Top currency</dt>
              <dd>{dashboard.summary?.top_currency?.currency ?? "NGN"}</dd>
            </div>
          </dl>
        </article>
      </section>
    </OpsShell>
  );
}
