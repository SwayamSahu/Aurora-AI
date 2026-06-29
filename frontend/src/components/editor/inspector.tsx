"use client";

import * as React from "react";
import { SlidersHorizontal } from "lucide-react";

import type { Clip } from "@/lib/api/timeline";
import { findClip } from "@/lib/editor/helpers";
import { useEditorStore } from "@/lib/editor/store";
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
import { EmptyState } from "@/components/shared/empty-state";

function NumberField({
  label,
  value,
  step = 0.1,
  min = 0,
  onCommit,
  onStart,
  suffix,
}: {
  label: string;
  value: number;
  step?: number;
  min?: number;
  onCommit: (v: number) => void;
  onStart: () => void;
  suffix?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs">{label}</Label>
      <div className="relative">
        <Input
          type="number"
          step={step}
          min={min}
          defaultValue={value}
          key={value}
          onFocus={onStart}
          onChange={(e) => {
            const v = parseFloat(e.target.value);
            if (!Number.isNaN(v)) onCommit(v);
          }}
          className="h-8"
        />
        {suffix ? (
          <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-muted-foreground">
            {suffix}
          </span>
        ) : null}
      </div>
    </div>
  );
}

export function Inspector() {
  const document = useEditorStore((s) => s.document);
  const selectedClipId = useEditorStore((s) => s.selectedClipId);
  const updateClip = useEditorStore((s) => s.updateClip);
  const snapshot = useEditorStore((s) => s.snapshot);

  const clip: Clip | undefined = selectedClipId
    ? findClip(document, selectedClipId)
    : undefined;

  if (!clip) {
    return (
      <EmptyState
        icon={SlidersHorizontal}
        title="No clip selected"
        description="Select a clip on the timeline to edit its properties."
        className="py-10"
      />
    );
  }

  const set = (patch: Partial<Clip>) => updateClip(clip.id, patch, false);
  const setStyle = (patch: Record<string, unknown>) =>
    updateClip(clip.id, { style: { ...(clip.style ?? {}), ...patch } }, false);

  const style = clip.style ?? {};

  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm font-semibold capitalize">{clip.kind} clip</p>
        <p className="text-xs text-muted-foreground">Adjust placement & properties.</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <NumberField
          label="Start"
          value={Number(clip.start.toFixed(2))}
          onStart={snapshot}
          onCommit={(v) => set({ start: v })}
          suffix="s"
        />
        <NumberField
          label="Duration"
          value={Number(clip.duration.toFixed(2))}
          onStart={snapshot}
          onCommit={(v) => set({ duration: v })}
          suffix="s"
        />
      </div>

      {(clip.kind === "video" || clip.kind === "audio") && (
        <NumberField
          label="Trim start"
          value={Number(clip.trim_start.toFixed(2))}
          onStart={snapshot}
          onCommit={(v) => set({ trim_start: v })}
          suffix="s"
        />
      )}

      {clip.kind === "video" && (
        <div className="space-y-1.5">
          <Label className="text-xs">Transition in</Label>
          <Select
            value={clip.transition_in ?? "none"}
            onValueChange={(v) => {
              snapshot();
              set({ transition_in: v === "none" ? null : v });
            }}
          >
            <SelectTrigger className="h-8">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None (hard cut)</SelectItem>
              <SelectItem value="fade">Fade</SelectItem>
              <SelectItem value="dissolve">Dissolve</SelectItem>
              <SelectItem value="wipeleft">Wipe Left</SelectItem>
              <SelectItem value="wiperight">Wipe Right</SelectItem>
              <SelectItem value="slideleft">Slide Left</SelectItem>
              <SelectItem value="slideright">Slide Right</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

      {clip.kind === "text" && (
        <div className="space-y-4 border-t border-border pt-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Text</Label>
            <Textarea
              value={clip.text ?? ""}
              onFocus={snapshot}
              onChange={(e) => set({ text: e.target.value })}
              className="min-h-16"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <NumberField
              label="Font size"
              value={Number(style.fontSize ?? 48)}
              step={1}
              min={8}
              onStart={snapshot}
              onCommit={(v) => setStyle({ fontSize: v })}
            />
            <div className="space-y-1.5">
              <Label className="text-xs">Color</Label>
              <Input
                type="color"
                value={(style.color as string) ?? "#ffffff"}
                onFocus={snapshot}
                onChange={(e) => setStyle({ color: e.target.value })}
                className="h-8 p-1"
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs">Alignment</Label>
            <Select
              value={(style.align as string) ?? "center"}
              onValueChange={(v) => {
                snapshot();
                setStyle({ align: v });
              }}
            >
              <SelectTrigger className="h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="left">Left</SelectItem>
                <SelectItem value="center">Center</SelectItem>
                <SelectItem value="right">Right</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <NumberField
            label="Vertical position"
            value={Number(style.y ?? 50)}
            step={1}
            min={0}
            onStart={snapshot}
            onCommit={(v) => setStyle({ y: Math.max(0, Math.min(100, v)) })}
            suffix="%"
          />
        </div>
      )}
    </div>
  );
}
