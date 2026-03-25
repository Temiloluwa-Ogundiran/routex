import { ApiPlayground } from "../components/playground/api-playground";
import { FeatureGrid } from "../components/sections/feature-grid";
import { FinalCta } from "../components/sections/final-cta";
import { HeroSection } from "../components/sections/hero-section";
import { HowItWorks } from "../components/sections/how-it-works";
import { SiteFooter } from "../components/layout/site-footer";
import { SiteHeader } from "../components/layout/site-header";
import { ProblemSolution } from "../components/sections/problem-solution";
import { ProofSection } from "../components/sections/proof-section";
import { TrustMarquee } from "../components/sections/trust-marquee";
import { UseCases } from "../components/sections/use-cases";
import { isLivePlaygroundConfigured } from "../lib/runtime-config";

export default function HomePage() {
  const playgroundMode = isLivePlaygroundConfigured() ? "live" : "disabled";

  return (
    <div className="site-shell">
      <SiteHeader />
      <main className="landing-shell">
        <HeroSection />
        <TrustMarquee />
        <ProblemSolution />
        <FeatureGrid />
        <HowItWorks />
        <UseCases />
        <ApiPlayground mode={playgroundMode} />
        <ProofSection />
        <FinalCta />
      </main>
      <SiteFooter />
    </div>
  );
}
