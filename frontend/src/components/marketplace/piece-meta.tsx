import { Heart, Bookmark, MessageSquare, Share2 } from "lucide-react";

import { cn } from "@/lib/utils";
import type { Piece } from "@/lib/marketplace/mock-pieces";
import { formatCount, formatDuration } from "@/lib/marketplace/format";

export function PieceMeta({ piece }: { piece: Piece }) {
  const kind = piece.type === "video" ? "VIDEO" : "STILL";
  const dims = `${piece.width}×${piece.height}`;
  const statusLabel = piece.status.toUpperCase();
  const statusColor =
    piece.status === "sold" ? "text-mk-coral" : "text-mk-lavender";

  return (
    <div>
      <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
        {piece.title}
      </h1>

      {/* Meta line */}
      <p className="mt-4 flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[12px] font-semibold uppercase tracking-[1px] text-muted-foreground">
        <span>{kind}</span>
        <span className="text-[var(--mk-text-dim)]">·</span>
        <span>{dims}</span>
        {piece.type === "video" && piece.durationSec ? (
          <>
            <span className="text-[var(--mk-text-dim)]">·</span>
            <span>{formatDuration(piece.durationSec)}</span>
          </>
        ) : null}
        <span className="text-[var(--mk-text-dim)]">·</span>
        <span className={cn("inline-flex items-center gap-1.5", statusColor)}>
          {piece.status !== "sold" ? (
            <span className="relative flex size-1.5">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-mk-lavender/70" />
              <span className="relative inline-flex size-1.5 rounded-full bg-mk-lavender" />
            </span>
          ) : null}
          {statusLabel}
        </span>
      </p>

      {/* Inspired counter */}
      <div className="mt-8">
        <div className="text-4xl font-extrabold tracking-tight text-mk-lavender sm:text-5xl">
          {piece.stats.inspired.toLocaleString()}
        </div>
        <div className="mt-1 text-[12px] font-semibold uppercase tracking-[1.5px] text-muted-foreground">
          Inspired
        </div>
      </div>

      {/* Mini stat row */}
      <div className="mt-6 flex items-center gap-6 text-[13px] text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <Heart className="size-4" /> {formatCount(piece.stats.likes)}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Bookmark className="size-4" /> {formatCount(piece.stats.bookmarks)}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <MessageSquare className="size-4" /> {formatCount(piece.stats.comments)}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Share2 className="size-4" /> Share
        </span>
      </div>
    </div>
  );
}
