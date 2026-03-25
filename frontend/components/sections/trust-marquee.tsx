const MARQUEE_ITEMS = [
  "PAYSTACK",
  "FLUTTERWAVE",
  "KORAPAY",
  "INTERSWITCH",
  "MERCHANTS",
  "PLATFORMS",
  "OPS TEAMS",
];

export function TrustMarquee() {
  return (
    <section aria-label="Gateway trust band" className="trust-marquee">
      <div className="trust-marquee__track">
        {[...MARQUEE_ITEMS, ...MARQUEE_ITEMS].map((item, index) => (
          <span className="trust-marquee__item" key={`${item}-${index}`}>
            {item}
          </span>
        ))}
      </div>
    </section>
  );
}
