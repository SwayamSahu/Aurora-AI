"use client";

import * as React from "react";
import { Wand2, Image as ImageIcon, Sparkles, Dices } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  DURATIONS,
  RESOLUTIONS,
  VIDEO_MODELS,
} from "@/lib/generation-options";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { StylePresets } from "@/components/studio/style-presets";

export type GenerationType = "generate_video" | "generate_image";

export interface ComposerState {
  type: GenerationType;
  prompt: string;
  negativePrompt: string;
  model: string;
  resolution: string;
  duration: string;
  seed: string;
  presets: Set<string>;
}

export const initialComposerState = (
  type: GenerationType = "generate_video",
): ComposerState => ({
  type,
  prompt: "",
  negativePrompt: "",
  model: VIDEO_MODELS[0].value,
  resolution: "768x512",
  duration: "4",
  seed: "",
  presets: new Set(),
});

const TYPES: { value: GenerationType; label: string; icon: typeof Wand2 }[] = [
  { value: "generate_video", label: "Text → Video", icon: Wand2 },
  { value: "generate_image", label: "Text → Image", icon: ImageIcon },
];

interface Props {
  state: ComposerState;
  onChange: (patch: Partial<ComposerState>) => void;
  onGenerate: () => void;
  busy: boolean;
}

export function PromptComposer({ state, onChange, onGenerate, busy }: Props) {
  const isVideo = state.type === "generate_video";

  function togglePreset(id: string) {
    const next = new Set(state.presets);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange({ presets: next });
  }

  return (
    <div className="space-y-5">
      {/* Type */}
      <div className="grid grid-cols-2 gap-2">
        {TYPES.map((t) => (
          <button
            key={t.value}
            type="button"
            onClick={() => onChange({ type: t.value })}
            className={cn(
              "flex items-center justify-center gap-2 rounded-lg border p-3 text-sm font-medium transition-colors",
              state.type === t.value
                ? "border-primary bg-accent/40"
                : "border-border hover:bg-accent/30",
            )}
          >
            <t.icon className="size-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Prompt */}
      <div className="space-y-1.5">
        <Label htmlFor="prompt">Prompt</Label>
        <Textarea
          id="prompt"
          value={state.prompt}
          onChange={(e) => onChange({ prompt: e.target.value })}
          placeholder="A cinematic drone shot over a misty forest at dawn, golden light…"
          className="min-h-28 resize-none"
        />
      </div>

      {/* Style presets */}
      <div className="space-y-2">
        <Label>Style</Label>
        <StylePresets active={state.presets} onToggle={togglePreset} />
      </div>

      {/* Negative prompt */}
      <div className="space-y-1.5">
        <Label htmlFor="negative">Negative prompt (optional)</Label>
        <Input
          id="negative"
          value={state.negativePrompt}
          onChange={(e) => onChange({ negativePrompt: e.target.value })}
          placeholder="blurry, distorted, watermark"
        />
      </div>

      {/* Video-only controls */}
      {isVideo ? (
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2 space-y-1.5">
            <Label>Model</Label>
            <Select value={state.model} onValueChange={(v) => onChange({ model: v })}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {VIDEO_MODELS.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Resolution</Label>
            <Select
              value={state.resolution}
              onValueChange={(v) => onChange({ resolution: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {RESOLUTIONS.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Duration</Label>
            <Select
              value={state.duration}
              onValueChange={(v) => onChange({ duration: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DURATIONS.map((d) => (
                  <SelectItem key={d.value} value={d.value}>
                    {d.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      ) : null}

      {/* Seed */}
      <div className="space-y-1.5">
        <Label htmlFor="seed">Seed (optional)</Label>
        <div className="flex gap-2">
          <Input
            id="seed"
            value={state.seed}
            inputMode="numeric"
            onChange={(e) =>
              onChange({ seed: e.target.value.replace(/[^0-9]/g, "") })
            }
            placeholder="Random"
          />
          <Button
            type="button"
            variant="outline"
            size="icon"
            aria-label="Randomize seed"
            onClick={() =>
              onChange({ seed: String(Math.floor(Math.random() * 1_000_000)) })
            }
          >
            <Dices className="size-4" />
          </Button>
        </div>
      </div>

      <Button
        className="w-full"
        size="lg"
        onClick={onGenerate}
        loading={busy}
        disabled={!state.prompt.trim()}
      >
        <Sparkles className="size-4" /> Generate
      </Button>
    </div>
  );
}
