import { cn } from "@/lib/utils";
import { bento } from "@/lib/landing/content";
import { landingIcon } from "@/lib/landing/icon-map";
import { Reveal } from "@/components/marketing/reveal";

// Emphasise the first and fourth cards so the grid reads as a true bento.
const SPANS = [
  "lg:col-span-2",
  "lg:col-span-1",
  "lg:col-span-1",
  "lg:col-span-1",
  "lg:col-span-1",
  "lg:col-span-1",
];

export function BentoFeatures() {
  return (
    <section className="mx-auto w-full max-w-7xl px-6 py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <h2 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl md:text-5xl">
          {bento.heading}
        </h2>
        <p className="mt-4 text-pretty text-lg text-muted-foreground">
          {bento.subheading}
        </p>
      </Reveal>

      <div className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {bento.features.map((feature, i) => {
          const Icon = landingIcon(feature.icon);
          return (
            <Reveal key={feature.title} delay={(i % 3) * 0.06} className={SPANS[i]}>
              <article className="group relative h-full overflow-hidden rounded-2xl border border-border bg-card/40 p-7 transition-all hover:border-primary/40 hover:bg-card">
                <div className="absolute -right-10 -top-10 size-32 rounded-full bg-primary/5 blur-2xl transition-opacity group-hover:opacity-100 sm:opacity-0" />
                <div className="grid size-11 place-items-center rounded-lg bg-accent text-accent-foreground transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                  <Icon className="size-5" />
                </div>
                <div className="mt-5 flex items-center gap-2">
                  <h3 className="text-lg font-semibold">{feature.title}</h3>
                  {feature.tag ? (
                    <span className="rounded-full bg-primary/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-primary">
                      {feature.tag}
                    </span>
                  ) : null}
                </div>
                <p
                  className={cn(
                    "mt-2 text-pretty text-muted-foreground",
                    i === 0 && "sm:max-w-md",
                  )}
                >
                  {feature.description}
                </p>
              </article>
            </Reveal>
          );
        })}
      </div>
    </section>
  );
}
