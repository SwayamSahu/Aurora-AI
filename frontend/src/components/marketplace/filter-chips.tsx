"use client";

import { cn } from "@/lib/utils";
import { useCategoryCounts } from "@/lib/marketplace/queries";
import { formatCount } from "@/lib/marketplace/format";

export function FilterChips({
  active,
  onSelect,
}: {
  active: string;
  onSelect: (id: string) => void;
}) {
  const { data: counts } = useCategoryCounts();
  const total = counts ? Object.values(counts).reduce((a, b) => a + b, 0) : 0;
  const categories = counts ? Object.entries(counts).sort((a, b) => b[1] - a[1]) : [];

  const base =
    "inline-flex h-[38px] shrink-0 items-center gap-1.5 rounded-full border px-4 text-[13px] font-semibold tracking-[0.3px] transition-colors";

  return (
    <div className="relative">
      <div className="mk-no-scrollbar mk-edge-fade flex gap-2.5 overflow-x-auto pb-1">
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
          <span
            className={cn(
              "text-[12px] font-medium",
              active === "all" ? "text-black/60" : "text-[var(--mk-text-dim)]",
            )}
          >
            {formatCount(total)}
          </span>
        </button>

        {categories.map(([name, count]) => (
          <button
            key={name}
            type="button"
            onClick={() => onSelect(name)}
            aria-pressed={active === name}
            className={cn(
              base,
              "uppercase",
              active === name
                ? "border-transparent bg-mk-lavender text-black"
                : "border-[var(--mk-border)] bg-[var(--mk-surface-2)] text-foreground",
            )}
          >
            {name}
            <span
              className={cn(
                "text-[12px] font-medium",
                active === name ? "text-black/60" : "text-[var(--mk-text-dim)]",
              )}
            >
              {formatCount(count)}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
