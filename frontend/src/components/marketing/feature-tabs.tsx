"use client";

import * as React from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";
import { featureTabs, media } from "@/lib/landing/content";
import { landingIcon } from "@/lib/landing/icon-map";
import { Reveal } from "@/components/marketing/reveal";
import { FeatureHud } from "@/components/marketing/feature-hud";

export function FeatureTabs() {
  const reduce = useReducedMotion();
  const [active, setActive] = React.useState(featureTabs[0].id);
  const tab = featureTabs.find((t) => t.id === active) ?? featureTabs[0];
  const visual = media.featureTab[tab.id];

  return (
    <section id="features" className="scroll-mt-20 border-y border-border bg-card/20 py-24">
      <div className="mx-auto w-full max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <h2 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl md:text-5xl">
            One canvas. Every step of the craft.
          </h2>
          <p className="mt-4 text-pretty text-lg text-muted-foreground">
            Generation, voice, captions and editing — switch between them without
            ever leaving your project.
          </p>
        </Reveal>

        {/* Segmented control */}
        <div className="mt-12 flex flex-wrap justify-center gap-2">
          {featureTabs.map((t) => {
            const Icon = landingIcon(t.icon);
            const isActive = t.id === active;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => setActive(t.id)}
                aria-pressed={isActive}
                className={cn(
                  "inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-all",
                  isActive
                    ? "border-primary bg-primary text-primary-foreground shadow-sm"
                    : "border-border bg-background text-muted-foreground hover:text-foreground",
                )}
              >
                <Icon className="size-4" />
                {t.label}
              </button>
            );
          })}
        </div>

        {/* Panel */}
        <div className="mt-12 grid items-center gap-10 lg:grid-cols-2">
          <AnimatePresence mode="wait">
            <motion.div
              key={tab.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            >
              <div className="inline-flex items-center gap-2 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-accent-foreground">
                {React.createElement(landingIcon(tab.icon), { className: "size-4" })}
                {tab.label}
              </div>
              <h3 className="mt-5 text-2xl font-semibold tracking-tight sm:text-3xl">
                {tab.heading}
              </h3>
              <p className="mt-3 text-pretty text-lg text-muted-foreground">
                {tab.body}
              </p>
              <ul className="mt-6 space-y-3">
                {tab.bullets.map((b) => (
                  <li key={b} className="flex items-start gap-3">
                    <span className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-full bg-primary/15 text-primary">
                      <Check className="size-3.5" />
                    </span>
                    <span className="text-foreground/90">{b}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          </AnimatePresence>

          {/* Visual */}
          <AnimatePresence mode="wait">
            <motion.div
              key={`${tab.id}-visual`}
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
              className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-border bg-background shadow-xl"
            >
              {/* Self-hosted, free-license loop for the active tab */}
              <video
                key={visual.src}
                className="absolute inset-0 size-full object-cover"
                src={visual.src}
                poster={visual.poster}
                autoPlay={!reduce}
                muted
                loop
                playsInline
                preload="none"
                aria-label={visual.alt}
              />
              <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(55%_55%_at_35%_25%,oklch(0.7_0.19_285/0.22),transparent),radial-gradient(45%_45%_at_80%_85%,oklch(0.62_0.2_320/0.2),transparent)]" />
              <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-background/60 via-transparent to-transparent" />
              {/* Tab icon chip */}
              <div className="absolute left-4 top-4 grid size-10 place-items-center rounded-xl border border-border bg-background/70 text-foreground backdrop-blur">
                {React.createElement(landingIcon(tab.icon), { className: "size-5" })}
              </div>
              {/* Context-aware app HUD */}
              <FeatureHud tabId={tab.id} />
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
