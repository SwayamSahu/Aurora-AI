"use client";

import * as React from "react";
import { Trash2 } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import {
  useAddListingComment,
  useDeleteListingComment,
  useListingComments,
} from "@/lib/marketplace/queries";
import type { ListingDetail } from "@/lib/marketplace/types";
import { Button } from "@/components/ui/button";
import { ReportButton } from "@/components/shared/report-button";

export function Comments({ piece }: { piece: ListingDetail }) {
  const { user, status } = useAuth();
  const { data: comments = [] } = useListingComments(piece.id);
  const add = useAddListingComment(piece.id);
  const remove = useDeleteListingComment(piece.id);
  const [body, setBody] = React.useState("");

  function submit() {
    const trimmed = body.trim();
    if (!trimmed) return;
    add.mutate(trimmed, { onSuccess: () => setBody("") });
  }

  return (
    <section className="mt-12 border-t border-[var(--mk-border)] pt-8">
      <h2 className="text-lg font-bold">
        Comments
        <span className="ml-2 font-normal text-muted-foreground">
          · {comments.length}
        </span>
      </h2>

      {status === "authenticated" ? (
        <div className="mt-5 flex items-center gap-3">
          <input
            value={body}
            onChange={(e) => setBody(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Say something about this piece…"
            aria-label="Add a comment"
            className="h-11 flex-1 rounded-full border border-[var(--mk-border)] bg-[var(--mk-surface-2)] px-5 text-[14px] text-foreground placeholder:text-muted-foreground focus:border-[var(--mk-border-strong)] focus:outline-none"
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
            ) : (
              <ReportButton
                targetType="listing_comment"
                targetId={c.id}
                label=""
                className="shrink-0 text-muted-foreground hover:text-foreground"
              />
            )}
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
