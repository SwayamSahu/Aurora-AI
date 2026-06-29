"use client";

import { Check } from "lucide-react";

import { cn } from "@/lib/utils";
import { STYLE_PRESETS } from "@/lib/generation-options";

export function StylePresets({
  active,
  onToggle,
}: {
  active: Set<string>;
  onToggle: (id: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {STYLE_PRESETS.map((preset) => {
        const on = active.has(preset.id);
        return (
          <button
            key={preset.id}
            type="button"
            onClick={() => onToggle(preset.id)}
            aria-pressed={on}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
              on
                ? "border-primary bg-primary/10 text-primary"
                : "border-border hover:bg-accent/40",
            )}
          >
            {on ? (
              <Check className="size-3.5" />
            ) : (
              <span aria-hidden>{preset.emoji}</span>
            )}
            {preset.label}
          </button>
        );
      })}
    </div>
  );
}
