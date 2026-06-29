/**
 * Marketplace data access. Reads the mock dataset today; swap these three
 * functions for `apiFetch` calls when the FastAPI endpoints land — callers
 * won't change.
 */
import { MOCK_PIECES, type Piece } from "./mock-pieces";

export function getPieceById(id: string): Piece | undefined {
  return MOCK_PIECES.find((p) => p.id === id);
}

/** Same-category first, then fill from the rest — stand-in for vector similarity. */
export function getSimilar(id: string, limit = 12): Piece[] {
  const piece = getPieceById(id);
  if (!piece) return [];
  const same = MOCK_PIECES.filter(
    (p) => p.id !== id && p.category === piece.category,
  );
  const rest = MOCK_PIECES.filter(
    (p) => p.id !== id && p.category !== piece.category,
  );
  return [...same, ...rest].slice(0, limit);
}

/** Stable display number, e.g. "0001", from the piece's position. */
export function getPieceNumber(id: string): string {
  const i = MOCK_PIECES.findIndex((p) => p.id === id);
  return String((i < 0 ? 0 : i) + 1).padStart(4, "0");
}
