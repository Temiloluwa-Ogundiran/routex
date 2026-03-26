import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer__grid">
        <div>
          <p className="site-footer__eyebrow">RouteX</p>
          <p className="site-footer__copy">
            One integration for collections, payouts, failover, and payment
            visibility across your stack.
          </p>
        </div>

        <div>
          <p className="site-footer__eyebrow">Explore</p>
          <Link href="/#product">Product</Link>
          <Link href="/#platform">Platform</Link>
          <Link href="/docs">Docs</Link>
        </div>

        <div>
          <p className="site-footer__eyebrow">Access</p>
          <Link href="/login">Log in</Link>
          <Link href="/signup">Get started</Link>
          <Link href="/admin/login">Admin</Link>
        </div>
      </div>
    </footer>
  );
}
