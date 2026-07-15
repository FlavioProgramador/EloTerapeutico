import { SiteHeader } from "./site-header";
import { Pricing } from "./pricing";
import { Faq } from "./faq";
import { FinalCta } from "./final-cta";
import { SiteFooter } from "./site-footer";
import { EloDivider } from "./elo-svg";

import {
  NewHero,
  NewAboutSection,
  NewVideoStatsSection,
  NewFeaturesGrid,
  NewTailoredCareSection,
} from "./new-sections";

export function LandingPage() {
  return (
    <div className="landing-page">
      <SiteHeader />
      <main>
        <NewHero />
        <NewAboutSection />
        <NewVideoStatsSection />
        <NewFeaturesGrid />
        <NewTailoredCareSection />
        <EloDivider />
        <Pricing />
        <Faq />
        <FinalCta />
      </main>
      <SiteFooter />
    </div>
  );
}
