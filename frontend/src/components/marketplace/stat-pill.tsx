import type { LucideIcon } from "lucide-react";

/** A single blurred-dark stat pill (icon + optional count) for card overlays. */
export function StatPill({
  icon: Icon,
  value,
}: {
  icon: LucideIcon;
  value?: string;
}) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-[var(--mk-stat-bg)] px-2 py-1 text-[12px] font-semibold text-white backdrop-blur-md">
      <Icon className="size-3.5" strokeWidth={2.2} />
      {value ? <span className="tabular-nums">{value}</span> : null}
    </span>
  );
}
