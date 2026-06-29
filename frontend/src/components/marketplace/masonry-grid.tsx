import type { Piece } from "@/lib/marketplace/mock-pieces";
import { PieceCard } from "@/components/marketplace/piece-card";
import { SkeletonCard } from "@/components/marketplace/skeleton-card";

const SKELETON_HEIGHTS = [240, 320, 200, 360, 280, 300, 220, 340, 260, 300, 230, 310];

/**
 * True masonry via CSS columns (60fps, no JS reflow). Cards use
 * break-inside-avoid so they never split across columns. Pieces may repeat
 * across infinite-scroll pages, so keys are composite.
 */
export function MasonryGrid({
  pieces,
  loadingCount = 0,
}: {
  pieces: Piece[];
  loadingCount?: number;
}) {
  if (pieces.length === 0 && loadingCount === 0) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        No pieces match your search.
      </p>
    );
  }

  return (
    <div className="columns-2 gap-4 sm:columns-2 lg:columns-3 xl:columns-4 [@media(min-width:1536px)]:columns-5">
      {pieces.map((piece, i) => (
        <PieceCard key={`${piece.id}-${i}`} piece={piece} index={i % 12} />
      ))}
      {Array.from({ length: loadingCount }).map((_, i) => (
        <SkeletonCard key={`sk-${i}`} height={SKELETON_HEIGHTS[i % SKELETON_HEIGHTS.length]} />
      ))}
    </div>
  );
}
