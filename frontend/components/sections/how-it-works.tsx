import Link from "next/link";

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
          <p className="section-kicker">Implementation flow</p>
          <h2>Launch faster with one RouteX integration.</h2>
          <p>Keep your product wiring small while RouteX handles routing complexity.</p>
        </div>
        <Link className="inline-link" href="/docs">
          Open docs
        </Link>
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
