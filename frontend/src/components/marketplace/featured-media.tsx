"use client";

import { absoluteMediaUrl } from "@/lib/marketplace/api";
import type { ListingDetail } from "@/lib/marketplace/types";

/** Large, contained featured media — letterboxed on the near-black bg.
 * Only the seller's public preview is ever shown here — the real, private
 * source asset is never exposed pre-purchase (see `checkout_service`). */
export function FeaturedMedia({ piece }: { piece: ListingDetail }) {
  const cover = piece.cover_url ? absoluteMediaUrl(piece.cover_url) : null;
  const previewIsVideo =
    piece.kind === "video" && piece.cover_content_type?.startsWith("video/");

  return (
    <div className="relative flex aspect-video items-center justify-center overflow-hidden rounded-2xl bg-black/40 ring-1 ring-[var(--mk-border)]">
      {!cover ? (
        <div className="absolute inset-0 bg-[radial-gradient(60%_60%_at_25%_20%,oklch(0.7_0.19_285/0.3),transparent),radial-gradient(50%_50%_at_80%_80%,oklch(0.62_0.2_320/0.25),transparent)]" />
      ) : previewIsVideo ? (
        <video
          src={cover}
          autoPlay
          muted
          loop
          playsInline
          className="max-h-[78vh] w-auto max-w-full object-contain"
        />
      ) : (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={cover}
          alt={piece.title}
          className="h-auto max-h-[78vh] w-auto max-w-full object-contain"
        />
      )}
      <span className="pointer-events-none absolute bottom-3 right-4 font-pixel text-[10px] tracking-wide text-white/40">
        aurora.ai
      </span>
    </div>
  );
}
