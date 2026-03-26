import Link from "next/link";
import { BrowserMockup } from "../ui/browser-mockup";
import { SectionBadge } from "../ui/section-badge";

export function HeroSection() {
  return (
    <section className="hero-panel hero-panel--dotted" id="product">
      <div className="hero-copy-block">
        <SectionBadge>Hyper-fast routing for test mode</SectionBadge>
        <h1 className="hero-title">
          Route every payment
          <span className="hero-title__outline"> with control.</span>
        </h1>
        <p className="hero-copy">
          Collections, payouts, and failover across Paystack, Flutterwave,
          Korapay, and Interswitch with one RouteX control layer.
        </p>
        <div className="hero-actions">
          <Link className="push-button push-button--primary" href="/signup">
            Get started
          </Link>
          <Link className="push-button push-button--secondary" href="/docs">
            Read the docs
          </Link>
        </div>
        <div className="hero-meta">
          <span>Collections, payouts, and failover</span>
          <span>Test mode across four gateways</span>
          <span>Optional gateway override</span>
        </div>
      </div>
      <BrowserMockup />
    </section>
  );
}
