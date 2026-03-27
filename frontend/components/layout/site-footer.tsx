import Link from "next/link";
import { docsHref } from "../../lib/docs-url";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <div className="site-footer__grid">
          <div className="site-footer__brand">
            <div className="site-footer__logo">
              <span aria-hidden="true" className="site-footer__logo-dot" />
              <span>RouteX</span>
            </div>
            <p className="site-footer__copy">
              Ship hosted collections, signed callbacks, and payout control
              without turning your team into a PSP operations desk.
            </p>
          </div>

          <div className="site-footer__column">
            <p className="site-footer__eyebrow">Platform</p>
            <Link href="/#product">Product</Link>
            <Link href="/#route">Why RouteX</Link>
            <a href={docsHref()}>Docs</a>
          </div>

          <div className="site-footer__column">
            <p className="site-footer__eyebrow">Access</p>
            <Link href="/login">Log in</Link>
            <Link href="/signup">Get started</Link>
            <Link href="/pay/status">Payment status</Link>
          </div>
        </div>

        <form action="/signup" className="site-footer__newsletter" method="get">
          <p className="site-footer__eyebrow">Next move</p>
          <p className="site-footer__copy">
            Drop in a work email and move straight into a RouteX workspace.
          </p>
          <div className="site-footer__newsletter-field">
            <label className="site-footer__newsletter-label" htmlFor="footer-email">
              <input
                aria-label="Work email"
                className="site-footer__newsletter-input"
                id="footer-email"
                name="email"
                placeholder="Work email"
                type="email"
              />
            </label>
            <button className="push-button push-button--primary" type="submit">
              Submit
            </button>
            <a className="site-footer__text-link" href={docsHref()}>
              Or jump into the API reference
            </a>
          </div>
        </form>
      </div>
    </footer>
  );
}
