"use client";

import * as React from "react";
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";
import type { VideoModelSpec } from "@/lib/api/generation";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

/** Badges that get a colored (accent) treatment; everything else is neutral. */
const ACCENT_BADGES = new Set(["NEW", "EXCLUSIVE", "4K"]);

interface Props {
  models: VideoModelSpec[];
  value: string;
  onChange: (modelId: string) => void;
  loading?: boolean;
}

/** The Studio model picker: a scrollable grid of model cards with provider,
 * resolution and duration-range badges — the multi-model selector that
 * mirrors leading AI-video platforms. */
export function ModelGallery({ models, value, onChange, loading }: Props) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-[74px] w-full rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="max-h-72 grid grid-cols-2 gap-2 overflow-y-auto pr-1">
      {models.map((m) => {
        const selected = m.id === value;
        return (
          <button
            key={m.id}
            type="button"
            onClick={() => onChange(m.id)}
            aria-pressed={selected}
            title={`${m.label} — ${m.provider}`}
            className={cn(
              "relative flex flex-col gap-1 rounded-lg border p-2.5 text-left transition-colors",
              selected
                ? "border-primary bg-accent/40"
                : "border-border hover:bg-accent/30",
            )}
          >
            {selected ? (
              <Check className="absolute right-2 top-2 size-3.5 text-primary" />
            ) : null}
            <span className="truncate pr-4 text-sm font-medium leading-tight">
              {m.label}
            </span>
            <span className="truncate text-[11px] text-muted-foreground">
              {m.provider}
            </span>
            <div className="mt-0.5 flex flex-wrap items-center gap-1">
              <Badge variant="outline" className="px-1 py-0 text-[10px]">
                {m.resolution}
              </Badge>
              <Badge variant="outline" className="px-1 py-0 text-[10px]">
                {m.min_duration}–{m.max_duration}s
              </Badge>
              <Badge variant="outline" className="px-1 py-0 text-[10px]">
                {m.credit_cost} cr
              </Badge>
              {m.badges.map((b) => (
                <Badge
                  key={b}
                  variant={ACCENT_BADGES.has(b) ? "secondary" : "outline"}
                  className="px-1 py-0 text-[10px]"
                >
                  {b}
                </Badge>
              ))}
            </div>
          </button>
        );
      })}
    </div>
  );
}
