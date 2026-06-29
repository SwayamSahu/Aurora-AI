/** Shimmering placeholder card with a varied height for the masonry. */
export function SkeletonCard({ height }: { height: number }) {
  return (
    <div className="mb-4 break-inside-avoid">
      <div
        className="relative overflow-hidden rounded-[14px] bg-[var(--mk-surface-1)]"
        style={{ height }}
      >
        <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/[0.06] to-transparent [animation:mk-shimmer_1.4s_infinite]" />
      </div>
    </div>
  );
}
