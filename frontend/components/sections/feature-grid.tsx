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
        <h2 className="feature-block__title">Simple to start. Strong when you grow.</h2>
        <p className="feature-block__summary">
          Take payments, send payouts, and follow every result in one place.
        </p>
      </div>

      <div className="feature-block__grid">
        <article className="poster-panel poster-panel--ink poster-panel--hero">
          <span aria-hidden="true" className="poster-panel__gridline" />
          <p className="poster-panel__eyebrow">Hosted collections</p>
          <h3 className="poster-panel__title">One payment link. More ways to pay.</h3>
          <p className="poster-panel__copy">
            Start one payment and RouteX returns the checkout page for your customer.
          </p>
          <div className="poster-panel__pillars">
            <div className="poster-pillar">
              <strong>Smart routing</strong>
              <span>RouteX picks the best gateway in real time.</span>
            </div>
            <div className="poster-pillar">
              <strong>Signed updates</strong>
              <span>Your app gets one clear webhook when the status changes.</span>
            </div>
            <div className="poster-pillar">
              <strong>Manual control</strong>
              <span>Choose a gateway yourself when you need to.</span>
            </div>
          </div>
        </article>

        <div className="poster-panel__stack">
          <article className="poster-panel">
            <p className="poster-panel__eyebrow">Payment updates</p>
            <h3 className="poster-panel__title">Know what happened.</h3>
            <p className="poster-panel__copy">
              RouteX checks the provider result, then sends your app one signed update.
            </p>
            <span className="poster-panel__meta">Header: X-AGGREGATOR-SIGNATURE</span>
          </article>

          <article className="poster-panel poster-panel--acid">
            <p className="poster-panel__eyebrow">Payouts</p>
            <h3 className="poster-panel__title">Run payouts from one place.</h3>
            <p className="poster-panel__copy">
              Keep balances, payment links, transactions, and payouts in one clean dashboard.
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
            Everything you need to get paid.
          </h2>
          <p className="feature-block__summary feature-block__summary--dark">
            Easy to understand. Ready for live money.
          </p>
        </div>

        <div className="benefit-grid">
          <article className="benefit-card">
            <span className="benefit-card__icon">01</span>
            <h3>Hosted collections</h3>
            <p>Share one checkout link instead of building one flow per provider.</p>
          </article>

          <article className="benefit-card">
            <span className="benefit-card__icon">02</span>
            <h3>Clear updates</h3>
            <p>Get a signed payment update after RouteX confirms the transaction.</p>
          </article>

          <article className="benefit-card">
            <span className="benefit-card__icon">03</span>
            <h3>Payout control</h3>
            <p>Handle outgoing payments, balances, and history from one dashboard.</p>
          </article>
        </div>
      </section>
    </section>
  );
}
