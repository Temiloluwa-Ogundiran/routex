import Link from "next/link";
import { BrowserMockup } from "../ui/browser-mockup";
import { DOCS_LINK_REL, DOCS_LINK_TARGET, docsHref } from "../../lib/docs-url";

export function HeroSection() {
  return (
    <section className="poster-hero" id="product">
      <div className="poster-hero__content">
        <span className="poster-badge">Built for modern teams</span>
        <h1 className="poster-hero__title">Accept payments without the mess.</h1>
        <span aria-hidden="true" className="poster-hero__underline" />
        <p className="poster-hero__copy">
          One checkout, one dashboard, and one simple way to track every payment.
        </p>
        <div className="poster-hero__actions">
          <Link className="push-button push-button--primary" href="/signup">
            Get Started
          </Link>
          <a
            className="push-button push-button--secondary"
            href={docsHref()}
            rel={DOCS_LINK_REL}
            target={DOCS_LINK_TARGET}
          >
            View Docs
          </a>
        </div>
        <div className="poster-hero__proof">
          <div className="poster-proof">
            <strong>4 gateways</strong>
            <span>Flutterwave, Paystack, Kora, Interswitch</span>
          </div>
          <div className="poster-proof">
            <strong>One checkout</strong>
            <span>Customers pick how they want to pay.</span>
          </div>
        </div>
      </div>
      <div className="poster-hero__visual">
        <BrowserMockup />
      </div>
    </section>
  );
}
