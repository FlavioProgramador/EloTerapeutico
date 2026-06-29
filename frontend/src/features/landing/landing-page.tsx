import { SiteHeader } from "./site-header";
import { Hero } from "./hero";
import { ProductPreview } from "./product-preview";
import { FeatureGrid } from "./feature-grid";
import { Workflow } from "./workflow";
import { Modules } from "./modules";
import { Security } from "./security";
import { Faq } from "./faq";
import { FinalCta } from "./final-cta";
import { SiteFooter } from "./site-footer";

export function LandingPage() {
  return (
    <div className="landing-page">
      <SiteHeader />
      <main>
        <Hero />
        <ProductPreview />
        <FeatureGrid />
        <Workflow />
        <Modules />
        <Security />
        <Faq />
        <FinalCta />
      </main>
      <SiteFooter />
    </div>
  );
}
