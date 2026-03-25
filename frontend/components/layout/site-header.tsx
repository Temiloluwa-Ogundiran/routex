import Link from "next/link";

const NAV_ITEMS = [
  { label: "Product", href: "#product" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Dashboard", href: "/dashboard" },
  { label: "Docs", href: "/docs" },
  { label: "Sandbox", href: "/#quickstart" },
];

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link className="site-header__brand" href="/">
        <span aria-hidden="true" className="site-header__mark">
          R
        </span>
        <span className="site-header__wordmark">RouteX</span>
      </Link>

      <nav aria-label="Primary" className="site-header__nav">
        {NAV_ITEMS.map((item) => (
          <Link className="site-header__link" href={item.href} key={item.label}>
            {item.label}
          </Link>
        ))}
      </nav>

      <div className="site-header__actions">
        <Link className="site-header__login" href="/login">
          Log In
        </Link>
        <Link className="push-button push-button--primary" href="/signup">
          Start Testing
        </Link>
      </div>
    </header>
  );
}
