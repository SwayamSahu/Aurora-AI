"use client";

import { Heart } from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";
import { useToggleLike } from "@/lib/blog/queries";
import type { BlogPostDetail } from "@/lib/blog/api";

export function LikeButton({ post, slug }: { post: BlogPostDetail; slug: string }) {
  const { status } = useAuth();
  const toggle = useToggleLike(slug);

  function onClick() {
    if (status !== "authenticated") {
      window.location.href = "/login";
      return;
    }
    toggle.mutate({ postId: post.id, liked: !post.liked_by_me });
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={toggle.isPending}
      aria-pressed={post.liked_by_me}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
        post.liked_by_me
          ? "border-transparent bg-mk-lavender text-black"
          : "border-[var(--mk-border)] text-muted-foreground hover:text-foreground",
      )}
    >
      <Heart className={cn("size-4", post.liked_by_me && "fill-current")} />
      {post.like_count}
    </button>
  );
}
