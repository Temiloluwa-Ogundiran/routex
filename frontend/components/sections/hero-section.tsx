import Link from "next/link";
import { BrowserMockup } from "../ui/browser-mockup";
import { DOCS_LINK_REL, DOCS_LINK_TARGET, docsHref } from "../../lib/docs-url";

export function HeroSection() {
  return (
    <section className="poster-hero" id="product">
      <div className="poster-hero__content">
        <span className="poster-badge">Built for real businesses</span>
        <h1 className="poster-hero__title">Take payments. Stay in control.</h1>
        <span aria-hidden="true" className="poster-hero__underline" />
        <p className="poster-hero__copy">
          One checkout, one dashboard, and clear updates when money moves.
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
            <span>Your customer chooses how to pay.</span>
          </div>
        </div>
      </div>
      <div className="poster-hero__visual">
        <BrowserMockup />
      </div>
    </section>
  );
}
