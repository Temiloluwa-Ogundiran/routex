const FEATURES = [
  {
    eyebrow: "Collections",
    title: "Unified checkouts",
    body: "Launch one payment endpoint, keep your redirect URL, and let RouteX handle provider-specific payloads behind the scenes.",
    variant: "wide",
  },
  {
    eyebrow: "Observability",
    title: "Real-time decisions",
    body: "See which gateway won, why it won, and how failovers recover revenue before customers feel the drop.",
    variant: "tall",
  },
  {
    eyebrow: "Payouts",
    title: "Merchant wallets",
    body: "Track test and live balances, payout requests, and API keys from one calmer control surface.",
    variant: "compact",
  },
  {
    eyebrow: "Webhooks",
    title: "Clean merchant updates",
    body: "Receive normalized merchant webhooks after RouteX verifies the provider event and signs the payload for you.",
    variant: "wide-dark",
  },
];

export function FeatureGrid() {
  return (
    <section className="story-section story-section--dark liquid-feature-section" id="platform">
      <div className="section-heading liquid-feature-heading">
        <p className="section-kicker">Features</p>
        <h2>
          Everything you need.
          <span> Nothing you don&apos;t.</span>
        </h2>
        <p>
          A premium orchestration layer for merchants who want speed, clarity,
          and reliable money movement without juggling gateway dashboards.
        </p>
      </div>

      <div className="feature-grid liquid-feature-grid">
        {FEATURES.map((feature, index) => (
          <article
            className={`feature-card liquid-feature-card liquid-feature-card--${feature.variant}`}
            key={feature.title}
          >
            <div className="liquid-feature-card__icon">{index + 1}</div>
            <p className="liquid-feature-card__eyebrow">{feature.eyebrow}</p>
            <h3>{feature.title}</h3>
            <p>{feature.body}</p>
            <span aria-hidden="true" className="liquid-feature-card__arrow">
              ›
            </span>
          </article>
        ))}
      </div>
    </section>
  );
}
