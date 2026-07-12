"use client";

import * as React from "react";
import Link from "next/link";
import { toast } from "sonner";
import { MessageSquare, Pencil, Trash2 } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { isModerator } from "@/lib/admin/access";
import {
  useAdminDeleteComment,
  useAdminPostComments,
  useAdminPosts,
  useDeletePost,
  useModerateComment,
} from "@/lib/blog/queries";
import { AdminCommentModeration } from "@/components/admin/comment-moderation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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

function CommentsPanel({ postId }: { postId: string }) {
  const { data: comments, isLoading } = useAdminPostComments(postId);
  const moderate = useModerateComment(postId);
  const del = useAdminDeleteComment(postId);

  return (
    <div className="mt-3 border-t border-[var(--mk-border)] pt-3">
      <AdminCommentModeration
        comments={comments}
        isLoading={isLoading}
        onToggleHidden={(id, hidden) =>
          moderate.mutate(
            { commentId: id, input: { is_hidden: hidden } },
            {
              onError: (err) =>
                toast.error(err instanceof Error ? err.message : "Failed."),
            },
          )
        }
        onEditBody={(id, body) =>
          moderate.mutate(
            { commentId: id, input: { body } },
            {
              onSuccess: () => toast.success("Comment updated."),
              onError: (err) =>
                toast.error(err instanceof Error ? err.message : "Failed."),
            },
          )
        }
        onDelete={(id) =>
          del.mutate(id, {
            onSuccess: () => toast.success("Comment deleted."),
            onError: (err) =>
              toast.error(err instanceof Error ? err.message : "Failed."),
          })
        }
      />
    </div>
  );
}

function DeletePostButton({ postId }: { postId: string }) {
  const remove = useDeletePost();
  return (
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
            This can&apos;t be undone. The post, its likes and comments will be
            permanently removed.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button
            variant="destructive"
            onClick={() =>
              remove.mutate(postId, {
                onSuccess: () => toast.success("Post deleted."),
                onError: (err) =>
                  toast.error(err instanceof Error ? err.message : "Failed."),
              })
            }
          >
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function AdminBlogPage() {
  const { user, status } = useAuth();
  const [statusFilter, setStatusFilter] = React.useState("all");
  const [q, setQ] = React.useState("");
  const [openComments, setOpenComments] = React.useState<string | null>(null);

  const {
    data,
    isLoading,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useAdminPosts({
    status: statusFilter === "all" ? undefined : statusFilter,
    q: q || undefined,
  });
  const posts = data?.pages.flatMap((page) => page.items) ?? [];
  const total = data?.pages[0]?.total ?? 0;

  if (status === "loading") {
    return (
      <div className="mx-auto w-full max-w-[900px] space-y-3 px-4 py-12">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (status !== "authenticated" || !isModerator(user)) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        Admin access required.
      </p>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[900px] px-4 py-12 md:px-8">
      <h1 className="mb-8 text-3xl font-extrabold tracking-tight">
        Blog Moderation
      </h1>

      <div className="mb-6 flex flex-wrap gap-3">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="published">Published</SelectItem>
          </SelectContent>
        </Select>
        <Input
          placeholder="Search title…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="max-w-xs"
        />
      </div>

      {isLoading ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <div className="space-y-2">
          {posts.map((post) => (
            <div
              key={post.id}
              className="rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4"
            >
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <p className="font-semibold">{post.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {post.status} · {post.author.full_name ?? "Anonymous"} ·{" "}
                    {post.comment_count} comments · {post.like_count} likes
                  </p>
                </div>

                <div className="flex shrink-0 items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setOpenComments(openComments === post.id ? null : post.id)
                    }
                  >
                    <MessageSquare className="size-3.5" /> Comments
                  </Button>
                  <Button variant="outline" size="sm" asChild>
                    <Link href={`/blog/${post.slug}/edit`}>
                      <Pencil className="size-3.5" /> Edit
                    </Link>
                  </Button>
                  <DeletePostButton postId={post.id} />
                </div>
              </div>

              {openComments === post.id ? (
                <CommentsPanel postId={post.id} />
              ) : null}
            </div>
          ))}
          {data && posts.length === 0 ? (
            <p className="py-16 text-center text-muted-foreground">
              No posts match this filter.
            </p>
          ) : null}
          {hasNextPage ? (
            <div className="flex items-center justify-between pt-2">
              <p className="text-xs text-muted-foreground">
                Showing {posts.length} of {total}
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchNextPage()}
                loading={isFetchingNextPage}
              >
                Load more
              </Button>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}
