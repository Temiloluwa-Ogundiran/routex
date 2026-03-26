import Link from "next/link";
import { docsHref } from "../../lib/docs-url";

export function FinalCta() {
  return (
    <section className="story-section story-section--cta liquid-cta-section" id="docs">
      <div className="final-cta liquid-cta">
        <h2>
          Ready to <span>Flow?</span>
        </h2>
        <p>
          Give your team one sharp surface for collections, payouts, merchant
          webhooks, and live payment visibility.
        </p>
        <div className="hero-actions">
          <Link className="push-button push-button--primary" href="/signup">
            Get Started Now
          </Link>
          <a className="push-button push-button--secondary" href={docsHref()}>
            Explore Docs
          </a>
        </div>
      </div>
    </section>
  );
}
