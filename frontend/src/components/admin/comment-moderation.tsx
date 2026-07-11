"use client";

import * as React from "react";
import { Eye, EyeOff, Pencil, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";

export interface ModerationComment {
  id: string;
  body: string;
  author: { id: string; full_name: string | null };
  created_at: string;
  is_hidden: boolean;
}

/** Shared admin panel for moderating comments — used for both blog posts
 * and marketplace listings, since `BlogComment` and `ListingCommentRead`
 * share this exact shape. */
export function AdminCommentModeration({
  comments,
  isLoading,
  onToggleHidden,
  onEditBody,
  onDelete,
}: {
  comments: ModerationComment[] | undefined;
  isLoading: boolean;
  onToggleHidden: (commentId: string, hidden: boolean) => void;
  onEditBody: (commentId: string, body: string) => void;
  onDelete: (commentId: string) => void;
}) {
  const [editingId, setEditingId] = React.useState<string | null>(null);
  const [draft, setDraft] = React.useState("");

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    );
  }

  if (!comments || comments.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-muted-foreground">
        No comments on this one.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {comments.map((c) => (
        <div
          key={c.id}
          className={`rounded-lg border p-3 ${
            c.is_hidden
              ? "border-amber-500/30 bg-amber-500/5"
              : "border-[var(--mk-border)] bg-[var(--mk-surface-1)]"
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-muted-foreground">
                {c.author.full_name ?? "Anonymous"} ·{" "}
                {new Date(c.created_at).toLocaleDateString()}
                {c.is_hidden ? (
                  <span className="ml-2 rounded-full bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-500">
                    Hidden
                  </span>
                ) : null}
              </p>

              {editingId === c.id ? (
                <div className="mt-2 space-y-2">
                  <Textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    className="min-h-16 text-sm"
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => {
                        onEditBody(c.id, draft);
                        setEditingId(null);
                      }}
                    >
                      Save
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingId(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <p className="mt-1 text-sm">{c.body}</p>
              )}
            </div>

            {editingId === c.id ? null : (
              <div className="flex shrink-0 items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label={c.is_hidden ? "Unhide comment" : "Hide comment"}
                  onClick={() => onToggleHidden(c.id, !c.is_hidden)}
                >
                  {c.is_hidden ? (
                    <Eye className="size-3.5" />
                  ) : (
                    <EyeOff className="size-3.5" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label="Edit comment"
                  onClick={() => {
                    setEditingId(c.id);
                    setDraft(c.body);
                  }}
                >
                  <Pencil className="size-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label="Delete comment"
                  className="text-destructive hover:text-destructive"
                  onClick={() => onDelete(c.id)}
                >
                  <Trash2 className="size-3.5" />
                </Button>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
