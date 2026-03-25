const PROBLEMS = [
  "Single gateway downtime kills conversion",
  "Manual switching during incidents",
  "Separate integrations for collections and payouts",
  "No visibility into why a payment failed",
];

const BENEFITS = [
  "One integration across four gateways",
  "Dynamic gateway scoring from health and performance",
  "Unified verification and webhooks",
  "Dashboard visibility for failovers and trends",
];

export function ProblemSolution() {
  return (
    <section className="story-section story-section--light" id="product">
      <div className="section-heading">
        <h2>STOP THE PAYMENT CHAOS.</h2>
        <p>
          RouteX flips payment operations from reactive gateway switching to
          one calm routing layer.
        </p>
      </div>

      <div className="compare-grid">
        <article className="compare-card compare-card--problem">
          <h3>THE OLD WAY</h3>
          <ul className="icon-list">
            {PROBLEMS.map((item) => (
              <li key={item}>
                <span className="icon-list__mark icon-list__mark--problem">x</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </article>

        <article className="compare-card compare-card--solution">
          <h3>THE ROUTEX WAY</h3>
          <ul className="icon-list">
            {BENEFITS.map((item) => (
              <li key={item}>
                <span className="icon-list__mark icon-list__mark--solution">+</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </article>
      </div>
    </section>
  );
}
