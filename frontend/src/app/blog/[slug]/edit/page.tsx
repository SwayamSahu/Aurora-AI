"use client";

import { useParams } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { usePost } from "@/lib/blog/queries";
import { PostEditorForm } from "@/components/blog/editor/post-editor-form";
import { Skeleton } from "@/components/ui/skeleton";

export default function EditBlogPostPage() {
  const params = useParams<{ slug: string }>();
  const { user, status } = useAuth();
  const { data: post, isLoading, isError } = usePost(params.slug);

  if (status === "loading" || isLoading) {
    return (
      <div className="mx-auto w-full max-w-[820px] space-y-4 px-4 py-12">
        <Skeleton className="h-56 w-full" />
        <Skeleton className="h-10 w-2/3" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (status !== "authenticated") {
    return (
      <p className="py-24 text-center text-muted-foreground">
        <a href="/login" className="text-mk-lavender hover:underline">
          Sign in
        </a>{" "}
        to edit this post.
      </p>
    );
  }

  if (isError || !post) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        Post not found.
      </p>
    );
  }

  if (post.author.id !== user?.id) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        You can only edit your own posts.
      </p>
    );
  }

  return <PostEditorForm existing={post} />;
}
