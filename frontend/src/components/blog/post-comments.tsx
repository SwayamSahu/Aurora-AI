"use client";

import * as React from "react";
import { Trash2 } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import {
  useAddComment,
  useComments,
  useDeleteComment,
} from "@/lib/blog/queries";
import { Button } from "@/components/ui/button";

export function PostComments({
  slug,
  postId,
}: {
  slug: string;
  postId: string;
}) {
  const { user, status } = useAuth();
  const { data: comments = [] } = useComments(slug);
  const add = useAddComment(slug, postId);
  const remove = useDeleteComment(slug);
  const [body, setBody] = React.useState("");

  function submit() {
    const trimmed = body.trim();
    if (!trimmed) return;
    add.mutate(trimmed, { onSuccess: () => setBody("") });
  }

  return (
    <section className="mt-14 border-t border-[var(--mk-border)] pt-8">
      <h2 className="font-serif-display text-xl italic">
        Comments · {comments.length}
      </h2>

      {status === "authenticated" ? (
        <div className="mt-5 flex gap-2">
          <input
            value={body}
            onChange={(e) => setBody(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Add a comment…"
            aria-label="Add a comment"
            className="h-11 flex-1 rounded-full border border-[var(--mk-border)] bg-[var(--mk-surface-2)] px-5 text-sm text-foreground placeholder:text-muted-foreground focus:border-[var(--mk-border-strong)] focus:outline-none"
          />
          <Button onClick={submit} loading={add.isPending} className="shrink-0">
            Post
          </Button>
        </div>
      ) : (
        <p className="mt-5 text-sm text-muted-foreground">
          <a href="/login" className="text-mk-lavender hover:underline">
            Sign in
          </a>{" "}
          to join the conversation.
        </p>
      )}

      <ul className="mt-6 space-y-4">
        {comments.map((c) => (
          <li key={c.id} className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-medium">
                {c.author.full_name ?? "Anonymous"}{" "}
                <span className="ml-2 text-xs font-normal text-muted-foreground">
                  {new Date(c.created_at).toLocaleDateString()}
                </span>
              </p>
              <p className="mt-1 text-sm text-foreground/90">{c.body}</p>
            </div>
            {user?.id === c.author.id ? (
              <button
                type="button"
                aria-label="Delete comment"
                onClick={() => remove.mutate(c.id)}
                className="shrink-0 text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="size-4" />
              </button>
            ) : null}
          </li>
        ))}
        {comments.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No comments yet. Be the first.
          </p>
        ) : null}
      </ul>
    </section>
  );
}
