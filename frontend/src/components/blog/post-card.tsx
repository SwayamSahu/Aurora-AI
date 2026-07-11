"use client";

import Link from "next/link";
import { Heart, MessageSquare, Clock } from "lucide-react";

import { categoryLabel } from "@/lib/blog/content";
import { absoluteMediaUrl, type BlogPostSummary } from "@/lib/blog/api";

export function PostCard({ post }: { post: BlogPostSummary }) {
  const date = new Date(post.created_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <Link
      href={`/blog/${post.slug}`}
      className="group flex flex-col overflow-hidden rounded-2xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] transition-colors hover:border-[var(--mk-border-strong)]"
    >
      <div className="relative aspect-[16/10] w-full overflow-hidden bg-[var(--mk-surface-2)]">
        {post.cover_url ? (
          // Dynamic backend-served asset URL; next/image needs remotePatterns.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={absoluteMediaUrl(post.cover_url)}
            alt=""
            className="size-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
          />
        ) : (
          <div className="absolute inset-0 bg-[radial-gradient(60%_60%_at_25%_20%,oklch(0.7_0.19_285/0.3),transparent),radial-gradient(50%_50%_at_80%_80%,oklch(0.62_0.2_320/0.25),transparent)]" />
        )}
        <span className="absolute left-3 top-3 rounded-md bg-black/60 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-white backdrop-blur">
          {categoryLabel(post.category)}
        </span>
      </div>

      <div className="flex flex-1 flex-col p-5">
        <h3 className="font-serif-display text-lg italic leading-snug text-foreground">
          {post.title}
        </h3>
        {post.excerpt ? (
          <p className="mt-2 line-clamp-2 flex-1 text-sm text-muted-foreground">
            {post.excerpt}
          </p>
        ) : (
          <div className="flex-1" />
        )}

        <div className="mt-4 flex items-center justify-between border-t border-[var(--mk-border)] pt-3 text-xs text-muted-foreground">
          <span>{date}</span>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1">
              <Clock className="size-3.5" /> {post.read_minutes} min
            </span>
            <span className="inline-flex items-center gap-1">
              <Heart className="size-3.5" /> {post.like_count}
            </span>
            <span className="inline-flex items-center gap-1">
              <MessageSquare className="size-3.5" /> {post.comment_count}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
