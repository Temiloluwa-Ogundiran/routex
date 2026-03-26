import { Suspense } from "react";

import { MerchantDashboardShell } from "../../components/app/merchant-dashboard-shell";

function DashboardLoadingFallback() {
  return (
    <section className="dashboard-hero">
      <div className="dashboard-hero__copy">
        <p className="section-badge">Merchant Workspace</p>
        <h1>Loading your RouteX workspace</h1>
        <p>We are preparing your balances, transactions, payment links, and API keys.</p>
      </div>
    </section>
  );
}

export default async function DashboardPage() {
  return (
    <div className="site-shell">
      <main className="dashboard-shell">
        <Suspense fallback={<DashboardLoadingFallback />}>
          <MerchantDashboardShell />
        </Suspense>
      </main>
    </div>
  );
}
