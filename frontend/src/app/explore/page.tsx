"use client";

import * as React from "react";

import { useListingsInfinite } from "@/lib/marketplace/queries";
import { SearchCreateBar } from "@/components/marketplace/search-create-bar";
import { FilterChips } from "@/components/marketplace/filter-chips";
import { ResultsCount } from "@/components/marketplace/results-count";
import { MasonryGrid } from "@/components/marketplace/masonry-grid";
import { InfiniteSentinel } from "@/components/marketplace/infinite-sentinel";

function useDebounced<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = React.useState(value);
  React.useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return debounced;
}

export default function ExplorePage() {
  const [active, setActive] = React.useState("all");
  const [query, setQuery] = React.useState("");
  const debouncedQuery = useDebounced(query, 300);

  const { data, isLoading, isFetchingNextPage, hasNextPage, fetchNextPage } =
    useListingsInfinite(active, debouncedQuery);

  const pieces = React.useMemo(
    () => data?.pages.flatMap((p) => p.items) ?? [],
    [data],
  );
  const total = data?.pages[0]?.total ?? 0;

  return (
    <div className="mx-auto w-full max-w-[1600px] px-4 pb-24 pt-7 md:px-10">
      <SearchCreateBar value={query} onChange={setQuery} />
      <div className="mt-6">
        <FilterChips active={active} onSelect={setActive} />
      </div>
      <div className="mt-6">
        <ResultsCount count={total} />
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
