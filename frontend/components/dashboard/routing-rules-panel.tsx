"use client";

import { useState } from "react";

import type {
  RouterRule,
} from "../../lib/dashboard-api";
import { PushButton } from "../ui/push-button";

type RoutingRulesPanelProps = {
  rules: RouterRule[];
  onRuleCreated: (rule: RouterRule) => void;
  onRuleUpdated: (rule: RouterRule) => void;
};

type RuleMutationResponse =
  | {
      rule: RouterRule;
    }
  | {
      detail?: string;
    };

function parseGatewayCodes(value: string) {
  return value
    .split(",")
    .map((code) => code.trim().toLowerCase())
    .filter((code) => code.length > 0);
}

function parseOptionalAmount(value: string) {
  if (!value.trim()) {
    return null;
  }

  const parsedValue = Number.parseFloat(value);
  return Number.isFinite(parsedValue) ? parsedValue : Number.NaN;
}

function formatAmountRange(rule: RouterRule) {
  if (rule.min_amount === null && rule.max_amount === null) {
    return "Any amount";
  }

  if (rule.min_amount !== null && rule.max_amount !== null) {
    return `NGN ${rule.min_amount.toLocaleString("en-NG")} to ${rule.max_amount.toLocaleString("en-NG")}`;
  }

  if (rule.min_amount !== null) {
    return `NGN ${rule.min_amount.toLocaleString("en-NG")}+`;
  }

  return `Up to NGN ${rule.max_amount?.toLocaleString("en-NG")}`;
}

function RulePill({
  label,
  tone = "default",
}: {
  label: string;
  tone?: "default" | "accent";
}) {
  return (
    <span
      className={`routing-rule-pill${
        tone === "accent" ? " routing-rule-pill--accent" : ""
      }`}
    >
      {label}
    </span>
  );
}

