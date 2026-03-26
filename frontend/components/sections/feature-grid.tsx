import { SectionBadge } from "../ui/section-badge";

const FEATURES = [
  {
    title: "Smart Routing",
    body: "Scores eligible gateways in real time using health, latency, and recent success signals.",
  },
  {
    title: "Automatic Failover",
    body: "Reroutes safe collection attempts when the first gateway path degrades or times out.",
  },
  {
    title: "Unified Payouts",
    body: "Use one payout surface with merchant wallets, provider selection, and clear payout tracking.",
  },
  {
    title: "Routing Analytics",
    body: "Track gateway health, selected paths, recovered transactions, and failover trends in one view.",
  },
  {
    title: "Unified Updates",
    body: "Keep payment status changes consistent across providers with one clean update flow.",
  },
  {
    title: "Sandbox-First API",
    body: "Test initiate, verify, and payout flows in test mode before moving into production setup.",
  },
];

export function FeatureGrid() {
  return (
    <section className="story-section story-section--yellow" id="features">
      <div className="section-heading section-heading--centered">
        <SectionBadge>Features</SectionBadge>
        <h2>EVERYTHING YOU NEED.</h2>
        <p>No fluff. Just the payment routing tools teams actually need.</p>
      </div>

      <div className="feature-grid">
        {FEATURES.map((feature, index) => (
          <article className="feature-card" key={feature.title}>
            <div className="feature-card__icon">{index + 1}</div>
            <h3>{feature.title}</h3>
            <p>{feature.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
