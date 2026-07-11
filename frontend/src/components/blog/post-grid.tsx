"use client";

import { PostCard } from "@/components/blog/post-card";
import type { BlogPostSummary } from "@/lib/blog/api";
import { blogCopy } from "@/lib/blog/content";

function SkeletonCard() {
  return (
    <div className="animate-pulse overflow-hidden rounded-2xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)]">
      <div className="aspect-[16/10] w-full bg-[var(--mk-surface-2)]" />
      <div className="space-y-2 p-5">
        <div className="h-4 w-3/4 rounded bg-[var(--mk-surface-2)]" />
        <div className="h-3 w-full rounded bg-[var(--mk-surface-2)]" />
        <div className="h-3 w-2/3 rounded bg-[var(--mk-surface-2)]" />
      </div>
    </div>
  );
}

export function PostGrid({
  posts,
  loadingCount = 0,
}: {
  posts: BlogPostSummary[];
  loadingCount?: number;
}) {
  if (posts.length === 0 && loadingCount === 0) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        {blogCopy.emptyState}
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
      {Array.from({ length: loadingCount }).map((_, i) => (
        <SkeletonCard key={`sk-${i}`} />
      ))}
    </div>
  );
}
