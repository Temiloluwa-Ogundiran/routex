const MARQUEE_COPY = [
  "Fast checkout",
  "Clear updates",
  "Easy payouts",
  "Smart routing",
];

export function FeatureGrid() {
  return (
    <section className="feature-block" id="route">
      <div aria-hidden="true" className="acid-marquee">
        <div className="acid-marquee__track">
          {[...MARQUEE_COPY, ...MARQUEE_COPY].map((item, index) => (
            <span key={`${item}-${index}`}>{item}</span>
          ))}
        </div>
      </div>

      <div className="feature-block__header">
        <p className="feature-block__eyebrow">Why teams choose RouteX</p>
        <h2 className="feature-block__title">Simple to start. Easy to trust.</h2>
        <p className="feature-block__summary">
          Accept payments, track what happened, and manage your balance from one place.
        </p>
      </div>

      <div className="feature-block__grid">
        <article className="poster-panel poster-panel--ink poster-panel--hero">
          <span aria-hidden="true" className="poster-panel__gridline" />
          <p className="poster-panel__eyebrow">Hosted collections</p>
          <h3 className="poster-panel__title">One checkout. More ways to pay.</h3>
          <p className="poster-panel__copy">
            Start one payment and send your customer straight to checkout.
          </p>
          <div className="poster-panel__pillars">
            <div className="poster-pillar">
              <strong>Best route</strong>
              <span>RouteX picks the healthiest gateway for the job.</span>
            </div>
            <div className="poster-pillar">
              <strong>Clear update</strong>
              <span>Your app gets one signed webhook after the result is confirmed.</span>
            </div>
            <div className="poster-pillar">
              <strong>Your choice</strong>
              <span>Pick a gateway yourself when you want full control.</span>
            </div>
          </div>
        </article>

        <div className="poster-panel__stack">
          <article className="poster-panel poster-panel--acid">
            <p className="poster-panel__eyebrow">Payouts</p>
            <h3 className="poster-panel__title">Manage payouts from one place.</h3>
            <p className="poster-panel__copy">
              Review balances, transactions, and outgoing payments in one clean workspace.
            </p>
          </article>
        </div>
      </div>

      <section className="feature-block__lower" aria-labelledby="built-to-ship-hard">
        <div className="feature-block__lower-copy">
          <p className="feature-block__eyebrow">What you get</p>
          <h2
            className="feature-block__title feature-block__title--compact"
            id="built-to-ship-hard"
          >
            What RouteX helps you do.
          </h2>
          <p className="feature-block__summary feature-block__summary--dark">
            Simple enough for any business team to understand.
          </p>
        </div>

        <div className="benefit-grid">
          <article className="benefit-card">
            <span className="benefit-card__icon">01</span>
            <h3>Collect money</h3>
            <p>Use one checkout instead of building one flow for every gateway.</p>
          </article>

          <article className="benefit-card">
            <span className="benefit-card__icon">02</span>
            <h3>Stay updated</h3>
            <p>Know when a payment succeeds, fails, or is still pending.</p>
          </article>

          <article className="benefit-card">
            <span className="benefit-card__icon">03</span>
            <h3>Control your balance</h3>
            <p>Manage payouts, balances, and history from one dashboard.</p>
          </article>
        </div>
      </section>
    </section>
  );
}
