import Link from "next/link";
import { BrowserMockup } from "../ui/browser-mockup";
import { SectionBadge } from "../ui/section-badge";

export function HeroSection() {
  return (
    <section className="hero-panel hero-panel--dotted" id="sandbox">
      <div className="hero-copy-block">
        <SectionBadge>NEW: Intelligent gateway failover is live</SectionBadge>
        <h1 className="hero-title">
          ROUTE EVERY PAYMENT
          <span className="hero-title__outline"> THROUGH THE SMARTEST PATH.</span>
        </h1>
        <p className="hero-copy">
          One integration for collections and payouts, smart gateway failover,
          and visibility across Nigeria&apos;s leading payment rails.
        </p>
        <div className="hero-actions">
          <Link className="push-button push-button--primary" href="/sandbox">
            Try Sandbox
          </Link>
          <Link className="push-button push-button--secondary" href="/docs">
            View API Docs
          </Link>
        </div>
        <div className="hero-meta">
          <span>NGN-first</span>
          <span>Sandbox-ready</span>
          <span>No live key required</span>
        </div>
      </div>
      <BrowserMockup />
    </section>
  );
}
