import type { RouterGatewayHealth } from "../../lib/dashboard-api";

type ScoreBreakdownCardProps = {
  gateways: RouterGatewayHealth[];
};

function computeSignalScore(gateway: RouterGatewayHealth) {
  return Math.round(
    gateway.success_rate_5m * 0.45 +
      gateway.success_rate_1h * 0.2 +
      Math.max(0, 100 - gateway.p95_latency_ms / 50) * 0.2 +
      (gateway.circuit_state.toLowerCase() === "closed" ? 100 : 0) * 0.1 +
      Math.max(0, 100 - gateway.timeout_rate_5m * 10) * 0.05,
  );
}

export function ScoreBreakdownCard({ gateways }: ScoreBreakdownCardProps) {
  const rankedSignals = [...gateways]
    .filter((gateway) => gateway.is_active)
    .map((gateway) => ({
      gateway,
      score: computeSignalScore(gateway),
    }))
    .sort((left, right) => right.score - left.score);

  return (
    <section className="dashboard-panel">
      <div className="dashboard-panel__header">
        <div>
          <p className="dashboard-panel__eyebrow">Explainability</p>
          <h3>Score Breakdown</h3>
        </div>
        <span className="dashboard-status-pill dashboard-status-pill--accent">
          live signals
        </span>
      </div>

      <div className="dashboard-score-list">
        {rankedSignals.map(({ gateway, score }) => (
          <div className="dashboard-score-row" key={gateway.gateway_code}>
            <div>
              <strong>{gateway.gateway_name}</strong>
              <p>
                {gateway.success_rate_5m.toFixed(1)}% success,{" "}
                {Math.round(gateway.p95_latency_ms)}ms p95
              </p>
            </div>
            <div className="dashboard-score-bar">
              <span style={{ width: `${score}%` }} />
              <strong>{score}</strong>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
