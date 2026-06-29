import Link from "next/link";
import { Check, ArrowRight } from "lucide-react";

import { openSource } from "@/lib/landing/content";
import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/marketing/reveal";
import { GithubMark } from "@/components/marketing/github-mark";

export function OpenSourceBand() {
  return (
    <section id="open-source" className="scroll-mt-20 px-6 py-24">
      <Reveal className="mx-auto w-full max-w-5xl">
        <div className="relative overflow-hidden rounded-3xl border border-border bg-card/40 px-6 py-14 sm:px-12">
          {/* Decorative glow */}
          <div className="pointer-events-none absolute -right-20 -top-20 size-72 rounded-full bg-primary/10 blur-3xl" />
          <div className="relative grid items-center gap-10 lg:grid-cols-2">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-border bg-background px-3 py-1 text-xs font-medium text-muted-foreground">
                <GithubMark className="size-3.5" />
                {openSource.eyebrow}
              </span>
              <h2 className="mt-5 text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
                {openSource.heading}
              </h2>
              <p className="mt-4 text-pretty text-lg text-muted-foreground">
                {openSource.body}
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button size="lg" asChild className="group">
                  <a
                    href={openSource.primary.href}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    <GithubMark className="size-4" />
                    {openSource.primary.label}
                  </a>
                </Button>
                <Button size="lg" variant="outline" asChild className="group">
                  <Link href={openSource.secondary.href}>
                    {openSource.secondary.label}
                    <ArrowRight className="transition-transform group-hover:translate-x-0.5" />
                  </Link>
                </Button>
              </div>
            </div>

            <ul className="space-y-4">
              {openSource.points.map((point) => (
                <li
                  key={point}
                  className="flex items-center gap-3 rounded-xl border border-border bg-background/60 px-5 py-4"
                >
                  <span className="grid size-6 shrink-0 place-items-center rounded-full bg-primary/15 text-primary">
                    <Check className="size-4" />
                  </span>
                  <span className="font-medium">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