export function RoutingRulesPanel({
  rules,
  onRuleCreated,
  onRuleUpdated,
}: RoutingRulesPanelProps) {
  const [name, setName] = useState("");
  const [operation, setOperation] = useState("collection");
  const [channel, setChannel] = useState("");
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");
  const [allowGateways, setAllowGateways] = useState("");
  const [denyGateways, setDenyGateways] = useState("");
  const [forcedOrder, setForcedOrder] = useState("");
  const [enabledByDefault, setEnabledByDefault] = useState(true);
  const [feedback, setFeedback] = useState(
    "Create a global rule to narrow or reorder gateway selection before scoring.",
  );
  const [pendingCreate, setPendingCreate] = useState(false);
  const [pendingRuleId, setPendingRuleId] = useState<number | null>(null);

  const activeRuleCount = rules.filter((rule) => rule.enabled).length;

  function resetForm() {
    setName("");
    setOperation("collection");
    setChannel("");
    setMinAmount("");
    setMaxAmount("");
    setAllowGateways("");
    setDenyGateways("");
    setForcedOrder("");
    setEnabledByDefault(true);
  }

  async function handleCreateRule() {
    const normalizedName = name.trim();
    if (!normalizedName) {
      setFeedback("Rule name is required.");
      return;
    }

    const parsedMinAmount = parseOptionalAmount(minAmount);
    const parsedMaxAmount = parseOptionalAmount(maxAmount);
    if (
      Number.isNaN(parsedMinAmount) ||
      Number.isNaN(parsedMaxAmount)
    ) {
      setFeedback("Enter valid numeric amounts or leave them blank.");
      return;
    }

    if (
      parsedMinAmount !== null &&
      parsedMaxAmount !== null &&
      parsedMinAmount > parsedMaxAmount
    ) {
      setFeedback("Minimum amount cannot be greater than maximum amount.");
      return;
    }

    setPendingCreate(true);
    setFeedback("Saving routing rule...");

    try {
      const response = await fetch("/api/admin/router/rules", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: normalizedName,
          operation,
          channel: channel.trim() || null,
          min_amount: parsedMinAmount,
          max_amount: parsedMaxAmount,
          allow_gateways: parseGatewayCodes(allowGateways),
          deny_gateways: parseGatewayCodes(denyGateways),
          force_priority_order: parseGatewayCodes(forcedOrder),
          enabled: enabledByDefault,
        }),
      });

      const payload = (await response.json()) as RuleMutationResponse;
      if (!response.ok || !("rule" in payload)) {
        setFeedback(
          "detail" in payload && payload.detail
            ? payload.detail
            : "Unable to create routing rule right now.",
        );
        return;
      }

      onRuleCreated(payload.rule);
      resetForm();
      setFeedback("Routing rule saved successfully.");
    } catch {
      setFeedback("Unable to create routing rule right now.");
    } finally {
      setPendingCreate(false);
    }
  }

  async function handleToggleRule(rule: RouterRule) {
    setPendingRuleId(rule.id);
    setFeedback(`${rule.enabled ? "Pausing" : "Enabling"} ${rule.name}...`);

    try {
      const response = await fetch(`/api/admin/router/rules/${rule.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          enabled: !rule.enabled,
        }),
      });

      const payload = (await response.json()) as RuleMutationResponse;
      if (!response.ok || !("rule" in payload)) {
        setFeedback(
          "detail" in payload && payload.detail
            ? payload.detail
            : "Unable to update routing rule right now.",
        );
        return;
      }

      onRuleUpdated(payload.rule);
      setFeedback(`${payload.rule.name} updated successfully.`);
    } catch {
      setFeedback("Unable to update routing rule right now.");
    } finally {
      setPendingRuleId(null);
    }
  }

  return (
    <section className="dashboard-section" id="dashboard-rules">
      <div className="section-heading section-heading--split">
        <div>
          <p className="section-kicker">Routing Policy Layer</p>
          <h2>Routing Rules</h2>
        </div>
        <p className="inline-link">
          {activeRuleCount} active rules. Live admin changes proxy safely through the backend.
        </p>
      </div>

      <div className="routing-rules-layout">
        <article className="dashboard-control-card routing-rules-form-card">
            <div className="dashboard-card__topline">
              <div>
                <p className="dashboard-card__eyebrow">Create Rule</p>
                <h3>Shape eligibility before routing</h3>
              </div>
            <span className="dashboard-status-pill dashboard-status-pill--accent">
              Global only
            </span>
          </div>

          <div className="routing-rules-form-grid">
            <div className="dashboard-control-form">
              <label className="dashboard-control-label" htmlFor="routing-rule-name">
                Rule name
              </label>
              <input
                aria-label="Rule name"
                className="dashboard-control-input"
                id="routing-rule-name"
                onChange={(event) => setName(event.target.value)}
                type="text"
                value={name}
              />
            </div>

            <div className="dashboard-control-form">
              <label className="dashboard-control-label" htmlFor="routing-rule-operation">
                Operation
              </label>
              <select
                aria-label="Operation"
                className="dashboard-control-input"
                id="routing-rule-operation"
                onChange={(event) => setOperation(event.target.value)}
                value={operation}
              >
                <option value="collection">collection</option>
                <option value="payout">payout</option>
              </select>
            </div>

            <div className="dashboard-control-form">
              <label className="dashboard-control-label" htmlFor="routing-rule-channel">
                Channel
              </label>
              <input
                aria-label="Channel"
                className="dashboard-control-input"
                id="routing-rule-channel"
                onChange={(event) => setChannel(event.target.value)}
                placeholder="card"
                type="text"
                value={channel}
              />
            </div>

            <div className="dashboard-control-form">
              <label className="dashboard-control-label" htmlFor="routing-rule-minimum">
                Minimum amount
              </label>
              <input
                aria-label="Minimum amount"
                className="dashboard-control-input"
                id="routing-rule-minimum"
                min="0"
                onChange={(event) => setMinAmount(event.target.value)}
                step="0.01"
                type="number"
                value={minAmount}
              />
            </div>

            <div className="dashboard-control-form">
              <label className="dashboard-control-label" htmlFor="routing-rule-maximum">
                Maximum amount
              </label>
              <input
                aria-label="Maximum amount"
                className="dashboard-control-input"
                id="routing-rule-maximum"
                min="0"
                onChange={(event) => setMaxAmount(event.target.value)}
                step="0.01"
                type="number"
                value={maxAmount}
              />
            </div>

            <div className="dashboard-control-form">
              <label className="dashboard-control-label" htmlFor="routing-rule-allow">
                Allow gateways
              </label>
              <input
                aria-label="Allow gateways"
                className="dashboard-control-input"
                id="routing-rule-allow"
                onChange={(event) => setAllowGateways(event.target.value)}
                placeholder="fltw,pstk"
                type="text"
                value={allowGateways}
              />
            </div>

            <div className="dashboard-control-form">
              <label className="dashboard-control-label" htmlFor="routing-rule-deny">
                Deny gateways
              </label>
              <input
                aria-label="Deny gateways"
                className="dashboard-control-input"
                id="routing-rule-deny"
                onChange={(event) => setDenyGateways(event.target.value)}
                placeholder="kora,isw"
                type="text"
                value={denyGateways}
              />
            </div>

            <div className="dashboard-control-form">
              <label className="dashboard-control-label" htmlFor="routing-rule-forced-order">
                Forced order
              </label>
              <input
                aria-label="Forced order"
                className="dashboard-control-input"
                id="routing-rule-forced-order"
                onChange={(event) => setForcedOrder(event.target.value)}
                placeholder="fltw,pstk"
                type="text"
                value={forcedOrder}
              />
            </div>
          </div>

          <label className="routing-rules-checkbox">
            <input
              checked={enabledByDefault}
              onChange={(event) => setEnabledByDefault(event.target.checked)}
              type="checkbox"
            />
            Start this rule enabled
          </label>

          <div className="dashboard-control-actions">
            <PushButton
              disabled={pendingCreate}
              onClick={() => void handleCreateRule()}
              type="button"
            >
              Create Rule
            </PushButton>
          </div>

          <p className="dashboard-control-feedback">{feedback}</p>
        </article>

        <div className="routing-rules-list">
          {rules.map((rule) => {
            const isPending = pendingRuleId === rule.id;

            return (
              <article className="routing-rule-card" key={rule.id}>
                <div className="dashboard-card__topline">
                  <div>
                    <p className="dashboard-card__eyebrow">Rule #{rule.id}</p>
                    <h3>{rule.name}</h3>
                  </div>
                  <span
                    className={`dashboard-status-pill dashboard-status-pill--${
                      rule.enabled ? "closed" : "maintenance"
                    }`}
                  >
                    {rule.enabled ? "Enabled" : "Paused"}
                  </span>
                </div>

                <div className="routing-rule-pill-row">
                  <RulePill label={rule.operation} tone="accent" />
                  <RulePill label={rule.channel ?? "all channels"} />
                  <RulePill label={formatAmountRange(rule)} />
                </div>

                <dl className="routing-rule-meta">
                  <div>
                    <dt>Allow</dt>
                    <dd>
                      {rule.allow_gateways.length > 0
                        ? rule.allow_gateways.join(", ")
                        : "All eligible gateways"}
                    </dd>
                  </div>
                  <div>
                    <dt>Deny</dt>
                    <dd>
                      {rule.deny_gateways.length > 0
                        ? rule.deny_gateways.join(", ")
                        : "None"}
                    </dd>
                  </div>
                  <div>
                    <dt>Forced order</dt>
                    <dd>
                      {rule.force_priority_order.length > 0
                        ? rule.force_priority_order.join(" -> ")
                        : "Score-driven"}
                    </dd>
                  </div>
                  <div>
                    <dt>Updated</dt>
                    <dd>
                      {new Date(rule.updated_at).toLocaleTimeString("en-NG", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </dd>
                  </div>
                </dl>

                <div className="routing-rule-actions">
                  <PushButton
                    disabled={isPending}
                    onClick={() => void handleToggleRule(rule)}
                    type="button"
                    variant={rule.enabled ? "secondary" : "primary"}
                  >
                    {rule.enabled ? "Pause" : "Enable"} {rule.name}
                  </PushButton>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
