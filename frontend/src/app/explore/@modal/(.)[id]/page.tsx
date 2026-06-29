import { notFound } from "next/navigation";

import { getPieceById, getSimilar, getPieceNumber } from "@/lib/marketplace/api";
import { PieceModal } from "@/components/marketplace/piece-modal";

export default async function InterceptedPiece({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const piece = getPieceById(id);
  if (!piece) notFound();

  return (
    <PieceModal
      piece={piece}
      similar={getSimilar(id)}
      number={getPieceNumber(id)}
    />
  );
}
