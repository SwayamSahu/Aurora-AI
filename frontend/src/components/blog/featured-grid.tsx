"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { categoryLabel } from "@/lib/blog/content";
import { absoluteMediaUrl, type BlogPostSummary } from "@/lib/blog/api";
import { useFeaturedPosts } from "@/lib/blog/queries";
import { blogCopy } from "@/lib/blog/content";

function FeaturedCard({ post, large }: { post: BlogPostSummary; large?: boolean }) {
  return (
    <Link
      href={`/blog/${post.slug}`}
      className={`group relative flex flex-col justify-end overflow-hidden rounded-2xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-6 transition-colors hover:border-[var(--mk-border-strong)] ${
        large ? "min-h-[260px]" : "min-h-[220px]"
      }`}
    >
      {post.cover_url ? (
        // Dynamic backend-served asset URL; next/image needs remotePatterns.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={absoluteMediaUrl(post.cover_url)}
          alt=""
          className="absolute inset-0 size-full object-cover opacity-40 transition-opacity duration-300 group-hover:opacity-55"
        />
      ) : (
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_60%_at_20%_15%,oklch(0.7_0.19_285/0.25),transparent),radial-gradient(50%_50%_at_85%_85%,oklch(0.62_0.2_320/0.2),transparent)]" />
      )}
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[var(--mk-bg)] via-[var(--mk-bg)]/40 to-transparent" />

      <div className="relative">
        <span className="inline-flex items-center rounded-md bg-mk-lavender/15 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-mk-lavender">
          {categoryLabel(post.category)}
        </span>
        <h3 className="mt-3 font-serif-display text-xl italic leading-snug text-foreground sm:text-2xl">
          {post.title}
        </h3>
        {post.excerpt ? (
          <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
            {post.excerpt}
          </p>
        ) : null}
        <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium text-mk-lavender">
          Read
          <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" />
        </span>
      </div>
    </Link>
  );
}

export function FeaturedGrid() {
  const { data, isLoading } = useFeaturedPosts();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="min-h-[220px] animate-pulse rounded-2xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)]"
          />
        ))}
      </div>
    );
  }

  if (!data || data.length === 0) return null;

  return (
    <section className="mx-auto w-full max-w-[1200px] px-4 pb-16 md:px-8">
      <h2 className="mb-6 font-serif-display text-2xl italic tracking-tight text-foreground sm:text-3xl">
        {blogCopy.featuredHeading}
      </h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {data.slice(0, 4).map((post, i) => (
          <FeaturedCard key={post.id} post={post} large={i < 2} />
        ))}
      </div>
    </section>
  );
}
