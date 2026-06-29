import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { getPieceById, getSimilar, getPieceNumber } from "@/lib/marketplace/api";
import { PieceDetail } from "@/components/marketplace/piece-detail";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const piece = getPieceById(id);
  if (!piece) return { title: "Piece not found — Aurora" };
  return {
    title: `${piece.title} · #${getPieceNumber(id)} — Aurora Marketplace`,
  };
}

export default async function PiecePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const piece = getPieceById(id);
  if (!piece) notFound();

  return (
    <PieceDetail
      piece={piece}
      similar={getSimilar(id)}
      number={getPieceNumber(id)}
      backHref="/explore"
    />
  );
}
