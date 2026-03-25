import { PushButton } from "../ui/push-button";

const NAV_ITEMS = [
  { label: "Product", href: "#product" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Dashboard", href: "/dashboard" },
  { label: "Docs", href: "/docs" },
  { label: "Sandbox", href: "#sandbox" },
];

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="site-header__brand">
        <span aria-hidden="true" className="site-header__mark">
          R
        </span>
        <span className="site-header__wordmark">RouteX</span>
      </div>

      <nav aria-label="Primary" className="site-header__nav">
        {NAV_ITEMS.map((item) => (
          <a className="site-header__link" href={item.href} key={item.label}>
            {item.label}
          </a>
        ))}
      </nav>

      <div className="site-header__actions">
        <a className="site-header__login" href="#login">
          Log In
        </a>
        <PushButton>Start Testing</PushButton>
      </div>
    </header>
  );
}
