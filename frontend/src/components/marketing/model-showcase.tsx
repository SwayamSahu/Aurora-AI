import { modelsSection } from "@/lib/landing/content";
import { landingIcon } from "@/lib/landing/icon-map";
import { Reveal } from "@/components/marketing/reveal";

export function ModelShowcase() {
  return (
    <section id="models" className="mx-auto w-full max-w-7xl scroll-mt-20 px-6 py-24">
      <Reveal className="mx-auto max-w-2xl text-center">
        <h2 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl md:text-5xl">
          {modelsSection.heading}
        </h2>
        <p className="mt-4 text-pretty text-lg text-muted-foreground">
          {modelsSection.subheading}
        </p>
      </Reveal>

      <div className="mt-14 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {modelsSection.models.map((model, i) => {
          const Icon = landingIcon(model.icon);
          return (
            <Reveal key={model.name} delay={i * 0.05}>
              <div className="group flex h-full items-center gap-4 rounded-xl border border-border bg-card/40 p-5 transition-all hover:border-primary/40 hover:bg-card">
                <div className="grid size-11 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                  <Icon className="size-5" />
                </div>
                <div className="min-w-0">
                  <p className="truncate font-semibold">{model.name}</p>
                  <p className="text-sm text-muted-foreground">{model.kind}</p>
                </div>
              </div>
            </Reveal>
          );
        })}
      </div>
    </section>
  );
}
