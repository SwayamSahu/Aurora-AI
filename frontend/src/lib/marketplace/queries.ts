/**
 * Infinite-scroll data layer for the gallery. Backs onto the mock dataset
 * today, paging + cycling it so the wall keeps filling like a real catalog.
 * Swap fetchPiecesPage for an `apiFetch("/pieces?cursor=…")` call later.
 */
import { useInfiniteQuery } from "@tanstack/react-query";

import { MOCK_PIECES, type Piece } from "./mock-pieces";

const PAGE_SIZE = 12;
const MAX_PAGES = 14;

export interface PiecesPage {
  items: Piece[];
  nextCursor: number | null;
}

const SPECIAL = new Set(["all", "fresh", "for-you", "trending"]);

function filterBase(active: string, query: string): Piece[] {
  const q = query.trim().toLowerCase();
  return MOCK_PIECES.filter((p) => {
    const matchesChip = SPECIAL.has(active) || p.category === active;
    const matchesQuery =
      !q || p.title.toLowerCase().includes(q) || p.category.includes(q);
    return matchesChip && matchesQuery;
  });
}

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

async function fetchPiecesPage(
  active: string,
  query: string,
  page: number,
): Promise<PiecesPage> {
  // Simulated latency so skeleton shimmer is visible.
  await delay(page === 0 ? 250 : 450);

  const base = filterBase(active, query);
  if (base.length === 0) return { items: [], nextCursor: null };

  const items = Array.from(
    { length: PAGE_SIZE },
    (_, i) => base[(page * PAGE_SIZE + i) % base.length],
  );
  const nextCursor = page + 1 < MAX_PAGES ? page + 1 : null;
  return { items, nextCursor };
}

export function usePiecesInfinite(active: string, query: string) {
  return useInfiniteQuery({
    queryKey: ["mk-pieces", active, query],
    queryFn: ({ pageParam }) => fetchPiecesPage(active, query, pageParam),
    initialPageParam: 0,
    getNextPageParam: (last) => last.nextCursor,
  });
}
