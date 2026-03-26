import { SiteFooter } from "../../components/layout/site-footer";
import { SiteHeader } from "../../components/layout/site-header";
import { ApiPlayground } from "../../components/playground/api-playground";

export default function SandboxPage() {
  return (
    <div className="site-shell">
      <SiteHeader />
      <main className="landing-shell">
        <section className="docs-shell">
          <div className="docs-shell__hero">
            <p className="docs-card__eyebrow">Sandbox</p>
            <h1>Test RouteX with your merchant workspace.</h1>
            <p>
              Send real test-mode requests for collections, payouts, and
              verification without leaving the browser.
            </p>
          </div>
        </section>
        <ApiPlayground />
      </main>
      <SiteFooter />
    </div>
  );
}
