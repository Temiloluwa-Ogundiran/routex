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
          <a href="#dashboard">Dashboard</a>
          <a href="#sandbox">Sandbox</a>
        </div>

        <div>
          <p className="site-footer__eyebrow">Developers</p>
          <a href="#docs">API Reference</a>
          <a href="#quickstart">Quickstart</a>
          <a href="#status">Status</a>
        </div>

        <div>
          <p className="site-footer__eyebrow">Company</p>
          <a href="#privacy">Privacy</a>
          <a href="#terms">Terms</a>
          <a href="#contact">Contact</a>
        </div>
      </div>
    </footer>
  );
}
