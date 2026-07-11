"use client";

import * as React from "react";

import { BLOG_CATEGORIES, blogCopy } from "@/lib/blog/content";
import { landingIcon } from "@/lib/landing/icon-map";
import { useCategoryCounts } from "@/lib/blog/queries";

const TILE_COLORS = [
  "bg-mk-violet/15 text-mk-lavender",
  "bg-mk-cyan/15 text-mk-cyan",
  "bg-mk-emerald/15 text-mk-emerald",
  "bg-mk-coral/15 text-mk-coral",
  "bg-mk-violet/15 text-mk-lavender",
  "bg-mk-cyan/15 text-mk-cyan",
];

export function CategoryTiles({
  active,
  onSelect,
}: {
  active: string;
  onSelect: (id: string) => void;
}) {
  const { data: counts } = useCategoryCounts();

  return (
    <section className="mx-auto w-full max-w-[1200px] px-4 pb-16 md:px-8">
      <h2 className="mb-6 font-serif-display text-2xl italic tracking-tight text-foreground sm:text-3xl">
        {blogCopy.categoriesHeading}
      </h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {BLOG_CATEGORIES.map((cat, i) => {
          const Icon = landingIcon(cat.icon);
          const count = counts?.[cat.id] ?? 0;
          const isActive = active === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              onClick={() => onSelect(isActive ? "all" : cat.id)}
              aria-pressed={isActive}
              className={`flex items-center justify-between gap-3 rounded-xl border px-4 py-4 text-left transition-colors ${
                isActive
                  ? "border-mk-violet/60 bg-[var(--mk-surface-hover)]"
                  : "border-[var(--mk-border)] bg-[var(--mk-surface-1)] hover:bg-[var(--mk-surface-hover)]"
              }`}
            >
              <span className="flex items-center gap-3">
                <span
                  className={`grid size-9 shrink-0 place-items-center rounded-lg ${TILE_COLORS[i % TILE_COLORS.length]}`}
                >
                  <Icon className="size-5" />
                </span>
                <span className="font-medium text-foreground">{cat.label}</span>
              </span>
              <span className="text-sm text-muted-foreground">{count} guides</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
