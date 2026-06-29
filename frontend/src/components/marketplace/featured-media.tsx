"use client";

import Image from "next/image";

import type { Piece } from "@/lib/marketplace/mock-pieces";

/** Large, contained featured media — letterboxed on the near-black bg. */
export function FeaturedMedia({ piece }: { piece: Piece }) {
  return (
    <div className="relative flex items-center justify-center overflow-hidden rounded-2xl bg-black/40 ring-1 ring-[var(--mk-border)]">
      {piece.type === "video" ? (
        <video
          src={piece.mediaUrl}
          poster={piece.posterUrl}
          autoPlay
          muted
          loop
          playsInline
          className="max-h-[78vh] w-auto max-w-full object-contain"
        />
      ) : (
        <Image
          src={piece.mediaUrl}
          alt={piece.title}
          width={piece.width}
          height={piece.height}
          priority
          className="h-auto max-h-[78vh] w-auto max-w-full object-contain"
        />
      )}
      <span className="pointer-events-none absolute bottom-3 right-4 font-pixel text-[10px] tracking-wide text-white/40">
        aurora.ai
      </span>
    </div>
  );
}
