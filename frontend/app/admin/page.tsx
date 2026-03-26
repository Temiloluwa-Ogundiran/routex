import { Suspense } from "react";

import { AdminDashboardShell } from "../../components/admin/admin-dashboard-shell";

function AdminDashboardLoadingFallback() {
  return (
    <main className="dashboard-shell">
      <section className="dashboard-hero">
        <div className="dashboard-hero__copy">
          <p className="section-badge">Router Control Room</p>
          <h1>Loading the RouteX control room</h1>
          <p>We are pulling live router health, failovers, and policy controls.</p>
        </div>
      </section>
    </main>
  );
}

export default function AdminDashboardPage() {
  return (
    <div className="site-shell">
      <Suspense fallback={<AdminDashboardLoadingFallback />}>
        <AdminDashboardShell />
      </Suspense>
    </div>
  );
}
