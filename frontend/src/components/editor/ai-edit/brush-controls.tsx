"use client";

import type { BrushSettings } from "@/lib/editor/ai-edit/mask";
import { Label } from "@/components/ui/label";

function Slider({
  id,
  label,
  min,
  max,
  step,
  value,
  format,
  onChange,
}: {
  id: string;
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  format: (v: number) => string;
  onChange: (v: number) => void;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <Label htmlFor={id} className="text-xs text-muted-foreground">
          {label}
        </Label>
        <span className="font-mono text-[11px] tabular-nums text-muted-foreground">
          {format(value)}
        </span>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-muted accent-primary"
      />
    </div>
  );
}

export function BrushControls({
  brush,
  onChange,
}: {
  brush: BrushSettings;
  onChange: (b: BrushSettings) => void;
}) {
  const set = <K extends keyof BrushSettings>(k: K, v: number) =>
    onChange({ ...brush, [k]: v });

  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-3">
      <Slider
        id="brush-size"
        label="Size"
        min={4}
        max={200}
        step={1}
        value={brush.size}
        format={(v) => `${v}px`}
        onChange={(v) => set("size", v)}
      />
      <Slider
        id="brush-hardness"
        label="Hardness"
        min={0}
        max={1}
        step={0.05}
        value={brush.hardness}
        format={(v) => `${Math.round(v * 100)}%`}
        onChange={(v) => set("hardness", v)}
      />
      <Slider
        id="brush-opacity"
        label="Opacity"
        min={0.1}
        max={1}
        step={0.05}
        value={brush.opacity}
        format={(v) => `${Math.round(v * 100)}%`}
        onChange={(v) => set("opacity", v)}
      />
      <Slider
        id="brush-feather"
        label="Feather"
        min={0}
        max={40}
        step={1}
        value={brush.feather}
        format={(v) => `${v}px`}
        onChange={(v) => set("feather", v)}
      />
    </div>
  );
}
