"use client";

import * as React from "react";

import { usePostsInfinite } from "@/lib/blog/queries";
import { blogCopy } from "@/lib/blog/content";
import { BlogHero } from "@/components/blog/blog-hero";
import { FeaturedGrid } from "@/components/blog/featured-grid";
import { CategoryTiles } from "@/components/blog/category-tiles";
import { PostFilterChips } from "@/components/blog/post-filter-chips";
import { PostGrid } from "@/components/blog/post-grid";
import { InfiniteSentinel } from "@/components/marketplace/infinite-sentinel";

/** Debounce a fast-changing value (search input) before it drives a query. */
function useDebounced<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = React.useState(value);
  React.useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return debounced;
}

export default function BlogPage() {
  const [query, setQuery] = React.useState("");
  const [category, setCategory] = React.useState("all");
  const debouncedQuery = useDebounced(query, 300);

  const { data, isLoading, isFetchingNextPage, hasNextPage, fetchNextPage } =
    usePostsInfinite(category, debouncedQuery);

  const posts = React.useMemo(
    () => data?.pages.flatMap((p) => p.items) ?? [],
    [data],
  );
  const total = data?.pages[0]?.total ?? 0;

  const showLanding = !debouncedQuery && category === "all";

  return (
    <div className="pb-24">
      <BlogHero query={query} onQueryChange={setQuery} totalPosts={total} />

      {showLanding ? (
        <>
          <FeaturedGrid />
          <CategoryTiles active={category} onSelect={setCategory} />
        </>
      ) : null}

      <section className="mx-auto w-full max-w-[1200px] px-4 md:px-8">
        {showLanding ? (
          <h2 className="mb-6 font-serif-display text-2xl italic tracking-tight text-foreground sm:text-3xl">
            {blogCopy.allPostsHeading}
          </h2>
        ) : null}
        <div className="mb-6">
          <PostFilterChips active={category} onSelect={setCategory} total={total} />
        </div>
        <PostGrid
          posts={posts}
          loadingCount={isLoading ? 6 : isFetchingNextPage ? 3 : 0}
        />
      </section>

      <InfiniteSentinel
        onIntersect={() => {
          if (hasNextPage && !isFetchingNextPage) fetchNextPage();
        }}
        disabled={!hasNextPage}
      />
    </div>
  );
}
