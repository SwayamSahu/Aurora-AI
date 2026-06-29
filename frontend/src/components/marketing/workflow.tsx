import { workflow } from "@/lib/landing/content";
import { landingIcon } from "@/lib/landing/icon-map";
import { Reveal } from "@/components/marketing/reveal";

export function Workflow() {
  return (
    <section
      id="workflow"
      className="scroll-mt-20 border-y border-border bg-card/20 py-24"
    >
      <div className="mx-auto w-full max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl md:text-5xl">
            {workflow.heading}
          </h2>
        </Reveal>

        <div className="relative mt-16 grid gap-8 md:grid-cols-3">
          {/* Connector line on desktop */}
          <div className="absolute inset-x-0 top-7 hidden h-px bg-gradient-to-r from-transparent via-border to-transparent md:block" />

          {workflow.steps.map((step, i) => {
            const Icon = landingIcon(step.icon);
            return (
              <Reveal key={step.title} delay={i * 0.1} className="relative">
                <div className="flex flex-col items-center text-center">
                  <div className="relative grid size-14 place-items-center rounded-2xl border border-border bg-background shadow-sm">
                    <Icon className="size-6 text-primary" />
                    <span className="absolute -right-2 -top-2 grid size-6 place-items-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                      {i + 1}
                    </span>
                  </div>
                  <h3 className="mt-5 text-xl font-semibold">{step.title}</h3>
                  <p className="mt-2 max-w-xs text-pretty text-muted-foreground">
                    {step.description}
                  </p>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
