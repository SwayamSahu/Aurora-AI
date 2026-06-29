import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { finalCta } from "@/lib/landing/content";
import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/reveal";

export function CtaSection() {
  return (
    <section className="px-6 py-24">
      <Reveal className="mx-auto w-full max-w-5xl">
        <div className="relative overflow-hidden rounded-3xl border border-border bg-gradient-to-br from-primary/10 via-card to-[oklch(0.62_0.2_320/0.1)] px-6 py-20 text-center sm:px-12">
          {/* Decorative glows */}
          <div className="pointer-events-none absolute -left-16 top-0 size-72 rounded-full bg-primary/15 blur-3xl" />
          <div className="pointer-events-none absolute -right-16 bottom-0 size-72 rounded-full bg-[oklch(0.62_0.2_320/0.15)] blur-3xl" />

          <div className="relative mx-auto max-w-2xl">
            <h2 className="text-balance text-4xl font-semibold tracking-tight sm:text-5xl">
              {finalCta.heading}
            </h2>
            <p className="mt-4 text-pretty text-lg text-muted-foreground">
              {finalCta.subheading}
            </p>
            <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Button size="lg" asChild className="group w-full sm:w-auto">
                <Link href={finalCta.primary.href}>
                  {finalCta.primary.label}
                  <ArrowRight className="transition-transform group-hover:translate-x-0.5" />
                </Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                asChild
                className="w-full sm:w-auto"
              >
                <Link href={finalCta.secondary.href}>
                  {finalCta.secondary.label}
                </Link>
              </Button>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
