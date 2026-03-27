import Link from "next/link";
import { BrowserMockup } from "../ui/browser-mockup";
import { docsHref } from "../../lib/docs-url";

export function HeroSection() {
  return (
    <section className="poster-hero" id="product">
      <div className="poster-hero__content">
        <span className="poster-badge">For builders &amp; breakers</span>
        <h1 className="poster-hero__title">
          Orchestrate payments without the PSP circus.
        </h1>
        <span aria-hidden="true" className="poster-hero__underline" />
        <p className="poster-hero__copy">
          RouteX gives your team one merchant contract for hosted checkout,
          signed callbacks, payout requests, and gateway overrides without
          scattering product logic across four provider consoles.
        </p>
        <div className="poster-hero__actions">
          <Link className="push-button push-button--primary" href="/signup">
            Get Started
          </Link>
          <a className="push-button push-button--secondary" href={docsHref()}>
            View Docs
          </a>
        </div>
        <div className="poster-hero__proof">
          <div className="poster-proof">
            <strong>4 rails live</strong>
            <span>Flutterwave, Paystack, Kora, Interswitch</span>
          </div>
          <div className="poster-proof">
            <strong>Hosted + API</strong>
            <span>Send one payload. Let customers pick how they pay.</span>
          </div>
        </div>
      </div>
      <div className="poster-hero__visual">
        <BrowserMockup />
      </div>
    </section>
  );
}
