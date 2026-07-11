"use client";

import { Search } from "lucide-react";

import { blogHero } from "@/lib/blog/content";

export function BlogHero({
  query,
  onQueryChange,
  totalPosts,
}: {
  query: string;
  onQueryChange: (v: string) => void;
  totalPosts?: number;
}) {
  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-16 pt-14 text-center md:pt-20">
      <span className="inline-flex items-center gap-2 rounded-full border border-[var(--mk-border)] bg-[var(--mk-surface-1)] px-4 py-1.5 text-xs font-semibold uppercase tracking-[1.5px] text-mk-lavender">
        {blogHero.eyebrow}
      </span>

      <h1 className="mt-6 font-serif-display text-5xl italic tracking-tight sm:text-6xl">
        {blogHero.titleLead}{" "}
        <span className="bg-gradient-to-r from-mk-violet via-mk-lavender to-mk-cyan bg-clip-text text-transparent">
          {blogHero.titleAccent}
        </span>
      </h1>

      <p className="mx-auto mt-5 max-w-xl text-pretty text-lg text-muted-foreground">
        {blogHero.subtitle}
        {typeof totalPosts === "number" && totalPosts > 0 ? (
          <span className="mt-1 block text-sm text-[var(--mk-text-dim)]">
            {totalPosts.toLocaleString()} posts and counting
          </span>
        ) : null}
      </p>

      <div className="relative mx-auto mt-8 max-w-lg">
        <Search className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="search"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder={blogHero.searchPlaceholder}
          aria-label="Search the blog"
          className="h-12 w-full rounded-full border border-[var(--mk-border)] bg-[var(--mk-surface-2)] pl-11 pr-4 text-[15px] text-foreground placeholder:text-muted-foreground focus:border-[var(--mk-border-strong)] focus:outline-none"
        />
      </div>
    </div>
  );
}
