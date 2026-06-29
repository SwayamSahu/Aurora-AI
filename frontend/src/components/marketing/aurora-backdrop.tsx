"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Aurora's signature animated gradient mesh — soft, drifting colour blobs
 * behind the hero. Pure CSS animation (GPU-friendly), theme-aware via the
 * brand primary tokens, and disabled under prefers-reduced-motion.
 */
export function AuroraBackdrop({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 -z-10 overflow-hidden",
        className,
      )}
    >
      {/* Drifting colour blobs */}
      <div className="aurora-blob aurora-blob--a" />
      <div className="aurora-blob aurora-blob--b" />
      <div className="aurora-blob aurora-blob--c" />

      {/* Fine grid overlay for depth */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,var(--border)_1px,transparent_1px),linear-gradient(to_bottom,var(--border)_1px,transparent_1px)] bg-[size:64px_64px] opacity-[0.18] [mask-image:radial-gradient(ellipse_at_center,black_30%,transparent_75%)]" />

      {/* Fade to background at the bottom for a clean section seam */}
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-b from-transparent to-background" />
    </div>
  );
}
