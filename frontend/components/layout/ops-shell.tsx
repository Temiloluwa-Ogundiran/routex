"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";

type OpsNavSection = {
  label: string;
  items: Array<{
    href: string;
    label: string;
  }>;
};

type OpsShellProps = {
  actions?: React.ReactNode;
  accountMenu?: React.ReactNode;
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
  actions,
  accountMenu,
  children,
  homeHref,
  initials,
  navSections,
  subtitle,
  title,
}: OpsShellProps) {
  const pathname = usePathname();
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);
  const accountMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isAccountMenuOpen) {
      return;
    }

    function handlePointerDown(event: PointerEvent) {
      if (!accountMenuRef.current?.contains(event.target as Node)) {
        setIsAccountMenuOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsAccountMenuOpen(false);
      }
    }

    window.addEventListener("pointerdown", handlePointerDown);
    window.addEventListener("keydown", handleEscape);

    return () => {
      window.removeEventListener("pointerdown", handlePointerDown);
      window.removeEventListener("keydown", handleEscape);
    };
  }, [isAccountMenuOpen]);

  useEffect(() => {
    setIsAccountMenuOpen(false);
  }, [pathname]);

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
      </aside>

      <div className="ops-main">
        <header className="ops-topbar">
          <div className="ops-topbar__crumbs">
            <span>{subtitle}</span>
            <strong>{title}</strong>
          </div>

          <div className="ops-topbar__utilities">
            {actions ? <div className="ops-topbar__actions">{actions}</div> : null}
            <div className="ops-account-menu" ref={accountMenuRef}>
              <button
                aria-expanded={isAccountMenuOpen}
                aria-haspopup={accountMenu ? "menu" : undefined}
                aria-label="Open account menu"
                className="ops-topbar__avatar ops-account-menu__trigger"
                onClick={() => {
                  if (!accountMenu) {
                    return;
                  }
                  setIsAccountMenuOpen((currentState) => !currentState);
                }}
                type="button"
              >
                {initials}
              </button>

              {accountMenu && isAccountMenuOpen ? (
                <div
                  className="ops-account-menu__panel"
                  role="menu"
                >
                  {accountMenu}
                </div>
              ) : null}
            </div>
          </div>
        </header>

        <div className="ops-content">{children}</div>
      </div>
    </div>
  );
}
