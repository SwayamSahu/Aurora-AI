export function ResultsCount({ count }: { count: number }) {
  return (
    <p className="text-[13px] font-semibold uppercase tracking-[1.2px] text-muted-foreground">
      <span className="text-foreground">{count.toLocaleString()}</span> Pieces
      <span className="mx-2 text-[var(--mk-text-dim)]">·</span>In view
    </p>
  );
}
