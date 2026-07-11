"use client";

import { BLOG_CATEGORIES } from "@/lib/blog/content";

export function PostFilterChips({
  active,
  onSelect,
  total,
}: {
  active: string;
  onSelect: (id: string) => void;
  total: number;
}) {
  return (
    <div className="mk-no-scrollbar mk-edge-fade flex gap-2 overflow-x-auto pb-1">
      <button
        type="button"
        onClick={() => onSelect("all")}
        aria-pressed={active === "all"}
        className={`inline-flex h-9 shrink-0 items-center rounded-full border px-4 text-sm font-medium transition-colors ${
          active === "all"
            ? "border-transparent bg-mk-lavender text-black"
            : "border-[var(--mk-border)] bg-[var(--mk-surface-2)] text-foreground"
        }`}
      >
        All {total.toLocaleString()} posts
      </button>
      {BLOG_CATEGORIES.map((cat) => (
        <button
          key={cat.id}
          type="button"
          onClick={() => onSelect(cat.id)}
          aria-pressed={active === cat.id}
          className={`inline-flex h-9 shrink-0 items-center rounded-full border px-4 text-sm font-medium transition-colors ${
            active === cat.id
              ? "border-transparent bg-mk-lavender text-black"
              : "border-[var(--mk-border)] bg-[var(--mk-surface-2)] text-foreground"
          }`}
        >
          {cat.label}
        </button>
      ))}
    </div>
  );
}
