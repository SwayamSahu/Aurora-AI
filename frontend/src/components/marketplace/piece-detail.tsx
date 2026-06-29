"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import type { Piece } from "@/lib/marketplace/mock-pieces";
import { FeaturedMedia } from "@/components/marketplace/featured-media";
import { PieceMeta } from "@/components/marketplace/piece-meta";
import { ActionBar } from "@/components/marketplace/action-bar";
import { Comments } from "@/components/marketplace/comments";
import { MoreLikeThis } from "@/components/marketplace/more-like-this";

export function PieceDetail({
  piece,
  similar,
  number,
  backHref,
  onBack,
  pulse,
}: {
  piece: Piece;
  similar: Piece[];
  number: string;
  backHref?: string;
  onBack?: () => void;
  pulse?: boolean;
}) {
  const back = (
    <span className="inline-flex items-center gap-2 rounded-full bg-[var(--mk-surface-2)] px-4 py-2 text-[14px] font-medium text-foreground transition-colors hover:bg-[var(--mk-surface-hover)]">
      <ArrowLeft className="size-4" />
      Explore
    </span>
  );

  return (
    <div className="mx-auto w-full max-w-[1600px] px-4 py-6 md:px-10">
      {/* Header */}
      <div className="flex items-center gap-6">
        {onBack ? (
          <button type="button" onClick={onBack} aria-label="Back to Explore">
            {back}
          </button>
        ) : (
          <Link href={backHref ?? "/explore"} aria-label="Back to Explore">
            {back}
          </Link>
        )}
        <p className="font-mono text-[12px] font-semibold uppercase tracking-[1.5px]">
          <span className="mr-3 inline-block h-px w-8 align-middle bg-[var(--mk-border-strong)]" />
          <span className="text-mk-lavender">{piece.category}</span>
          <span className="ml-2 text-muted-foreground">· #{number}</span>
        </p>
      </div>

      {/* Two-column body */}
      <div className="mt-6 grid gap-10 lg:grid-cols-[1.35fr_1fr]">
        <div className="min-w-0">
          <FeaturedMedia piece={piece} />
          <PieceMeta piece={piece} />
          <ActionBar piece={piece} pulse={pulse} />
          <Comments piece={piece} />
        </div>

        <MoreLikeThis category={piece.category} pieces={similar} />
      </div>
    </div>
  );
}
