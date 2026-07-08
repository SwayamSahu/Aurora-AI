"use client";

import * as React from "react";

import { cn } from "@/lib/utils";
import {
  EDIT_CATEGORIES,
  type EditPreset,
  presetsByCategory,
} from "@/lib/editor/ai-edit/presets";
import { landingIcon } from "@/lib/landing/icon-map";
import { ScrollArea } from "@/components/ui/scroll-area";

/**
 * Browsable, data-driven catalog of every AI edit preset, grouped by
 * category tabs. Selecting a preset configures the prompt panel.
 */
export function PresetGallery({
  selected,
  onSelect,
}: {
  selected: EditPreset | null;
  onSelect: (p: EditPreset) => void;
}) {
  const [category, setCategory] = React.useState(EDIT_CATEGORIES[0].id);
  const presets = presetsByCategory(category);

  return (
    <div>
      {/* Category tabs */}
      <div className="flex flex-wrap gap-1">
        {EDIT_CATEGORIES.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => setCategory(c.id)}
            aria-pressed={category === c.id}
            className={cn(
              "inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-medium transition-colors",
              category === c.id
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border text-muted-foreground hover:text-foreground",
            )}
          >
            {React.createElement(landingIcon(c.icon), { className: "size-3" })}
            {c.label}
          </button>
        ))}
      </div>

      {/* Preset chips */}
      <ScrollArea className="mt-3 h-40 pr-2">
        <div className="flex flex-wrap gap-1.5">
          {presets.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelect(p)}
              aria-pressed={selected?.id === p.id}
              className={cn(
                "rounded-lg border px-2.5 py-1.5 text-left text-xs transition-colors",
                selected?.id === p.id
                  ? "border-primary bg-accent text-accent-foreground"
                  : "border-border text-foreground/85 hover:bg-accent/50",
              )}
            >
              {p.label}
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
