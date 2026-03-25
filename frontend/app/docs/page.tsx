import { SiteFooter } from "../../components/layout/site-footer";
import { SiteHeader } from "../../components/layout/site-header";
import { ReferenceShell } from "../../components/docs/reference-shell";
import { getApiReferenceData } from "../../lib/openapi";

export default async function DocsPage() {
  const referenceData = await getApiReferenceData();

  return (
    <div className="site-shell">
      <SiteHeader />
      <main className="landing-shell">
        <ReferenceShell
          groups={referenceData.groups}
          sourceLabel={referenceData.sourceLabel}
          sourceMode={referenceData.sourceMode}
        />
      </main>
      <SiteFooter />
    </div>
  );
}
