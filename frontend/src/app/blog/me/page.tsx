"use client";

import Link from "next/link";
import { Pencil, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { useDeletePost, useMyPosts } from "@/lib/blog/queries";
import { categoryLabel } from "@/lib/blog/content";
import { absoluteMediaUrl, type BlogPostSummary } from "@/lib/blog/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

function MyPostRow({ post }: { post: BlogPostSummary }) {
  const remove = useDeletePost();

  async function onDelete() {
    try {
      await remove.mutateAsync(post.id);
      toast.success("Post deleted.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't delete the post.");
    }
  }

  return (
    <div className="flex items-center gap-4 rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4">
      <div className="size-16 shrink-0 overflow-hidden rounded-lg bg-[var(--mk-surface-2)]">
        {post.cover_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={absoluteMediaUrl(post.cover_url)}
            alt=""
            className="size-full object-cover"
          />
        ) : null}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Link
            href={`/blog/${post.slug}`}
            className="truncate font-serif-display text-base italic text-foreground hover:underline"
          >
            {post.title || "Untitled"}
          </Link>
          <span
            className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${
              post.status === "published"
                ? "bg-emerald-500/15 text-emerald-500"
                : "bg-amber-500/15 text-amber-500"
            }`}
          >
            {post.status}
          </span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          {categoryLabel(post.category)} · {post.like_count} likes ·{" "}
          {post.comment_count} comments
        </p>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <Button variant="outline" size="sm" asChild>
          <Link href={`/blog/${post.slug}/edit`}>
            <Pencil className="size-3.5" /> Edit
          </Link>
        </Button>
        <Dialog>
          <DialogTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="size-3.5" /> Delete
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete this post?</DialogTitle>
              <DialogDescription>
                This can&apos;t be undone. The post, its likes and comments
                will be permanently removed.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline">Cancel</Button>
              </DialogClose>
              <Button variant="destructive" onClick={onDelete}>
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default function MyPostsPage() {
  const { status } = useAuth();
  const { data: posts, isLoading } = useMyPosts();

  if (status === "loading") {
    return (
      <div className="mx-auto w-full max-w-[820px] space-y-3 px-4 py-12">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (status !== "authenticated") {
    return (
      <p className="py-24 text-center text-muted-foreground">
        <a href="/login" className="text-mk-lavender hover:underline">
          Sign in
        </a>{" "}
        to see your posts.
      </p>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[820px] px-4 py-12 md:px-8">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="font-serif-display text-3xl italic tracking-tight text-foreground">
          My posts
        </h1>
        <Button asChild size="sm" className="gap-1.5">
          <Link href="/blog/new">
            <Pencil className="size-3.5" /> New post
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : posts && posts.length > 0 ? (
        <div className="space-y-3">
          {posts.map((post) => (
            <MyPostRow key={post.id} post={post} />
          ))}
        </div>
      ) : (
        <p className="py-16 text-center text-muted-foreground">
          You haven&apos;t written anything yet.{" "}
          <Link href="/blog/new" className="text-mk-lavender hover:underline">
            Write your first post
          </Link>
          .
        </p>
      )}
    </div>
  );
}
