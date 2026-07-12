"use client";

import * as React from "react";
import { toast } from "sonner";
import { Sparkles, Wand2 } from "lucide-react";

import {
  type EditPreset,
  MAGIC_PROMPT_PRESET,
  needsPaintedMask,
  needsPromptInput,
  resolvePrompt,
} from "@/lib/editor/ai-edit/presets";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { PresetGallery } from "@/components/editor/ai-edit/preset-gallery";

const MASK_MODE_HINT: Record<string, string> = {
  painted: "Paint the region to edit",
  "auto-subject": "Auto-selects the main subject",
  "auto-face": "Auto-selects face(s)",
  "auto-hair": "Auto-selects hair",
  "auto-clothing": "Auto-selects clothing",
  "auto-sky": "Auto-selects the sky",
  "auto-background": "Auto-selects the background",
  "auto-text": "Auto-detects on-screen text",
  "full-frame": "Applies to the whole clip",
};

/**
 * Right-hand AI Edit panel: preset catalog + prompt box + apply. In E1 the
 * apply step queues a local draft (the edit-layer backend lands in E2).
 */
export interface AppliedEdit {
  engine: string;
  presetId: string;
  label: string;
  prompt: string;
  params?: Record<string, unknown>;
}

export function PromptPanel({
  hasInk,
  applying,
  onApply,
}: {
  hasInk: boolean;
  applying: boolean;
  onApply: (edit: AppliedEdit) => void;
}) {
  const [preset, setPreset] = React.useState<EditPreset | null>(null);
  const [text, setText] = React.useState("");

  const activePreset = preset ?? MAGIC_PROMPT_PRESET;
  const wantsText = needsPromptInput(activePreset);
  const wantsMask = needsPaintedMask(activePreset);
  const missingMask = wantsMask && !hasInk;
  const missingText = wantsText && !text.trim();

  function apply() {
    if (missingMask) {
      toast.error("Paint a selection first — this edit needs a region.");
      return;
    }
    if (missingText) {
      toast.error("Describe the change in the prompt box.");
      return;
    }
    onApply({
      engine: activePreset.engine,
      presetId: activePreset.id,
      label: activePreset.label,
      prompt: resolvePrompt(activePreset, text),
      params: activePreset.params,
    });
    setText("");
  }

  return (
    <div className="space-y-4">
      <div>
        <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <Wand2 className="size-3.5" /> Presets
        </p>
        <PresetGallery
          selected={preset}
          onSelect={(p) => setPreset(p.id === preset?.id ? null : p)}
        />
      </div>

      <div>
        <div className="mb-2 flex items-center justify-between">
          <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            <Sparkles className="size-3.5" />
            {preset ? preset.label : "Magic prompt"}
          </p>
          <Badge variant="secondary" className="text-[10px]">
            {MASK_MODE_HINT[activePreset.maskMode]}
          </Badge>
        </div>
        <Textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          placeholder={
            preset
              ? wantsText
                ? "Describe the change — e.g. “a yellow Ferrari”"
                : "Optional: refine the preset…"
              : "Describe any edit — e.g. “make this scene cinematic”"
          }
        />
      </div>

      <Button className="w-full" onClick={apply} loading={applying}>
        Apply edit
      </Button>
      <p className="text-center text-[11px] text-muted-foreground">
        Edits queue as non-destructive layers on this clip.
      </p>
    </div>
  );
}
