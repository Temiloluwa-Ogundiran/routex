import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer__grid">
        <div>
          <p className="site-footer__eyebrow">Unified Routing</p>
          <p className="site-footer__copy">
            Unified payment routing for collections, payouts, and operational
            visibility.
          </p>
        </div>

        <div>
          <p className="site-footer__eyebrow">Product</p>
          <a href="#product">Routing</a>
          <Link href="/dashboard">Dashboard</Link>
          <Link href="/#quickstart">Sandbox</Link>
        </div>

        <div>
          <p className="site-footer__eyebrow">Developers</p>
          <Link href="/docs">API Reference</Link>
          <a href="#quickstart">Quickstart</a>
          <Link href="/admin">Status</Link>
        </div>

        <div>
          <p className="site-footer__eyebrow">Company</p>
          <Link href="/signup">Create Account</Link>
          <Link href="/login">Log In</Link>
          <Link href="/admin/login">Admin Login</Link>
        </div>
      </div>
    </footer>
  );
}
