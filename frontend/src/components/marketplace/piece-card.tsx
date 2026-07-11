"use client";

import * as React from "react";
import Link from "next/link";
import { MessageSquare, Heart, Play, Coins } from "lucide-react";

import { cn } from "@/lib/utils";
import { absoluteMediaUrl } from "@/lib/marketplace/api";
import type { MarketplaceListing } from "@/lib/marketplace/types";
import { formatCount, formatDuration } from "@/lib/marketplace/format";
import { StatPill } from "@/components/marketplace/stat-pill";

export function PieceCard({
  piece,
  index = 0,
}: {
  piece: MarketplaceListing;
  index?: number;
}) {
  const [loaded, setLoaded] = React.useState(false);
  const [hovered, setHovered] = React.useState(false);
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const isVideo = piece.kind === "video";
  const sold = piece.status === "sold";
  const cover = piece.cover_url ? absoluteMediaUrl(piece.cover_url) : null;
  const previewIsVideo = isVideo && piece.cover_content_type?.startsWith("video/");
  const width = piece.width ?? 4;
  const height = piece.height ?? 5;

  React.useEffect(() => {
    const el = videoRef.current;
    if (!el) return;
    if (hovered) {
      void el.play().catch(() => {});
    } else {
      el.pause();
      el.currentTime = 0;
    }
  }, [hovered]);

  return (
    <Link
      href={`/explore/p/${piece.id}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="group mb-4 block break-inside-avoid focus-visible:outline-none motion-safe:[animation:mk-rise_0.5s_cubic-bezier(0.16,1,0.3,1)_both]"
      style={{ animationDelay: `${Math.min(index, 11) * 40}ms` }}
      aria-label={`${piece.title} — ${piece.price_credits} credits`}
    >
      <figure
        className={cn(
          "relative overflow-hidden rounded-[14px] border border-transparent bg-[var(--mk-surface-1)]",
          "transition-[transform,box-shadow,border-color] duration-200 ease-[var(--ease-out,cubic-bezier(0.16,1,0.3,1))]",
          "group-hover:-translate-y-1 group-hover:border-[var(--mk-border-strong)] group-hover:shadow-[var(--mk-shadow-card-hover)]",
          sold && "saturate-[0.6]",
        )}
        style={{ aspectRatio: `${width} / ${height}` }}
      >
        {cover ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={cover}
            alt={piece.title}
            onLoad={() => setLoaded(true)}
            className={cn(
              "absolute inset-0 size-full object-cover transition-[opacity,filter] duration-300",
              loaded ? "opacity-100" : "opacity-0",
              previewIsVideo && hovered ? "opacity-0" : "",
              "group-hover:brightness-110",
            )}
          />
        ) : (
          <div className="absolute inset-0 bg-[radial-gradient(60%_60%_at_25%_20%,oklch(0.7_0.19_285/0.3),transparent),radial-gradient(50%_50%_at_80%_80%,oklch(0.62_0.2_320/0.25),transparent)]" />
        )}

        {previewIsVideo && cover ? (
          <video
            ref={videoRef}
            src={cover}
            muted
            loop
            playsInline
            preload="none"
            className={cn(
              "absolute inset-0 size-full object-cover transition-opacity duration-300",
              hovered ? "opacity-100" : "opacity-0",
            )}
          />
        ) : null}

        <div className="pointer-events-none absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-black/40 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />

        {/* Stat overlay */}
        <div className="absolute inset-x-2.5 top-2.5 flex items-center justify-end gap-1.5 opacity-60 transition-opacity duration-200 group-hover:opacity-100">
          <StatPill
            icon={MessageSquare}
            value={piece.comment_count > 0 ? String(piece.comment_count) : undefined}
          />
          <StatPill
            icon={Heart}
            value={piece.like_count > 0 ? formatCount(piece.like_count) : undefined}
          />
        </div>

        {/* Price chip */}
        <div className="absolute bottom-2.5 left-2.5 flex items-center gap-1.5">
          <span className="inline-flex items-center gap-1 rounded-full bg-[var(--mk-stat-bg)] px-2 py-1 text-[11px] font-semibold text-white backdrop-blur-md">
            <Coins className="size-3" />
            {piece.price_credits}
          </span>
          {isVideo && piece.duration_seconds ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-[var(--mk-stat-bg)] px-2 py-1 text-[11px] font-semibold text-white backdrop-blur-md">
              <Play className="size-3 fill-white" />
              {formatDuration(piece.duration_seconds)}
            </span>
          ) : null}
        </div>

        {piece.description ? (
          <div className="pointer-events-none absolute inset-x-0 bottom-0 translate-y-2 bg-gradient-to-t from-black/80 via-black/40 to-transparent px-3 pb-7 pt-8 opacity-0 transition-all duration-200 group-hover:translate-y-0 group-hover:opacity-100">
            <p className="line-clamp-2 font-mono text-[11px] leading-snug text-white/85">
              {piece.description}
            </p>
          </div>
        ) : null}

        <span className="pointer-events-none absolute bottom-2 right-2.5 font-pixel text-[8px] tracking-wide text-white/35">
          aurora.ai
        </span>

        {sold ? (
          <span className="absolute right-[-30px] top-3 rotate-45 bg-[var(--mk-coral)] px-8 py-0.5 text-[10px] font-bold uppercase tracking-wider text-black shadow-lg">
            Sold
          </span>
        ) : null}
      </figure>
    </Link>
  );
}
