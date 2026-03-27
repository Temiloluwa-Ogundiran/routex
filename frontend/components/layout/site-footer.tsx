import Link from "next/link";
import { DOCS_LINK_REL, DOCS_LINK_TARGET, docsHref } from "../../lib/docs-url";

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
              One place to accept payments, follow results, and manage payouts.
            </p>
          </div>

          <div className="site-footer__column">
            <p className="site-footer__eyebrow">Platform</p>
            <Link href="/#product">Product</Link>
            <Link href="/#route">Why RouteX</Link>
            <a href={docsHref()} rel={DOCS_LINK_REL} target={DOCS_LINK_TARGET}>
              Docs
            </a>
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
            Add your email and open your RouteX workspace.
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
              Start
            </button>
            <a
              className="site-footer__text-link"
              href={docsHref()}
              rel={DOCS_LINK_REL}
              target={DOCS_LINK_TARGET}
            >
              Or read the docs
            </a>
          </div>
        </form>
      </div>
    </footer>
  );
}
