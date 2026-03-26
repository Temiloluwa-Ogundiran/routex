export function BrowserMockup() {
  return (
    <section aria-label="RouteX dashboard preview" className="browser-mockup liquid-device-stage">
      <article className="liquid-device-stage__floating liquid-device-stage__floating--gain">
        <span>Webhook success</span>
        <strong>+99.4%</strong>
      </article>

      <article className="liquid-device">
        <div className="liquid-device__spark">R</div>
        <div className="liquid-device__badge">PRO</div>

        <div className="liquid-device__body">
          <p className="liquid-device__label">Total volume</p>
          <strong className="liquid-device__amount">NGN 124,500</strong>

          <div className="liquid-device__meter">
            <span />
            <small>Monthly limit</small>
            <strong>75%</strong>
          </div>
        </div>

        <div className="liquid-device__actions">
          <button className="liquid-device__action liquid-device__action--accent" type="button">
            Collect
          </button>
          <button className="liquid-device__action" type="button">
            Verify
          </button>
          <button className="liquid-device__action" type="button">
            Payout
          </button>
        </div>
      </article>

      <article className="liquid-device-stage__floating liquid-device-stage__floating--secure">
        <div className="liquid-device-stage__shield">O</div>
        <div>
          <span>Secure</span>
          <strong>Protected</strong>
        </div>
      </article>
    </section>
  );
}
