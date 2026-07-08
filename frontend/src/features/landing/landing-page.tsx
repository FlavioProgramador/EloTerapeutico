import { SiteHeader } from "./site-header";
import { Hero } from "./hero";
import { ProblemSection } from "./problem-section";
import { ModuleStories } from "./module-stories";
import { Journey } from "./journey";
import { ValueSection } from "./value-section";
import { SocialProof } from "./social-proof";
import { Testimonials } from "./testimonials";
import { TrustSection } from "./trust-section";
import { Pricing } from "./pricing";
import { Faq } from "./faq";
import { FinalCta } from "./final-cta";
import { SiteFooter } from "./site-footer";
import { EloDivider } from "./elo-svg";

export function LandingPage() {
  return (
    <div className="landing-page">
      <SiteHeader />
      <main>
        <Hero />
        <ProblemSection />
        <ModuleStories />
        <EloDivider />
        <Journey />
        <ValueSection />
        <SocialProof />
        <Testimonials />
        <TrustSection />
        <Pricing />
        <Faq />
        <FinalCta />
      </main>
      <SiteFooter />
    </div>
  );
}
