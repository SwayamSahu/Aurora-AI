"use client";

import * as React from "react";
import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { ArrowRight, Play } from "lucide-react";

import { hero, cta } from "@/lib/landing/content";
import { Button } from "@/components/ui/button";
import { AuroraBackdrop } from "@/components/marketing/aurora-backdrop";
import { HeroShowreel } from "@/components/marketing/hero-showreel";

export function Hero() {
  const reduce = useReducedMotion();
  const container = {
    hidden: {},
    show: {
      transition: { staggerChildren: reduce ? 0 : 0.08, delayChildren: 0.05 },
    },
  };
  const item = {
    hidden: { opacity: 0, y: reduce ? 0 : 18 },
    show: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as const },
    },
  };

  return (
    <section className="relative isolate overflow-hidden pt-32 pb-20 sm:pt-40 sm:pb-28">
      <AuroraBackdrop />

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="mx-auto flex w-full max-w-4xl flex-col items-center px-6 text-center"
      >
        <motion.span
          variants={item}
          className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-4 py-1.5 text-xs font-medium text-muted-foreground backdrop-blur"
        >
          <span className="size-1.5 rounded-full bg-primary" />
          {hero.eyebrow}
        </motion.span>

        <motion.h1
          variants={item}
          className="mt-6 text-balance text-5xl font-semibold tracking-tight sm:text-6xl md:text-7xl"
        >
          {hero.titleLead}{" "}
          <span className="bg-gradient-to-r from-primary via-[oklch(0.62_0.2_320)] to-[oklch(0.66_0.16_230)] bg-clip-text text-transparent">
            {hero.titleAccent}
          </span>
        </motion.h1>

        <motion.p
          variants={item}
          className="mt-6 max-w-2xl text-pretty text-lg leading-relaxed text-muted-foreground sm:text-xl"
        >
          {hero.subtitle}
        </motion.p>

        <motion.div
          variants={item}
          className="mt-9 flex flex-col items-center gap-3 sm:flex-row"
        >
          <Button size="lg" asChild className="group w-full sm:w-auto">
            <Link href={cta.primary.href}>
              {cta.primary.label}
              <ArrowRight className="transition-transform group-hover:translate-x-0.5" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" asChild className="w-full sm:w-auto">
            <a href={cta.ghost.href}>
              <Play className="size-4" />
              {cta.ghost.label}
            </a>
          </Button>
        </motion.div>

        <motion.p variants={item} className="mt-6 text-xs text-muted-foreground">
          {hero.note}
        </motion.p>
      </motion.div>

      {/* Showreel / preview frame */}
      <motion.div
        id="showreel"
        initial={{ opacity: 0, y: reduce ? 0 : 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className="mx-auto mt-16 w-full max-w-5xl px-6"
      >
        <div className="relative rounded-2xl border border-border bg-card/40 p-2 shadow-2xl backdrop-blur">
          <HeroShowreel />
        </div>
      </motion.div>
    </section>
  );
}
