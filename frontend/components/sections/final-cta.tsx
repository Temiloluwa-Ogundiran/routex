import Link from "next/link";

export function FinalCta() {
  return (
    <section className="story-section story-section--cta" id="docs">
      <div className="final-cta">
        <h2>Ready to move money without guesswork?</h2>
        <p>
          Start in test mode, force a gateway when you need to, and keep the webhook story clean from day one.
        </p>
        <div className="hero-actions">
          <Link className="push-button push-button--primary" href="/signup">
            Open your workspace
          </Link>
          <Link className="push-button push-button--secondary" href="/docs">
            Open docs
          </Link>
        </div>
      </div>
    </section>
  );
}
