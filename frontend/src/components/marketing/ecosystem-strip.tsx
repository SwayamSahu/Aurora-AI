import { ecosystem } from "@/lib/landing/content";

/**
 * "Built on open source" — an honest ecosystem strip of the technologies
 * Aurora is made of, presented as a seamless looping marquee.
 */
export function EcosystemStrip() {
  // Duplicate the list so the -50% translate loop is seamless.
  const items = [...ecosystem.items, ...ecosystem.items];

  return (
    <section className="border-y border-border bg-card/30 py-10">
      <div className="mx-auto w-full max-w-7xl px-6">
        <p className="text-center text-xs font-medium uppercase tracking-widest text-muted-foreground">
          {ecosystem.label}
        </p>
        <div className="marquee-pause relative mt-6 overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_12%,black_88%,transparent)]">
          <div className="animate-marquee flex w-max items-center gap-12 pr-12">
            {items.map((item, i) => (
              <span
                key={`${item}-${i}`}
                className="text-lg font-semibold text-muted-foreground/70 transition-colors hover:text-foreground"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
