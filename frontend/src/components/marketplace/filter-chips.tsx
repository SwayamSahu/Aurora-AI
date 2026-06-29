"use client";

import { Star } from "lucide-react";

import { cn } from "@/lib/utils";
import { MOCK_CATEGORIES } from "@/lib/marketplace/mock-pieces";
import { formatCount } from "@/lib/marketplace/format";

export interface ChipState {
  active: string; // "all" | "fresh" | "for-you" | "trending" | category name
}

const SPECIAL = [
  { id: "fresh", label: "FRESH", cls: "border-mk-emerald/50 text-mk-emerald" },
  { id: "for-you", label: "FOR YOU", cls: "bg-mk-violet/20 text-mk-lavender border-transparent", star: true },
  { id: "trending", label: "TRENDING", cls: "border-mk-coral/50 text-mk-coral", count: 42 },
];

export function FilterChips({
  active,
  onSelect,
}: {
  active: string;
  onSelect: (id: string) => void;
}) {
  const base =
    "inline-flex h-[38px] shrink-0 items-center gap-1.5 rounded-full border px-4 text-[13px] font-semibold tracking-[0.3px] transition-colors";

  return (
    <div className="relative">
      <div className="mk-no-scrollbar mk-edge-fade flex gap-2.5 overflow-x-auto pb-1">
        {SPECIAL.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onSelect(s.id)}
            aria-pressed={active === s.id}
            className={cn(
              base,
              active === s.id
                ? "border-transparent bg-mk-lavender text-black"
                : s.cls,
            )}
          >
            {s.label}
            {s.star ? <Star className="size-3 fill-current" /> : null}
            {s.count ? (
              <span className="text-[12px] font-medium opacity-70">{s.count}</span>
            ) : null}
          </button>
        ))}

        <button
          type="button"
          onClick={() => onSelect("all")}
          aria-pressed={active === "all"}
          className={cn(
            base,
            active === "all"
              ? "border-transparent bg-mk-lavender text-black shadow-[0_0_18px_-6px_var(--mk-lavender)]"
              : "border-[var(--mk-border)] bg-[var(--mk-surface-2)] text-foreground",
          )}
        >
          ALL
        </button>

        {MOCK_CATEGORIES.map((c) => (
          <button
            key={c.name}
            type="button"
            onClick={() => onSelect(c.name)}
            aria-pressed={active === c.name}
            className={cn(
              base,
              "uppercase",
              active === c.name
                ? "border-transparent bg-mk-lavender text-black"
                : "border-[var(--mk-border)] bg-[var(--mk-surface-2)] text-foreground",
            )}
          >
            {c.label}
            <span
              className={cn(
                "text-[12px] font-medium",
                active === c.name ? "text-black/60" : "text-[var(--mk-text-dim)]",
              )}
            >
              {formatCount(c.count)}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
