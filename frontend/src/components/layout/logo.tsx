import { cn } from "@/lib/utils";

export function Logo({
  className,
  showWordmark = true,
}: {
  className?: string;
  showWordmark?: boolean;
}) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <svg
        viewBox="0 0 32 32"
        className="size-7 shrink-0"
        role="img"
        aria-label="Aurora logo"
      >
        <defs>
          <linearGradient id="aurora-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="oklch(0.7 0.19 285)" />
            <stop offset="100%" stopColor="oklch(0.62 0.2 320)" />
          </linearGradient>
        </defs>
        <rect width="32" height="32" rx="8" fill="url(#aurora-grad)" />
        <path
          d="M11 21l5-10 5 10M12.8 17.4h6.4"
          stroke="white"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      </svg>
      {showWordmark ? (
        <span className="text-base font-semibold tracking-tight">Aurora</span>
      ) : null}
    </div>
  );
}
