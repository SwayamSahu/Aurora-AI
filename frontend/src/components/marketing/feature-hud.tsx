"use client";

import * as React from "react";

import { cn } from "@/lib/utils";
import { featureHud } from "@/lib/landing/content";

/** Number of bars in the faux voice waveform. */
const WAVE_BARS = 24;

/**
 * Context-aware "app HUD" pinned to the bottom of a feature-tab visual.
 * It dresses the preview as the live product: a prompt rendering with a
 * progress bar, a voice waveform, or a caption/timeline timecode.
 */
export function FeatureHud({ tabId }: { tabId: string }) {
  const hud = featureHud[tabId];
  if (!hud) return null;

  return (
    <div className="absolute inset-x-0 bottom-0 flex h-16 items-center gap-3 border-t border-border bg-background/65 px-5 backdrop-blur-md">
      {/* Status + prompt/transcript line */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-primary">
          <span className="relative flex size-1.5">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary/70" />
            <span className="relative inline-flex size-1.5 rounded-full bg-primary" />
          </span>
          {hud.status}
        </div>
        <p className="mt-1 truncate font-mono text-xs text-foreground/75">
          {hud.line}
        </p>
      </div>

      {/* Right-hand control */}
      <div className="shrink-0">
        {hud.kind === "progress" ? (
          <ProgressControl value={Number(hud.value) || 0} meta={hud.meta} />
        ) : hud.kind === "waveform" ? (
          <WaveformControl meta={hud.meta} />
        ) : (
          <TimecodeControl value={String(hud.value ?? "")} meta={hud.meta} />
        )}
      </div>
    </div>
  );
}

function ProgressControl({ value, meta }: { value: number; meta?: string }) {
  // Animate the fill from 0 to `value` when the control mounts (tab switch).
  const [width, setWidth] = React.useState(0);
  React.useEffect(() => {
    const id = requestAnimationFrame(() => setWidth(value));
    return () => cancelAnimationFrame(id);
  }, [value]);

  return (
    <div className="w-32">
      <div className="mb-1 flex items-center justify-between font-mono text-[10px] text-muted-foreground">
        <span>{meta}</span>
        <span className="tabular-nums text-foreground/80">{value}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-muted-foreground/20">
        <div
          className="h-full rounded-full bg-gradient-to-r from-primary to-[oklch(0.62_0.2_320)] transition-[width] duration-1000 ease-out motion-reduce:transition-none"
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

function WaveformControl({ meta }: { meta?: string }) {
  // Deterministic pseudo-random heights so SSR and client match.
  const heights = React.useMemo(
    () =>
      Array.from({ length: WAVE_BARS }, (_, i) =>
        Math.round(30 + 65 * Math.abs(Math.sin(i * 1.3) * Math.cos(i * 0.7))),
      ),
    [],
  );

  return (
    <div className="flex items-center gap-3">
      <div className="flex h-8 items-end gap-[3px]">
        {heights.map((h, i) => (
          <span
            key={i}
            className="w-[3px] origin-bottom rounded-full bg-gradient-to-t from-primary/60 to-primary motion-safe:animate-[voice-wave_1.1s_ease-in-out_infinite]"
            style={{
              height: `${h}%`,
              animationDelay: `${(i % 6) * 0.09}s`,
            }}
          />
        ))}
      </div>
      {meta ? (
        <span className="font-mono text-[10px] tabular-nums text-muted-foreground">
          {meta}
        </span>
      ) : null}
    </div>
  );
}

function TimecodeControl({ value, meta }: { value: string; meta?: string }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md border border-border bg-background/70 px-2 py-1",
          "font-mono text-xs tabular-nums text-foreground/85",
        )}
      >
        <span className="size-1.5 rounded-full bg-primary" />
        {value}
      </span>
      {meta ? (
        <span className="rounded-md bg-accent px-2 py-1 font-mono text-[10px] font-medium text-accent-foreground">
          {meta}
        </span>
      ) : null}
    </div>
  );
}
