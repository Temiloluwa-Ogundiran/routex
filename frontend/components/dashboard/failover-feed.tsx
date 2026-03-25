import type { RouterFailover } from "../../lib/dashboard-api";

type FailoverFeedProps = {
  failovers: RouterFailover[];
};

export function FailoverFeed({ failovers }: FailoverFeedProps) {
  return (
    <section className="dashboard-panel dashboard-panel--dark">
      <div className="dashboard-panel__header">
        <div>
          <p className="dashboard-panel__eyebrow">Recovery Feed</p>
          <h3>Recent Failovers</h3>
        </div>
        <span className="dashboard-status-pill dashboard-status-pill--highlight">
          {failovers.length} events
        </span>
      </div>

      <div className="dashboard-feed">
        {failovers.length === 0 ? (
          <p className="dashboard-feed__empty">
            No failovers yet. The router is still watching every gateway lane.
          </p>
        ) : (
          failovers.map((failover) => (
            <article className="dashboard-feed__item" key={failover.reference}>
              <div>
                <p className="dashboard-feed__eyebrow">{failover.reference}</p>
                <strong>{failover.selected_gateway ?? "unassigned"} recovered the payment</strong>
              </div>
              <p>
                {failover.attempt_count} attempts. Fallback trail:{" "}
                {failover.fallback_order.join(" -> ")}
              </p>
            </article>
          ))
        )}
      </div>
    </section>
  );
}
