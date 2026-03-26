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
          <p className="site-footer__eyebrow">Product</p>
          <Link href="/#product">Routing</Link>
          <Link href="/#features">Features</Link>
          <Link href="/#how-it-works">How It Works</Link>
          <Link href="/#quickstart">Sandbox</Link>
        </div>

        <div>
          <p className="site-footer__eyebrow">Developers</p>
          <Link href="/docs">API Docs</Link>
          <Link href="/#quickstart">Sandbox</Link>
          <Link href="/dashboard">Dashboard</Link>
        </div>
      </div>
    </footer>
  );
}
