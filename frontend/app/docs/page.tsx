import { SiteFooter } from "../../components/layout/site-footer";
import { SiteHeader } from "../../components/layout/site-header";
import { ReferenceShell } from "../../components/docs/reference-shell";
import { getApiReferenceData } from "../../lib/openapi";

export const dynamic = "force-dynamic";

export default async function DocsPage() {
  const referenceData = await getApiReferenceData();

  return (
    <div className="site-shell">
      <SiteHeader />
      <main className="landing-shell">
        <ReferenceShell
          baseUrl={referenceData.baseUrl}
          groups={referenceData.groups}
          sourceMode={referenceData.sourceMode}
          unavailableReason={referenceData.unavailableReason}
        />
      </main>
      <SiteFooter />
    </div>
  );
}
