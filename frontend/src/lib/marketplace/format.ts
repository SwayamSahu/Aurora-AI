/** Compact stat formatting: 12000 → "12k", 8500 → "8.5k", 1714563 → "1.7m". */
export function formatCount(n: number): string {
  if (n < 1000) return String(n);
  if (n < 1_000_000) {
    const k = n / 1000;
    return (k >= 100 || Number.isInteger(k) ? Math.round(k) : k.toFixed(1)) + "k";
  }
  const m = n / 1_000_000;
  return (Number.isInteger(m) ? m : m.toFixed(1)) + "m";
}

/** Seconds → "0:08" / "1:24". */
export function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}
