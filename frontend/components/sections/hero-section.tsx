import Link from "next/link";
import { BrowserMockup } from "../ui/browser-mockup";
import { docsHref } from "../../lib/docs-url";

export function HeroSection() {
  return (
    <section className="hero-panel liquid-hero" id="product">
      <div className="hero-copy-block">
        <span className="liquid-hero__kicker">Next-gen payment routing</span>
        <h1 className="hero-title">
          FLUID
          <span className="hero-title__outline"> PAYMENTS</span>
        </h1>
        <p className="hero-copy">
          RouteX gives merchants one premium surface for collections, payouts,
          merchant webhooks, and gateway control across Flutterwave, Paystack,
          Korapay, and Interswitch.
        </p>
        <div className="hero-actions">
          <Link className="push-button push-button--primary" href="/signup">
            Open Account
          </Link>
          <a className="push-button push-button--secondary" href={docsHref()}>
            View Docs
          </a>
        </div>
        <div className="liquid-hero__social-proof">
          <div className="liquid-hero__avatars" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </div>
          <div>
            <strong>4 gateways</strong>
            <span>One clean merchant API</span>
          </div>
        </div>
      </div>
      <BrowserMockup />
    </section>
  );
}
