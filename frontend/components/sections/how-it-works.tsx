const STEPS = [
  {
    number: "1",
    title: "Connect",
    body: "Add one RouteX key and keep your checkout or payout calls pointed at a single API.",
  },
  {
    number: "2",
    title: "Route",
    body: "RouteX filters eligible gateways, scores the healthiest path, and logs the decision.",
  },
  {
    number: "3",
    title: "Monitor",
    body: "See health shifts, failover saves, wallet movement, and routing trends in one place.",
  },
];

export function HowItWorks() {
  return (
    <section className="story-section story-section--dark" id="how-it-works">
      <div className="section-heading section-heading--split">
        <div>
          <p className="section-kicker">Adoption flow</p>
          <h2>How It Works</h2>
          <p>Simple as 1-2-3.</p>
        </div>
        <a className="inline-link" href="#docs">
          See full API docs
        </a>
      </div>

      <div className="steps-grid">
        {STEPS.map((step, index) => (
          <article className="step-card" key={step.number}>
            <div className={`step-card__number step-card__number--${index + 1}`}>
              {step.number}
            </div>
            <h3>{step.title}</h3>
            <p>{step.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
