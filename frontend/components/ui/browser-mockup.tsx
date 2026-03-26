export function BrowserMockup() {
  return (
    <section aria-label="RouteX dashboard preview" className="browser-mockup">
      <header className="browser-mockup__bar">
        <div className="browser-mockup__traffic">
          <span className="browser-mockup__dot browser-mockup__dot--red" />
          <span className="browser-mockup__dot browser-mockup__dot--yellow" />
          <span className="browser-mockup__dot browser-mockup__dot--green" />
        </div>
        <div className="browser-mockup__search" />
      </header>

      <div className="browser-mockup__body">
        <div className="browser-mockup__headline">
          <p>Active gateway score</p>
          <strong>92.4% route health</strong>
        </div>

        <div className="browser-mockup__top-grid">
          <article className="metric-card metric-card--light">
            <span>Top gateway</span>
            <strong>Flutterwave</strong>
            <small>Latency 1.1s</small>
          </article>
          <article className="metric-card metric-card--dark">
            <span>Recovered today</span>
            <strong>18 failovers</strong>
            <small>Saved transactions</small>
          </article>
        </div>

        <div className="browser-mockup__chart-card">
          <div className="browser-mockup__chips">
            <span className="gateway-chip gateway-chip--active">PSTK</span>
            <span className="gateway-chip">FLTW</span>
            <span className="gateway-chip">KORA</span>
            <span className="gateway-chip gateway-chip--muted">ISW</span>
          </div>
          <div className="browser-mockup__chart">
            <span className="browser-mockup__chart-bar browser-mockup__chart-bar--1" />
            <span className="browser-mockup__chart-bar browser-mockup__chart-bar--2" />
            <span className="browser-mockup__chart-bar browser-mockup__chart-bar--3" />
            <span className="browser-mockup__chart-bar browser-mockup__chart-bar--4" />
          </div>
          <div className="browser-mockup__event">
            <strong>Failover event</strong>
            <span>Paystack timeout rerouted to Korapay in 1.8s</span>
          </div>
        </div>
      </div>
    </section>
  );
}
