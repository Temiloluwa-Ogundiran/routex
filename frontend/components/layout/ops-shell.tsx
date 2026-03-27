"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type OpsNavSection = {
  label: string;
  items: Array<{
    href: string;
    label: string;
  }>;
};

type OpsShellProps = {
  children: React.ReactNode;
  homeHref: string;
  initials: string;
  navSections: OpsNavSection[];
  subtitle: string;
  title: string;
};

function isActivePath(pathname: string, href: string) {
  if (href.startsWith("#") || href.includes("#")) {
    return false;
  }

  const normalizedHref = href.split("?")[0];
  return (
    pathname === normalizedHref || pathname.startsWith(`${normalizedHref}/`)
  );
}

export function OpsShell({
  children,
  homeHref,
  initials,
  navSections,
  subtitle,
  title,
}: OpsShellProps) {
  const pathname = usePathname();

  return (
    <div className="ops-shell">
      <aside className="ops-sidebar">
        <Link className="ops-sidebar__brand" href={homeHref}>
          <span aria-hidden="true" className="ops-sidebar__mark">
            R
          </span>
          <div className="ops-sidebar__brand-copy">
            <span>{subtitle}</span>
            <strong>{title}</strong>
          </div>
        </Link>

        <div className="ops-sidebar__sections">
          {navSections.map((section) => (
            <section className="ops-sidebar__section" key={section.label}>
              <p className="ops-sidebar__label">{section.label}</p>
              <nav className="ops-sidebar__nav">
                {section.items.map((item) => {
                  const active = isActivePath(pathname, item.href);
                  return (
                    <Link
                      className={`ops-sidebar__link${active ? " ops-sidebar__link--active" : ""}`}
                      href={item.href}
                      key={`${section.label}-${item.label}`}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
            </section>
          ))}
        </div>

        <div className="ops-sidebar__footer">
          <Link className="ops-sidebar__link" href={homeHref}>
            Settings
          </Link>
        </div>
      </aside>

      <div className="ops-main">
        <header className="ops-topbar">
          <div className="ops-topbar__crumbs">
            <span>{subtitle}</span>
            <strong>{title}</strong>
          </div>

          <div className="ops-topbar__utilities">
            <div aria-hidden="true" className="ops-topbar__search">
              Search...
            </div>
            <span className="ops-topbar__avatar">{initials}</span>
          </div>
        </header>

        <div className="ops-content">{children}</div>
      </div>
    </div>
  );
}
