import { FeatureGrid } from "../components/sections/feature-grid";
import { FinalCta } from "../components/sections/final-cta";
import { HeroSection } from "../components/sections/hero-section";
import { SiteFooter } from "../components/layout/site-footer";
import { SiteHeader } from "../components/layout/site-header";

export default function HomePage() {
  return (
    <div className="site-shell">
      <SiteHeader />
      <main className="landing-shell">
        <HeroSection />
        <FeatureGrid />
        <FinalCta />
      </main>
      <SiteFooter />
    </div>
  );
}
