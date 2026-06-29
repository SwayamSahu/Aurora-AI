import type { Metadata } from "next";

import { brand } from "@/lib/landing/content";
import { MarketingNav } from "@/components/marketing/marketing-nav";
import { Hero } from "@/components/marketing/hero";
import { EcosystemStrip } from "@/components/marketing/ecosystem-strip";
import { ModelShowcase } from "@/components/marketing/model-showcase";
import { FeatureTabs } from "@/components/marketing/feature-tabs";
import { BentoFeatures } from "@/components/marketing/bento-features";
import { Workflow } from "@/components/marketing/workflow";
import { StatsBand } from "@/components/marketing/stats-band";
import { Testimonials } from "@/components/marketing/testimonials";
import { OpenSourceBand } from "@/components/marketing/open-source-band";
import { Faq } from "@/components/marketing/faq";
import { CtaSection } from "@/components/marketing/cta-section";
import { MarketingFooter } from "@/components/marketing/marketing-footer";

export const metadata: Metadata = {
  title: brand.metaTitle,
  description: brand.metaDescription,
  openGraph: {
    title: brand.metaTitle,
    description: brand.metaDescription,
    type: "website",
  },
};

export default function LandingPage() {
  return (
    <div className="min-h-svh bg-background">
      {/* Skip link for keyboard users */}
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[60] focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:text-primary-foreground"
      >
        Skip to content
      </a>

      <MarketingNav />

      <main id="main">
        <Hero />
        <EcosystemStrip />
        <ModelShowcase />
        <FeatureTabs />
        <BentoFeatures />
        <Workflow />
        <StatsBand />
        <Testimonials />
        <OpenSourceBand />
        <Faq />
        <CtaSection />
      </main>

      <MarketingFooter />
    </div>
  );
}
