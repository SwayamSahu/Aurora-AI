"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { usePost } from "@/lib/blog/queries";
import { PostView } from "@/components/blog/post-view";
import { PostComments } from "@/components/blog/post-comments";
import { Skeleton } from "@/components/ui/skeleton";

export default function BlogPostPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;
  const { data: post, isLoading, isError } = usePost(slug);

  return (
    <div className="pb-24">
      <div className="mx-auto w-full max-w-[1100px] px-4 pt-6 md:px-8">
        <Link
          href="/blog"
          className="inline-flex items-center gap-2 rounded-full bg-[var(--mk-surface-2)] px-4 py-2 text-sm text-foreground transition-colors hover:bg-[var(--mk-surface-hover)]"
        >
          <ArrowLeft className="size-4" />
          The Journal
        </Link>
      </div>

      {isLoading ? (
        <div className="mx-auto w-full max-w-[1100px] space-y-4 px-4 py-12 md:px-8">
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-12 w-2/3" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : isError || !post ? (
        <p className="py-24 text-center text-muted-foreground">
          Post not found.
        </p>
      ) : (
        <>
          <PostView post={post} slug={slug} />
          <div className="mx-auto w-full max-w-[1100px] px-4 md:px-8">
            <PostComments slug={slug} postId={post.id} />
          </div>
        </>
      )}
    </div>
  );
}
