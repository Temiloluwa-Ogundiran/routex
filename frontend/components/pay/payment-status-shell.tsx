"use client";

import { useEffect, useState } from "react";
import { docsHref } from "../../lib/docs-url";

type PaymentStatus = "success" | "pending" | "failed";

type PaymentStatusShellProps = {
  gatewayReference: string;
  nextDestination: string | null;
  reference: string;
  selectedGateway: string | null;
  status: PaymentStatus;
};

const STATUS_COPY: Record<
  PaymentStatus,
  {
    badge: string;
    heading: string;
    body: string;
    detail: string;
  }
> = {
  success: {
    badge: "Verified",
    heading: "Payment confirmed",
    body: "RouteX verified your payment and updated the transaction status.",
    detail: "You can safely continue back to the merchant app.",
  },
  pending: {
    badge: "Reconciling",
    heading: "Payment pending",
    body: "We received the provider return and we are still confirming the final payment outcome.",
    detail: "You can continue now, or wait for the merchant app to refresh the status.",
  },
  failed: {
    badge: "Needs attention",
    heading: "Payment failed",
    body: "The payment could not be confirmed as successful from the provider return flow.",
    detail: "You can head back to the merchant app to retry or choose another payment option.",
  },
};

const GATEWAY_LABELS: Record<string, string> = {
  fltw: "Flutterwave",
  isw: "Interswitch",
  kora: "Korapay",
  pstk: "Paystack",
};

function getGatewayLabel(selectedGateway: string | null): string {
  if (!selectedGateway) {
    return "Routed Gateway";
  }
  return GATEWAY_LABELS[selectedGateway] ?? selectedGateway.toUpperCase();
}

function isSafeNextDestination(nextDestination: string | null): nextDestination is string {
  if (!nextDestination) {
    return false;
  }
  return (
    nextDestination.startsWith("/") ||
    nextDestination.startsWith("http://") ||
    nextDestination.startsWith("https://")
  );
}

function getAutoForwardDelay(status: PaymentStatus, nextDestination: string | null): number | null {
  if (!isSafeNextDestination(nextDestination)) {
    return null;
  }
  if (status === "success") {
    return 3;
  }
  if (status === "failed") {
    return 5;
  }
  return null;
}

export function PaymentStatusShell({
  gatewayReference,
  nextDestination,
  reference,
  selectedGateway,
  status,
}: PaymentStatusShellProps) {
  const autoForwardDelay = getAutoForwardDelay(status, nextDestination);
  const [secondsRemaining, setSecondsRemaining] = useState(autoForwardDelay);
  const copy = STATUS_COPY[status];
  const continueHref = isSafeNextDestination(nextDestination) ? nextDestination : null;
  const gatewayLabel = getGatewayLabel(selectedGateway);

  useEffect(() => {
    setSecondsRemaining(autoForwardDelay);
  }, [autoForwardDelay]);

  useEffect(() => {
    if (!autoForwardDelay || !isSafeNextDestination(nextDestination)) {
      return undefined;
    }

    setSecondsRemaining(autoForwardDelay);
    let remaining = autoForwardDelay;

    const intervalId = window.setInterval(() => {
      remaining -= 1;
      setSecondsRemaining(Math.max(remaining, 0));

      if (remaining <= 0) {
        window.clearInterval(intervalId);
        window.location.assign(nextDestination);
      }
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, [autoForwardDelay, nextDestination]);

  return (
    <section className={`payment-status-panel payment-status-panel--${status}`}>
      <div className="payment-status-card">
        <span className={`payment-status-badge payment-status-badge--${status}`}>
          {copy.badge}
        </span>
        <h1>{copy.heading}</h1>
        <p className="payment-status-lead">{copy.body}</p>
        <p className="payment-status-detail">{copy.detail}</p>

        <div className="payment-status-actions">
          {continueHref ? (
            <a className="push-button push-button--primary" href={continueHref}>
              Continue to merchant
            </a>
          ) : null}
          <a className="push-button push-button--secondary" href={docsHref()}>
            View API reference
          </a>
        </div>

        {secondsRemaining !== null ? (
          <p className="payment-status-countdown">
            Redirecting you in {secondsRemaining} second
            {secondsRemaining === 1 ? "" : "s"}.
          </p>
        ) : continueHref ? (
          <p className="payment-status-countdown">
            Continue when you are ready. We will not redirect you automatically
            while the payment is still pending.
          </p>
        ) : (
          <p className="payment-status-countdown">
            Share the transaction reference with the merchant if you need support.
          </p>
        )}
      </div>

      <aside className="payment-status-summary" aria-label="Payment summary">
        <div>
          <p className="payment-status-summary__label">Reference</p>
          <strong>{reference}</strong>
        </div>
        <div>
          <p className="payment-status-summary__label">Gateway</p>
          <strong>{gatewayLabel}</strong>
        </div>
        <div>
          <p className="payment-status-summary__label">Gateway reference</p>
          <strong>{gatewayReference}</strong>
        </div>
        <div>
          <p className="payment-status-summary__label">Status</p>
          <strong>{status}</strong>
        </div>
      </aside>
    </section>
  );
}
