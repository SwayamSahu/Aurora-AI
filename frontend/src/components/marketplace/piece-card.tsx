"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { Eye, MessageSquare, Heart, Bookmark, Play } from "lucide-react";

import { cn } from "@/lib/utils";
import type { Piece } from "@/lib/marketplace/mock-pieces";
import { formatCount, formatDuration } from "@/lib/marketplace/format";
import { StatPill } from "@/components/marketplace/stat-pill";

// One-line prompt teases by category — baited on hover to drive the click.
const PROMPTS: Record<string, string> = {
  fantasy: "a lone mage at the edge of a floating realm…",
  landscapes: "golden hour spilling over endless misted peaks…",
  portraits: "soft studio light on a weathered, storied face…",
  anime: "cel-shaded heroine mid-leap through a neon city…",
  animals: "an apex predator stalking through drifting ash…",
  "sci-fi": "a neon megacity drowning in violet rain…",
  fashion: "editorial silhouette in liquid-metal couture…",
  food: "steam curling off a rustic, hand-plated dish…",
};

export function PieceCard({ piece, index = 0 }: { piece: Piece; index?: number }) {
  const [loaded, setLoaded] = React.useState(false);
  const [hovered, setHovered] = React.useState(false);
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const isVideo = piece.type === "video";
  const sold = piece.status === "sold";

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
      href={`/explore/${piece.id}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className="group mb-4 block break-inside-avoid focus-visible:outline-none motion-safe:[animation:mk-rise_0.5s_cubic-bezier(0.16,1,0.3,1)_both]"
      style={{ animationDelay: `${Math.min(index, 11) * 40}ms` }}
      aria-label={`${piece.title} — ${formatCount(piece.stats.views)} views`}
    >
      <figure
        className={cn(
          "relative overflow-hidden rounded-[14px] border border-transparent bg-[var(--mk-surface-1)]",
          "transition-[transform,box-shadow,border-color] duration-200 ease-[var(--ease-out,cubic-bezier(0.16,1,0.3,1))]",
          "group-hover:-translate-y-1 group-hover:border-[var(--mk-border-strong)] group-hover:shadow-[var(--mk-shadow-card-hover)]",
          sold && "saturate-[0.6]",
        )}
        style={{ aspectRatio: `${piece.width} / ${piece.height}` }}
      >
        {/* LQIP blur layer */}
        <div
          aria-hidden
          className={cn(
            "absolute inset-0 scale-110 bg-cover bg-center blur-xl transition-opacity duration-500",
            loaded ? "opacity-0" : "opacity-100",
          )}
          style={{ backgroundImage: `url(${piece.lqip})` }}
        />

        {/* Poster / image */}
        <Image
          src={piece.posterUrl}
          alt={piece.title}
          fill
          sizes="(min-width:1536px) 18vw, (min-width:1280px) 22vw, (min-width:1024px) 30vw, (min-width:640px) 45vw, 50vw"
          onLoad={() => setLoaded(true)}
          className={cn(
            "object-cover transition-[opacity,filter] duration-300",
            loaded ? "opacity-100" : "opacity-0",
            isVideo && hovered ? "opacity-0" : "",
            "group-hover:brightness-110",
          )}
        />

        {/* Hover video */}
        {isVideo ? (
          <video
            ref={videoRef}
            src={piece.mediaUrl}
            poster={piece.posterUrl}
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

        {/* Top scrim for stat legibility */}
        <div className="pointer-events-none absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-black/40 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />

        {/* Stat overlay */}
        <div className="absolute inset-x-2.5 top-2.5 flex items-center justify-end gap-1.5 opacity-60 transition-opacity duration-200 group-hover:opacity-100">
          <StatPill icon={Eye} value={formatCount(piece.stats.views)} />
          <StatPill
            icon={MessageSquare}
            value={piece.stats.comments > 0 ? String(piece.stats.comments) : undefined}
          />
          <StatPill
            icon={Heart}
            value={piece.stats.likes > 0 ? String(piece.stats.likes) : undefined}
          />
          {piece.stats.bookmarks > 0 ? (
            <StatPill icon={Bookmark} value={String(piece.stats.bookmarks)} />
          ) : null}
        </div>

        {/* Video duration badge */}
        {isVideo ? (
          <div className="absolute bottom-2.5 left-2.5">
            <span className="inline-flex items-center gap-1 rounded-full bg-[var(--mk-stat-bg)] px-2 py-1 text-[11px] font-semibold text-white backdrop-blur-md">
              <Play className="size-3 fill-white" />
              {piece.durationSec ? formatDuration(piece.durationSec) : ""}
            </span>
          </div>
        ) : null}

        {/* Prompt tease (revealed on hover to bait the click) */}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 translate-y-2 bg-gradient-to-t from-black/80 via-black/40 to-transparent px-3 pb-7 pt-8 opacity-0 transition-all duration-200 group-hover:translate-y-0 group-hover:opacity-100">
          <p className="line-clamp-2 font-mono text-[11px] leading-snug text-white/85">
            {PROMPTS[piece.category] ?? "an Aurora original, ready to make yours…"}
          </p>
        </div>

        {/* Watermark */}
        <span className="pointer-events-none absolute bottom-2 right-2.5 font-pixel text-[8px] tracking-wide text-white/35">
          aurora.ai
        </span>

        {/* Sold ribbon */}
        {sold ? (
          <span className="absolute right-[-30px] top-3 rotate-45 bg-[var(--mk-coral)] px-8 py-0.5 text-[10px] font-bold uppercase tracking-wider text-black shadow-lg">
            Sold
          </span>
        ) : null}
      </figure>
    </Link>
  );
}
