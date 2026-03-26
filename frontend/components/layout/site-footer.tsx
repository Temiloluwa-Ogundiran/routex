import Link from "next/link";
import { docsHref } from "../../lib/docs-url";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer__grid liquid-footer">
        <div className="liquid-footer__brand">
          <div className="liquid-footer__logo">
            <span aria-hidden="true" className="liquid-footer__logo-dot" />
            <span>RouteX</span>
          </div>
          <p className="site-footer__copy">
            Payment orchestration for teams that want one beautiful surface for
            collections, payouts, routing visibility, and merchant webhooks.
          </p>
        </div>

        <div className="liquid-footer__column">
          <p className="site-footer__eyebrow">Platform</p>
          <Link href="/#product">Product</Link>
          <Link href="/#platform">Features</Link>
          <a href={docsHref()}>Docs</a>
        </div>

        <div className="liquid-footer__column">
          <p className="site-footer__eyebrow">Access</p>
          <Link href="/login">Log in</Link>
          <Link href="/signup">Get Started</Link>
          <Link href="/admin/login">Admin</Link>
        </div>
      </div>
    </footer>
  );
}
