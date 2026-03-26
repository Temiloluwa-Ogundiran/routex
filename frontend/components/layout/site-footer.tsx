import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer__grid">
        <div>
          <p className="site-footer__eyebrow">Unified Routing</p>
          <p className="site-footer__copy">
            Unified payment routing for collections, payouts, and smarter
            payment performance.
          </p>
        </div>

        <div>
          <p className="site-footer__eyebrow">Explore</p>
          <Link href="/#product">Product</Link>
          <Link href="/#how-it-works">How It Works</Link>
          <Link href="/docs">API Docs</Link>
          <Link href="/sandbox">Sandbox</Link>
        </div>

        <div>
          <p className="site-footer__eyebrow">Accounts</p>
          <Link href="/login">Merchant Login</Link>
          <Link href="/signup">Create Account</Link>
          <Link href="/admin/login">Admin Login</Link>
        </div>
      </div>
    </footer>
  );
}
