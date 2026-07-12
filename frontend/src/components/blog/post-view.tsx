"use client";

import * as React from "react";
import Link from "next/link";
import { Clock, Pencil } from "lucide-react";

import { categoryLabel } from "@/lib/blog/content";
import { absoluteMediaUrl, type BlogPostDetail } from "@/lib/blog/api";
import { useAuth } from "@/components/auth/auth-provider";
import { LikeButton } from "@/components/blog/like-button";
import { ReportButton } from "@/components/shared/report-button";

interface TocItem {
  id: string;
  text: string;
  level: number;
}

function slugifyHeading(text: string, i: number): string {
  const base = text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return base ? `${base}-${i}` : `section-${i}`;
}

/**
 * Bake `id="…"` attributes onto every h1-h3 in one pass and collect the
 * table of contents at the same time. Doing this on the HTML string (rather
 * than mutating the live DOM after render) means the ids can't be lost to a
 * later re-render resetting `dangerouslySetInnerHTML`.
 */
function withHeadingIds(html: string): { html: string; toc: TocItem[] } {
  let i = 0;
  const toc: TocItem[] = [];
  const out = html.replace(
    /<h([1-3])([^>]*)>([\s\S]*?)<\/h\1>/gi,
    (_match, level: string, attrs: string, inner: string) => {
      const text = inner.replace(/<[^>]+>/g, "").trim();
      const id = slugifyHeading(text, i);
      i += 1;
      toc.push({ id, text, level: Number(level) });
      return `<h${level} id="${id}"${attrs}>${inner}</h${level}>`;
    },
  );
  return { html: out, toc };
}

export function PostView({
  post,
  slug,
}: {
  post: BlogPostDetail;
  slug: string;
}) {
  // The server sanitizes on write (nh3, strict allow-list) — body_html is
  // already safe HTML by the time it reaches the client.
  const { html: safeHtml, toc } = React.useMemo(
    () => withHeadingIds(post.body_html),
    [post.body_html],
  );
  const { user } = useAuth();
  const isAuthor = user?.id === post.author.id;

  const date = new Date(post.created_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <article className="mx-auto grid w-full max-w-[1100px] grid-cols-1 gap-10 px-4 py-12 md:px-8 lg:grid-cols-[1fr_220px]">
      <div className="min-w-0">
        <span className="inline-flex items-center rounded-md bg-mk-lavender/15 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-mk-lavender">
          {categoryLabel(post.category)}
        </span>
        <h1 className="mt-4 font-serif-display text-4xl italic leading-tight tracking-tight sm:text-5xl">
          {post.title}
        </h1>
        {post.subtitle ? (
          <p className="mt-3 text-lg text-muted-foreground">{post.subtitle}</p>
        ) : null}

        <div className="mt-5 flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          <span>{post.author.full_name ?? "Anonymous"}</span>
          <span>·</span>
          <span>{date}</span>
          <span className="inline-flex items-center gap-1">
            <Clock className="size-3.5" /> {post.read_minutes} min read
          </span>
          <LikeButton post={post} slug={slug} />
          <ReportButton targetType="blog_post" targetId={post.id} />
          {isAuthor ? (
            <Link
              href={`/blog/${slug}/edit`}
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--mk-border)] px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <Pencil className="size-3.5" /> Edit
            </Link>
          ) : null}
        </div>

        {post.cover_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={absoluteMediaUrl(post.cover_url)}
            alt=""
            className="mt-8 w-full rounded-2xl border border-[var(--mk-border)] object-cover"
          />
        ) : null}

        <div
          className="blog-prose mt-8"
          dangerouslySetInnerHTML={{ __html: safeHtml }}
        />
      </div>

      {toc.length > 0 ? (
        <aside className="hidden lg:block">
          <div className="sticky top-24 rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4">
            <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              On this page
            </p>
            <ul className="space-y-2 text-sm">
              {toc.map((item) => (
                <li key={item.id} style={{ paddingLeft: (item.level - 1) * 12 }}>
                  <a
                    href={`#${item.id}`}
                    className="text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {item.text}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      ) : null}
    </article>
  );
}
