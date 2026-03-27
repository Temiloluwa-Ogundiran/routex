import Link from "next/link";
import { docsHref } from "../../lib/docs-url";

export function FinalCta() {
  return (
    <section className="acid-final-cta" id="docs">
      <div className="acid-final-cta__panel">
        <p className="feature-block__eyebrow">Launch lane</p>
        <h2 className="acid-final-cta__title">Ready to route?</h2>
        <p className="acid-final-cta__copy">
          Start in test mode, keep the merchant payload clean, and let RouteX
          handle hosted collections, signed webhooks, and provider-specific
          orchestration behind the scenes.
        </p>
        <div className="acid-final-cta__actions">
          <Link className="push-button push-button--primary" href="/signup">
            Get started now
          </Link>
          <a className="push-button push-button--secondary" href={docsHref()}>
            Read API reference
          </a>
        </div>
      </div>
    </section>
  );
}
