const MARQUEE_COPY = [
  "Fast checkout",
  "Live payouts",
  "Clear webhooks",
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
        <h2 className="feature-block__title">Everything you need. Nothing you don&apos;t.</h2>
        <p className="feature-block__summary">
          Keep checkout, payouts, and payment updates in one clean system.
        </p>
      </div>

      <div className="feature-block__grid">
        <article className="poster-panel poster-panel--ink poster-panel--hero">
          <span aria-hidden="true" className="poster-panel__gridline" />
          <p className="poster-panel__eyebrow">Hosted collections</p>
          <h3 className="poster-panel__title">
            One checkout link. Customers choose how they pay.
          </h3>
          <p className="poster-panel__copy">
            Start one payment and let RouteX return the checkout link for the customer.
          </p>
          <div className="poster-panel__pillars">
            <div className="poster-pillar">
              <strong>Smart routing</strong>
              <span>Send one request and RouteX picks the best path.</span>
            </div>
            <div className="poster-pillar">
              <strong>Webhook updates</strong>
              <span>Your app gets one clear payment update.</span>
            </div>
            <div className="poster-pillar">
              <strong>Manual control</strong>
              <span>Pick a gateway only when you really need to.</span>
            </div>
          </div>
        </article>

        <div className="poster-panel__stack">
          <article className="poster-panel">
            <p className="poster-panel__eyebrow">Payment updates</p>
            <h3 className="poster-panel__title">Know what happened, fast.</h3>
            <p className="poster-panel__copy">
              RouteX confirms the provider result, then sends your app a simple signed webhook.
            </p>
            <span className="poster-panel__meta">Header: X-AGGREGATOR-SIGNATURE</span>
          </article>

          <article className="poster-panel poster-panel--acid">
            <p className="poster-panel__eyebrow">Payouts</p>
            <h3 className="poster-panel__title">Run payouts from one place.</h3>
            <p className="poster-panel__copy">
              Keep balances, payment links, transactions, and payouts in one dashboard.
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
            Run payments from one clean stack.
          </h2>
          <p className="feature-block__summary feature-block__summary--dark">
            Simple enough for fast teams. Strong enough for live money movement.
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
