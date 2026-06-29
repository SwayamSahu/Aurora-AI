"use client";

import * as React from "react";

import { MOCK_CATEGORIES, MOCK_TOTAL } from "@/lib/marketplace/mock-pieces";
import { usePiecesInfinite } from "@/lib/marketplace/queries";
import { SearchCreateBar } from "@/components/marketplace/search-create-bar";
import { FilterChips } from "@/components/marketplace/filter-chips";
import { ResultsCount } from "@/components/marketplace/results-count";
import { MasonryGrid } from "@/components/marketplace/masonry-grid";
import { InfiniteSentinel } from "@/components/marketplace/infinite-sentinel";

export default function ExplorePage() {
  const [active, setActive] = React.useState("all");
  const [query, setQuery] = React.useState("");

  const {
    data,
    isLoading,
    isFetchingNextPage,
    hasNextPage,
    fetchNextPage,
  } = usePiecesInfinite(active, query);

  const pieces = React.useMemo(
    () => data?.pages.flatMap((p) => p.items) ?? [],
    [data],
  );

  // Marketplace-scale count for the "N PIECES · IN VIEW" line.
  const displayCount = React.useMemo(() => {
    if (query.trim()) return pieces.length;
    const cat = MOCK_CATEGORIES.find((c) => c.name === active);
    return cat ? cat.count : MOCK_TOTAL;
  }, [active, query, pieces.length]);

  return (
    <div className="mx-auto w-full max-w-[1600px] px-4 pb-24 pt-7 md:px-10">
      <SearchCreateBar value={query} onChange={setQuery} />
      <div className="mt-6">
        <FilterChips active={active} onSelect={setActive} />
      </div>
      <div className="mt-6">
        <ResultsCount count={displayCount} />
      </div>
      <div className="mt-6">
        <MasonryGrid
          pieces={pieces}
          loadingCount={isLoading ? 15 : isFetchingNextPage ? 5 : 0}
        />
      </div>

      <InfiniteSentinel
        onIntersect={() => {
          if (hasNextPage && !isFetchingNextPage) fetchNextPage();
        }}
        disabled={!hasNextPage}
      />
    </div>
  );
}
