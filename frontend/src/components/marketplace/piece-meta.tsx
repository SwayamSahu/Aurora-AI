"use client";

import { Heart, MessageSquare, Coins, Share2 } from "lucide-react";

import { cn } from "@/lib/utils";
import type { ListingDetail } from "@/lib/marketplace/types";
import { formatCount, formatDuration } from "@/lib/marketplace/format";

export function PieceMeta({ piece }: { piece: ListingDetail }) {
  const kind = piece.kind === "video" ? "VIDEO" : "STILL";
  const dims = piece.width && piece.height ? `${piece.width}×${piece.height}` : null;
  const statusLabel = piece.status.toUpperCase();
  const statusColor = piece.status === "sold" ? "text-mk-coral" : "text-mk-lavender";

  return (
    <div>
      <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
        {piece.title}
      </h1>

      {/* Meta line */}
      <p className="mt-4 flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[12px] font-semibold uppercase tracking-[1px] text-muted-foreground">
        <span>{kind}</span>
        {dims ? (
          <>
            <span className="text-[var(--mk-text-dim)]">·</span>
            <span>{dims}</span>
          </>
        ) : null}
        {piece.kind === "video" && piece.duration_seconds ? (
          <>
            <span className="text-[var(--mk-text-dim)]">·</span>
            <span>{formatDuration(piece.duration_seconds)}</span>
          </>
        ) : null}
        <span className="text-[var(--mk-text-dim)]">·</span>
        <span className={cn("inline-flex items-center gap-1.5", statusColor)}>
          {piece.status === "active" ? (
            <span className="relative flex size-1.5">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-mk-lavender/70" />
              <span className="relative inline-flex size-1.5 rounded-full bg-mk-lavender" />
            </span>
          ) : null}
          {statusLabel}
        </span>
      </p>

      {piece.description ? (
        <p className="mt-4 max-w-prose text-[15px] leading-relaxed text-muted-foreground">
          {piece.description}
        </p>
      ) : null}

      {/* Price */}
      <div className="mt-8">
        <div className="flex items-center gap-2 text-4xl font-extrabold tracking-tight text-mk-lavender sm:text-5xl">
          <Coins className="size-8" />
          {piece.price_credits.toLocaleString()}
        </div>
        <div className="mt-1 text-[12px] font-semibold uppercase tracking-[1.5px] text-muted-foreground">
          Credits{piece.stock > 1 ? ` · ${piece.stock} available` : ""}
        </div>
      </div>

      {/* Mini stat row */}
      <div className="mt-6 flex items-center gap-6 text-[13px] text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <Heart className="size-4" /> {formatCount(piece.like_count)}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <MessageSquare className="size-4" /> {formatCount(piece.comment_count)}
        </span>
        <button
          type="button"
          onClick={() => {
            if (typeof navigator !== "undefined" && navigator.clipboard) {
              void navigator.clipboard.writeText(window.location.href);
            }
          }}
          className="inline-flex items-center gap-1.5 transition-colors hover:text-foreground"
        >
          <Share2 className="size-4" /> Share
        </button>
      </div>
    </div>
  );
}
