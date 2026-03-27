const MARQUEE_COPY = [
  "RouteX ships loud",
  "Checkout ready",
  "Signed webhooks",
  "Manual override",
  "Payout control",
  "Webhook relay",
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
        <p className="feature-block__eyebrow">Choose your route</p>
        <h2 className="feature-block__title">Choose your route</h2>
        <p className="feature-block__summary">
          Keep the merchant contract tight. RouteX handles hosted checkout,
          webhook relay, verification, payouts, and fallback routing behind one
          payload shape.
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
            Send a clean initiate request and RouteX returns the hosted checkout
            link. Leave the gateway out for automatic routing, or set one only
            when you need a specific provider.
          </p>
          <div className="poster-panel__pillars">
            <div className="poster-pillar">
              <strong>Manual override</strong>
              <span>Pin a PSP for a flow that needs it. Stay automatic for the rest.</span>
            </div>
            <div className="poster-pillar">
              <strong>Webhook relay</strong>
              <span>Normalize provider events before your merchant system ever sees them.</span>
            </div>
            <div className="poster-pillar">
              <strong>Fallback ready</strong>
              <span>Keep checkout alive when a preferred PSP slows down or drops.</span>
            </div>
          </div>
        </article>

        <div className="poster-panel__stack">
          <article className="poster-panel">
            <p className="poster-panel__eyebrow">Webhook relay</p>
            <h3 className="poster-panel__title">
              Signed merchant callbacks after RouteX verifies the PSP.
            </h3>
            <p className="poster-panel__copy">
              Merchants pass `notification_url`. RouteX receives the provider
              callback first, verifies it, then posts a cleaner event to the
              merchant.
            </p>
            <span className="poster-panel__meta">Header: X-AGGREGATOR-SIGNATURE</span>
          </article>

          <article className="poster-panel poster-panel--acid">
            <p className="poster-panel__eyebrow">Payout control</p>
            <h3 className="poster-panel__title">
              Trigger merchant payouts without teaching ops four dashboards.
            </h3>
            <p className="poster-panel__copy">
              Teams keep balances, transaction lookup, and payout requests in
              one product lane instead of jumping between provider consoles.
            </p>
          </article>
        </div>
      </div>

      <section className="feature-block__lower" aria-labelledby="built-to-ship-hard">
        <div className="feature-block__lower-copy">
          <p className="feature-block__eyebrow">Built to ship hard</p>
          <h2
            className="feature-block__title feature-block__title--compact"
            id="built-to-ship-hard"
          >
            Built to ship hard.
          </h2>
          <p className="feature-block__summary feature-block__summary--dark">
            Loud on the surface. Precise in the contract. RouteX is built for
            teams that want merchant checkout, signed callbacks, and payout
            control without bolting together four provider playbooks.
          </p>
        </div>

        <div className="benefit-grid">
          <article className="benefit-card">
            <span className="benefit-card__icon">01</span>
            <h3>Hosted collections</h3>
            <p>Return one clean checkout link instead of branching your UI by provider.</p>
          </article>

          <article className="benefit-card">
            <span className="benefit-card__icon">02</span>
            <h3>Webhook relay</h3>
            <p>Receive normalized events signed by RouteX after provider verification is complete.</p>
          </article>

          <article className="benefit-card">
            <span className="benefit-card__icon">03</span>
            <h3>Payout control</h3>
            <p>Keep outbound flows, balance visibility, and transaction lookup inside one merchant stack.</p>
          </article>
        </div>
      </section>
    </section>
  );
}
