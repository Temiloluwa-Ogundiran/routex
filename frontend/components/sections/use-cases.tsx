const USE_CASES = [
  {
    label: "For Merchants",
    title: "Checkout teams",
    body: "Improve authorization success without wiring every gateway directly into your product.",
    tone: "sage",
  },
  {
    label: "Most Popular",
    title: "Platforms",
    body: "Run one control layer for many merchants and centralize gateway strategy from one place.",
    tone: "yellow",
  },
  {
    label: "For Ops & Finance",
    title: "Operations",
    body: "Track incidents faster, explain routing choices, and keep payout activity visible.",
    tone: "dark",
  },
];

export function UseCases() {
  return (
    <section className="story-section story-section--light" id="dashboard">
      <div className="section-heading section-heading--centered">
        <h2>Made for checkout teams, platforms, and ops.</h2>
      </div>

      <div className="persona-grid">
        {USE_CASES.map((card) => (
          <article className={`persona-card persona-card--${card.tone}`} key={card.title}>
            <span className="persona-card__badge">{card.label}</span>
            <h3>{card.title}</h3>
            <p>{card.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
