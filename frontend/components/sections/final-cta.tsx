import Link from "next/link";

export function FinalCta() {
  return (
    <section className="story-section story-section--cta" id="docs">
      <div className="final-cta">
        <h2>READY TO ROUTE SMARTER?</h2>
        <p>
          Test collections, payouts, and verification in the RouteX sandbox
          before you wire in production.
        </p>
        <div className="hero-actions">
          <Link className="push-button push-button--primary" href="/sandbox">
            Start in Sandbox
          </Link>
          <Link className="push-button push-button--secondary" href="/docs">
            View API Docs
          </Link>
        </div>
      </div>
    </section>
  );
}
