"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowRight, ChevronDown, Lock } from "lucide-react";

import { cn } from "@/lib/utils";
import type { Piece } from "@/lib/marketplace/mock-pieces";

const SECONDARY = ["Save", "Repost", "Pin to board", "Share"];

export function ActionBar({ piece, pulse }: { piece: Piece; pulse?: boolean }) {
  const [showDetails, setShowDetails] = React.useState(false);
  const sold = piece.status === "sold";

  return (
    <div className="mt-8">
      <div className="flex flex-wrap items-center gap-3">
        <Link
          href="/signup"
          className={cn(
            "group inline-flex h-12 items-center gap-2 rounded-full px-6 text-[14px] font-bold uppercase tracking-[1px] text-black transition-transform hover:scale-[1.02]",
            pulse && "[animation:mk-pulse_1.4s_ease-out_1]",
            sold && "pointer-events-none opacity-50",
          )}
          style={{ background: "var(--mk-grad-make-yours)" }}
        >
          {sold ? "Sold out" : "Make this yours"}
          <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
        </Link>

        {SECONDARY.map((label) => (
          <Link
            key={label}
            href="/signup"
            className="inline-flex h-12 items-center rounded-full bg-[var(--mk-surface-2)] px-5 text-[13px] font-bold uppercase tracking-[1px] text-foreground transition-colors hover:bg-[var(--mk-surface-hover)]"
          >
            {label}
          </Link>
        ))}
      </div>

      <button
        type="button"
        onClick={() => setShowDetails((v) => !v)}
        aria-expanded={showDetails}
        className="mt-4 inline-flex h-10 items-center gap-2 rounded-full bg-[var(--mk-surface-2)] px-5 text-[13px] font-bold uppercase tracking-[1px] text-foreground transition-colors hover:bg-[var(--mk-surface-hover)]"
      >
        Details
        <ChevronDown
          className={cn("size-4 transition-transform", showDetails && "rotate-180")}
        />
      </button>

      {showDetails ? (
        <div className="mt-4 rounded-2xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-5">
          <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-[13px]">
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Type</dt>
              <dd className="font-mono">{piece.type}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Resolution</dt>
              <dd className="font-mono">
                {piece.width}×{piece.height}
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Model</dt>
              <dd className="inline-flex items-center gap-1.5 font-mono text-muted-foreground">
                <Lock className="size-3" /> hidden
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Seed</dt>
              <dd className="inline-flex items-center gap-1.5 font-mono text-muted-foreground">
                <Lock className="size-3" /> hidden
              </dd>
            </div>
          </dl>
          <Link
            href="/signup"
            className="mt-4 inline-flex items-center gap-1.5 text-[13px] font-semibold text-mk-lavender hover:underline"
          >
            <Lock className="size-3.5" />
            Sign in to reveal the full prompt, model and seed
          </Link>
        </div>
      ) : null}
    </div>
  );
}
