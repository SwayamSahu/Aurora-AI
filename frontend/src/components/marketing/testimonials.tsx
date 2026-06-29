import { Quote } from "lucide-react";

import { testimonials } from "@/lib/landing/content";
import { Reveal } from "@/components/marketing/reveal";

export function Testimonials() {
  return (
    <section className="mx-auto w-full max-w-7xl px-6 py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <h2 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl md:text-5xl">
          {testimonials.heading}
        </h2>
      </Reveal>

      <div className="mt-14 grid gap-6 md:grid-cols-3">
        {testimonials.items.map((t, i) => (
          <Reveal key={t.name} delay={i * 0.08}>
            <figure className="flex h-full flex-col rounded-2xl border border-border bg-card/40 p-7">
              <Quote className="size-7 text-primary/40" />
              <blockquote className="mt-4 flex-1 text-pretty text-lg leading-relaxed text-foreground/90">
                {t.quote}
              </blockquote>
              <figcaption className="mt-6 flex items-center gap-3 border-t border-border pt-5">
                <div className="grid size-10 place-items-center rounded-full bg-gradient-to-br from-primary to-[oklch(0.62_0.2_320)] text-sm font-semibold text-primary-foreground">
                  {t.name.charAt(0)}
                </div>
                <div>
                  <p className="text-sm font-semibold">{t.name}</p>
                  <p className="text-xs text-muted-foreground">{t.role}</p>
                </div>
              </figcaption>
            </figure>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
