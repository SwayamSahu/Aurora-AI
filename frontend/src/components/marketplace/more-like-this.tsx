import type { Piece } from "@/lib/marketplace/mock-pieces";
import { PieceCard } from "@/components/marketplace/piece-card";

export function MoreLikeThis({
  category,
  pieces,
}: {
  category: string;
  pieces: Piece[];
}) {
  return (
    <aside>
      <p className="text-[12px] font-semibold uppercase tracking-[1.5px] text-mk-lavender">
        More like this
      </p>
      <h2 className="mt-2 text-3xl font-extrabold capitalize tracking-tight">
        {category}
      </h2>

      <div className="mt-6 columns-2 gap-4">
        {pieces.map((p) => (
          <PieceCard key={p.id} piece={p} />
        ))}
      </div>
    </aside>
  );
}
