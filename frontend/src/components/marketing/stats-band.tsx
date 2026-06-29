import { stats } from "@/lib/landing/content";
import { Reveal } from "@/components/marketing/reveal";

export function StatsBand() {
  return (
    <section className="mx-auto w-full max-w-7xl px-6 py-20">
      <div className="grid grid-cols-2 gap-y-10 rounded-3xl border border-border bg-card/40 px-6 py-12 sm:px-10 lg:grid-cols-4">
        {stats.map((stat, i) => (
          <Reveal key={stat.label} delay={i * 0.06} className="text-center">
            <p className="bg-gradient-to-r from-primary to-[oklch(0.62_0.2_320)] bg-clip-text text-4xl font-semibold tracking-tight text-transparent sm:text-5xl">
              {stat.value}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">{stat.label}</p>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
