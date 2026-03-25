const PROOF_CARDS = [
  {
    title: "4 Gateways. 1 API.",
    body: "Paystack, Flutterwave, Korapay, and Interswitch sit behind one integration surface.",
  },
  {
    title: "Collections + Payouts",
    body: "Handle inbound payments and outbound disbursements without separate orchestration tooling.",
  },
  {
    title: "Routing Visibility",
    body: "Surface gateway health, failover events, and selected paths in a demo-ready dashboard.",
  },
];

export function ProofSection() {
  return (
    <section className="story-section story-section--sage">
      <div className="section-heading section-heading--centered">
        <h2>BUILT TO SHOW ITS WORK.</h2>
        <p>
          RouteX is designed to make routing decisions visible, not mysterious.
        </p>
      </div>

      <div className="proof-grid">
        {PROOF_CARDS.map((card) => (
          <article className="proof-card" key={card.title}>
            <p className="proof-card__eyebrow">RouteX proof</p>
            <h3>{card.title}</h3>
            <p>{card.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
