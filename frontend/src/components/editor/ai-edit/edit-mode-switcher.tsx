"use client";

import { Clapperboard, Wand2 } from "lucide-react";

import { cn } from "@/lib/utils";

export type EditorMode = "timeline" | "ai-edit";

/** Segmented control switching the editor between Timeline and AI Edit. */
export function EditModeSwitcher({
  mode,
  onMode,
}: {
  mode: EditorMode;
  onMode: (m: EditorMode) => void;
}) {
  const base =
    "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors";
  return (
    <div
      role="tablist"
      aria-label="Editor mode"
      className="inline-flex items-center gap-1 rounded-lg border bg-card p-1"
    >
      <button
        type="button"
        role="tab"
        aria-selected={mode === "timeline"}
        onClick={() => onMode("timeline")}
        className={cn(
          base,
          mode === "timeline"
            ? "bg-primary text-primary-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground",
        )}
      >
        <Clapperboard className="size-4" /> Timeline
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={mode === "ai-edit"}
        onClick={() => onMode("ai-edit")}
        className={cn(
          base,
          mode === "ai-edit"
            ? "bg-primary text-primary-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground",
        )}
      >
        <Wand2 className="size-4" /> AI Edit
      </button>
    </div>
  );
}
