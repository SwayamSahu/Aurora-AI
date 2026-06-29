"use client";

import Link from "next/link";

import type { Piece } from "@/lib/marketplace/mock-pieces";

export function Comments({ piece }: { piece: Piece }) {
  return (
    <section className="mt-12 border-t border-[var(--mk-border)] pt-8">
      <h2 className="text-lg font-bold">
        Comments
        <span className="ml-2 font-normal text-muted-foreground">
          · {piece.stats.comments}
        </span>
      </h2>

      <div className="mt-5 flex items-center gap-3">
        <input
          type="text"
          placeholder="Say something about this piece…"
          aria-label="Add a comment"
          className="h-11 flex-1 rounded-full border border-[var(--mk-border)] bg-[var(--mk-surface-2)] px-5 text-[14px] text-foreground placeholder:text-muted-foreground focus:border-[var(--mk-border-strong)] focus:outline-none"
        />
        <Link
          href="/signup"
          className="inline-flex h-11 shrink-0 items-center rounded-full bg-mk-lavender px-6 text-[14px] font-semibold text-black transition-transform hover:scale-[1.02]"
        >
          Post
        </Link>
      </div>

      <p className="mt-6 text-center text-[13px] text-muted-foreground">
        {piece.stats.comments === 0
          ? "No comments yet. Be the first."
          : "Sign in to read and join the conversation."}
      </p>
    </section>
  );
}
