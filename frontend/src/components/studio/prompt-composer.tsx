"use client";

import * as React from "react";
import { Wand2, Image as ImageIcon, Sparkles, Dices, Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  ASPECT_RATIOS,
  clampDurationToModel,
  DEFAULT_ASPECT_RATIO,
  DEFAULT_VIDEO_MODEL_ID,
  durationOptionsFor,
} from "@/lib/generation-options";
import { useVideoModels } from "@/lib/query/generation";
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
import { ModelGallery } from "@/components/studio/model-gallery";

export type GenerationType = "generate_video" | "generate_image";

export interface ComposerState {
  type: GenerationType;
  prompt: string;
  negativePrompt: string;
  model: string;
  aspect: string;
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
  model: DEFAULT_VIDEO_MODEL_ID,
  aspect: DEFAULT_ASPECT_RATIO,
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
  const [enhancing, setEnhancing] = React.useState(false);

  const modelsQuery = useVideoModels();
  const models = modelsQuery.data ?? [];
  const selectedSpec = models.find((m) => m.id === state.model);
  const durationOptions = durationOptionsFor(selectedSpec);

  // Picking a model re-validates the duration against its capability range.
  function handleModelChange(modelId: string) {
    const spec = models.find((m) => m.id === modelId);
    onChange({ model: modelId, duration: clampDurationToModel(state.duration, spec) });
  }

  function togglePreset(id: string) {
    const next = new Set(state.presets);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange({ presets: next });
  }

  async function handleEnhance() {
    if (!state.prompt.trim() || enhancing) return;
    setEnhancing(true);
    try {
      const res = await fetch("/api/enhance-prompt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: state.prompt, type: state.type }),
      });
      if (res.ok) {
        const data = await res.json();
        onChange({ prompt: data.enhanced });
      }
    } finally {
      setEnhancing(false);
    }
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
        <div className="relative">
          <Textarea
            id="prompt"
            value={state.prompt}
            onChange={(e) => onChange({ prompt: e.target.value })}
            placeholder="A cinematic drone shot over a misty forest at dawn, golden light…"
            className="min-h-28 resize-none pb-9"
          />
          <button
            type="button"
            onClick={handleEnhance}
            disabled={!state.prompt.trim() || enhancing}
            className={cn(
              "absolute bottom-2 left-2 flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-all",
              "border border-border/60 bg-background/80 backdrop-blur-sm",
              "text-muted-foreground hover:text-foreground hover:border-primary/50 hover:bg-accent/60",
              "disabled:opacity-40 disabled:cursor-not-allowed",
            )}
          >
            {enhancing ? (
              <Loader2 className="size-3 animate-spin" />
            ) : (
              <Sparkles className="size-3" />
            )}
            {enhancing ? "Enhancing…" : "Enhance prompt"}
          </button>
        </div>
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

      {/* Video-only: model gallery */}
      {isVideo ? (
        <div className="space-y-1.5">
          <Label>Model</Label>
          <ModelGallery
            models={models}
            value={state.model}
            onChange={handleModelChange}
            loading={modelsQuery.isLoading}
          />
        </div>
      ) : null}

      {/* Aspect ratio — applies to both video and image generation */}
      <div className={cn("grid gap-3", isVideo ? "grid-cols-2" : "grid-cols-1")}>
        <div className="space-y-1.5">
          <Label>Aspect ratio</Label>
          <Select value={state.aspect} onValueChange={(v) => onChange({ aspect: v })}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ASPECT_RATIOS.map((a) => (
                <SelectItem key={a.id} value={a.id}>
                  {a.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {isVideo ? (
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
                {durationOptions.map((d) => (
                  <SelectItem key={d.value} value={d.value}>
                    {d.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : null}
      </div>

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
