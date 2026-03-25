import type { RouterGatewayHealth } from "../../lib/dashboard-api";

type GatewayHealthGridProps = {
  gateways: RouterGatewayHealth[];
};

export function GatewayHealthGrid({ gateways }: GatewayHealthGridProps) {
  return (
    <section className="dashboard-section" id="dashboard-gateways">
      <div className="section-heading section-heading--split">
        <div>
          <p className="section-kicker">Live Routing Signals</p>
          <h2>Gateway Health</h2>
        </div>
        <p className="inline-link">Auto-sorted by priority and freshness.</p>
      </div>

      <div className="dashboard-card-grid">
        {gateways.map((gateway) => (
          <article
            aria-label={`Gateway health for ${gateway.gateway_name}`}
            className="dashboard-card"
            key={gateway.gateway_code}
          >
            <div className="dashboard-card__topline">
              <div>
                <p className="dashboard-card__eyebrow">{gateway.gateway_code}</p>
                <h3>{gateway.gateway_name}</h3>
              </div>
              <span
                className={`dashboard-status-pill dashboard-status-pill--${gateway.circuit_state.toLowerCase()}`}
              >
                {gateway.circuit_state}
              </span>
            </div>

            <dl className="dashboard-stat-list">
              <div>
                <dt>Success 5m</dt>
                <dd>{gateway.success_rate_5m.toFixed(1)}%</dd>
              </div>
              <div>
                <dt>Latency</dt>
                <dd>{Math.round(gateway.p95_latency_ms)}ms</dd>
              </div>
              <div>
                <dt>Timeouts</dt>
                <dd>{gateway.timeout_rate_5m.toFixed(1)}%</dd>
              </div>
              <div>
                <dt>Weight</dt>
                <dd>{gateway.priority_weight.toFixed(2)}</dd>
              </div>
            </dl>

            <div className="dashboard-card__meta">
              <span>{gateway.supports_collections ? "Collections" : "No collections"}</span>
              <span>{gateway.supports_payouts ? "Payouts" : "No payouts"}</span>
              <span>{gateway.is_active ? "Active" : "Paused"}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
