"use client";

import { useParams } from "next/navigation";

import { useListing, useSimilarListings } from "@/lib/marketplace/queries";
import { PieceDetail } from "@/components/marketplace/piece-detail";

export default function PiecePage() {
  const params = useParams<{ id: string }>();
  const { data: piece, isLoading, isError } = useListing(params.id);
  const { data: similar } = useSimilarListings(params.id, piece?.category ?? "");

  if (isLoading) {
    return <p className="py-24 text-center text-muted-foreground">Loading…</p>;
  }
  if (isError || !piece) {
    return <p className="py-24 text-center text-muted-foreground">Piece not found.</p>;
  }

  return (
    <PieceDetail piece={piece} similar={similar ?? []} backHref="/explore" />
  );
}
