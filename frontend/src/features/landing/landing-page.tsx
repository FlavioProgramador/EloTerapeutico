import { BenefitRail } from "./benefit-rail";
import { Faq } from "./faq";
import { FinalCta } from "./final-cta";
import { Hero } from "./hero";
import { Journey } from "./journey";
import { ModuleStories } from "./module-stories";
import { ProblemSection } from "./problem-section";
import { ProductStage } from "./product-stage";
import { SiteFooter } from "./site-footer";
import { SiteHeader } from "./site-header";
import { TrustSection } from "./trust-section";
import { ValueSection } from "./value-section";

export function LandingPage() {
  return (
    <div className="landing-page">
      <SiteHeader />
      <main>
        <Hero />
        <BenefitRail />
        <ProblemSection />
        <ProductStage />
        <Journey />
        <ModuleStories />
        <ValueSection />
        <TrustSection />
        <Faq />
        <FinalCta />
      </main>
      <SiteFooter />
    </div>
  );
}
