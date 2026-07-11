"use client";

import { useParams } from "next/navigation";

import { useListing, useSimilarListings } from "@/lib/marketplace/queries";
import { PieceModal } from "@/components/marketplace/piece-modal";

export default function InterceptedPiece() {
  const params = useParams<{ id: string }>();
  const { data: piece, isLoading, isError } = useListing(params.id);
  const { data: similar } = useSimilarListings(params.id, piece?.category ?? "");

  if (isLoading || isError || !piece) return null;

  return <PieceModal piece={piece} similar={similar ?? []} />;
}
