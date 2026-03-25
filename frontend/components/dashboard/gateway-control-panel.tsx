"use client";

import { useState } from "react";

import type {
  RouterGatewayControlPayload,
  RouterGatewayControlResult,
  RouterGatewayHealth,
} from "../../lib/dashboard-api";
import { PushButton } from "../ui/push-button";

type GatewayControlPanelProps = {
  gateways: RouterGatewayHealth[];
  onGatewayUpdated: (gateway: RouterGatewayHealth) => void;
};

function buildWeightDrafts(gateways: RouterGatewayHealth[]) {
  return Object.fromEntries(
    gateways.map((gateway) => [
      gateway.gateway_code,
      gateway.priority_weight.toFixed(2),
    ]),
  );
}

export function GatewayControlPanel({
  gateways,
  onGatewayUpdated,
}: GatewayControlPanelProps) {
  const [weightDrafts, setWeightDrafts] = useState(() => buildWeightDrafts(gateways));
  const [pendingGatewayCode, setPendingGatewayCode] = useState<string | null>(null);
  const [messages, setMessages] = useState<Record<string, string>>({});

  function setMessage(gatewayCode: string, message: string) {
    setMessages((current) => ({
      ...current,
      [gatewayCode]: message,
    }));
  }

  async function patchGateway(
    gateway: RouterGatewayHealth,
    payload: RouterGatewayControlPayload,
  ) {
    setPendingGatewayCode(gateway.gateway_code);
    setMessage(gateway.gateway_code, "Saving...");

    try {
      const response = await fetch(
        `/api/admin/router/gateways/${gateway.gateway_code}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        },
      );

      const json = (await response.json()) as
        | RouterGatewayControlResult
        | { message?: string };

      if (!response.ok || !("gateway" in json)) {
        const errorMessage = "message" in json ? json.message : undefined;
        setMessage(
          gateway.gateway_code,
          errorMessage ?? "Unable to update the gateway right now.",
        );
        return;
      }

      const nextGateway: RouterGatewayHealth = {
        ...gateway,
        ...json.gateway,
      };

      setWeightDrafts((current) => ({
        ...current,
        [gateway.gateway_code]: nextGateway.priority_weight.toFixed(2),
      }));
      onGatewayUpdated(nextGateway);
      setMessage(gateway.gateway_code, "Gateway updated successfully.");
    } catch {
      setMessage(gateway.gateway_code, "Unable to update the gateway right now.");
    } finally {
      setPendingGatewayCode(null);
    }
  }

  async function handleToggle(gateway: RouterGatewayHealth) {
    const nextWeight = Number.parseFloat(weightDrafts[gateway.gateway_code] ?? "0");
    await patchGateway(gateway, {
      gateway_name: gateway.gateway_name,
      is_active: !gateway.is_active,
      priority_weight: Number.isFinite(nextWeight)
        ? nextWeight
        : gateway.priority_weight,
      supports_collections: gateway.supports_collections,
      supports_payouts: gateway.supports_payouts,
    });
  }

  async function handleSave(gateway: RouterGatewayHealth) {
    const nextWeight = Number.parseFloat(weightDrafts[gateway.gateway_code] ?? "");
    if (!Number.isFinite(nextWeight) || nextWeight < 0) {
      setMessage(gateway.gateway_code, "Enter a valid non-negative weight.");
      return;
    }

    await patchGateway(gateway, {
      gateway_name: gateway.gateway_name,
      is_active: gateway.is_active,
      priority_weight: nextWeight,
      supports_collections: gateway.supports_collections,
      supports_payouts: gateway.supports_payouts,
    });
  }

  return (
    <section className="dashboard-section">
      <div className="section-heading section-heading--split">
        <div>
          <p className="section-kicker">Manual Overrides</p>
          <h2>Gateway Controls</h2>
        </div>
        <p className="inline-link">
          Changes flow through the backend admin proxy.
        </p>
      </div>

      <div className="dashboard-control-grid">
        {gateways.map((gateway) => {
          const isPending = pendingGatewayCode === gateway.gateway_code;

          return (
            <article className="dashboard-control-card" key={gateway.gateway_code}>
              <div className="dashboard-card__topline">
                <div>
                  <p className="dashboard-card__eyebrow">{gateway.gateway_code}</p>
                  <h3>{gateway.gateway_name}</h3>
                </div>
                <span
                  className={`dashboard-status-pill dashboard-status-pill--${
                    gateway.is_active ? "closed" : "maintenance"
                  }`}
                >
                  {gateway.is_active ? "Active" : "Paused"}
                </span>
              </div>

              <div className="dashboard-control-form">
                <label
                  className="dashboard-control-label"
                  htmlFor={`gateway-weight-${gateway.gateway_code}`}
                >
                  Weight for {gateway.gateway_name}
                </label>
                <input
                  aria-label={`Weight for ${gateway.gateway_name}`}
                  className="dashboard-control-input"
                  id={`gateway-weight-${gateway.gateway_code}`}
                  min="0"
                  onChange={(event) =>
                    setWeightDrafts((current) => ({
                      ...current,
                      [gateway.gateway_code]: event.target.value,
                    }))
                  }
                  step="0.05"
                  type="number"
                  value={weightDrafts[gateway.gateway_code] ?? "0.00"}
                />
              </div>

              <div className="dashboard-control-actions">
                <PushButton
                  disabled={isPending}
                  onClick={() => void handleSave(gateway)}
                  type="button"
                  variant="secondary"
                >
                  Save {gateway.gateway_name}
                </PushButton>
                <PushButton
                  disabled={isPending}
                  onClick={() => void handleToggle(gateway)}
                  type="button"
                >
                  {gateway.is_active ? "Pause" : "Enable"} {gateway.gateway_name}
                </PushButton>
              </div>

              <p className="dashboard-control-feedback">
                {messages[gateway.gateway_code] ??
                  "Adjust routing weight or pause this gateway for new traffic."}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
