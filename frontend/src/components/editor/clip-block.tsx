"use client";

import * as React from "react";
import { Music, Captions, Video as VideoIcon, Image as ImageIcon } from "lucide-react";

import type { Clip } from "@/lib/api/timeline";
import { cn } from "@/lib/utils";
import { MIN_CLIP_DURATION, snapTime } from "@/lib/editor/helpers";
import { useEditorStore } from "@/lib/editor/store";
import { useAsset } from "@/components/editor/assets-context";
import { assetContentUrl } from "@/lib/api/assets";

type DragMode = "move" | "trim-left" | "trim-right";

const KIND_ICON = {
  video: VideoIcon,
  image: ImageIcon,
  audio: Music,
  text: Captions,
};

export function ClipBlock({
  clip,
  snapTargets,
}: {
  clip: Clip;
  snapTargets: number[];
}) {
  const pxPerSec = useEditorStore((s) => s.pxPerSec);
  const selected = useEditorStore((s) => s.selectedClipId === clip.id);
  const selectClip = useEditorStore((s) => s.selectClip);
  const updateClip = useEditorStore((s) => s.updateClip);
  const removeClip = useEditorStore((s) => s.removeClip);
  const snapshot = useEditorStore((s) => s.snapshot);
  const asset = useAsset(clip.asset_id);

  const sourceDuration = asset?.duration_seconds ?? null;
  const Icon = KIND_ICON[clip.kind];
  const label = clip.kind === "text" ? clip.text || "Text" : asset?.name ?? clip.kind;

  const startDrag = (mode: DragMode) => (e: React.PointerEvent) => {
    e.preventDefault();
    e.stopPropagation();
    selectClip(clip.id);
    snapshot(); // one history entry per interaction

    const startX = e.clientX;
    const orig = { start: clip.start, duration: clip.duration, trim: clip.trim_start };
    const threshold = 8 / pxPerSec;

    const onMove = (ev: PointerEvent) => {
      const deltaSec = (ev.clientX - startX) / pxPerSec;

      if (mode === "move") {
        let next = Math.max(0, orig.start + deltaSec);
        next = snapTime(next, snapTargets, threshold);
        updateClip(clip.id, { start: next }, false);
        return;
      }

      if (mode === "trim-left") {
        let newStart = Math.max(0, orig.start + deltaSec);
        newStart = snapTime(newStart, snapTargets, threshold);
        let delta = newStart - orig.start;
        // Bound so duration and trim stay valid.
        if (orig.duration - delta < MIN_CLIP_DURATION)
          delta = orig.duration - MIN_CLIP_DURATION;
        if (orig.trim + delta < 0) delta = -orig.trim;
        updateClip(
          clip.id,
          {
            start: orig.start + delta,
            duration: orig.duration - delta,
            trim_start: orig.trim + delta,
          },
          false,
        );
        return;
      }

      // trim-right
      let end = orig.start + orig.duration + deltaSec;
      end = snapTime(end, snapTargets, threshold);
      let newDuration = Math.max(MIN_CLIP_DURATION, end - orig.start);
      if (sourceDuration != null) {
        newDuration = Math.min(newDuration, sourceDuration - orig.trim);
      }
      updateClip(clip.id, { duration: newDuration }, false);
    };

    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  };

  const left = clip.start * pxPerSec;
  const width = Math.max(8, clip.duration * pxPerSec);
  const showThumb =
    (clip.kind === "video" || clip.kind === "image") && asset != null;

  const transitionLabel =
    clip.kind === "video" &&
    clip.transition_in &&
    clip.transition_in !== "none"
      ? clip.transition_in.slice(0, 5)
      : null;

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label={`${clip.kind} clip: ${label}, ${clip.duration.toFixed(1)}s${transitionLabel ? `, transition: ${clip.transition_in}` : ""}`}
      aria-pressed={selected}
      onPointerDown={startDrag("move")}
      onClick={(e) => {
        e.stopPropagation();
        selectClip(clip.id);
      }}
      onKeyDown={(e) => {
        if (e.key === "Delete" || e.key === "Backspace") {
          e.preventDefault();
          snapshot();
          removeClip(clip.id);
        } else if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          selectClip(clip.id);
        }
      }}
      style={{ left, width }}
      className={cn(
        "group absolute top-1 bottom-1 flex cursor-grab items-stretch overflow-hidden rounded-md border text-xs active:cursor-grabbing",
        selected
          ? "border-primary ring-2 ring-primary/40 z-10"
          : "border-border",
        clip.kind === "text" && "bg-primary/15",
        clip.kind === "audio" && "bg-success/15",
        (clip.kind === "video" || clip.kind === "image") && "bg-accent/40",
      )}
    >
      {/* Left trim handle */}
      <span
        onPointerDown={startDrag("trim-left")}
        className="absolute left-0 top-0 z-20 h-full w-1.5 cursor-ew-resize bg-primary/0 group-hover:bg-primary/60"
      />

      {showThumb ? (
        <div className="h-full w-10 shrink-0 overflow-hidden bg-black/20">
          {clip.kind === "image" ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={assetContentUrl(asset!)} alt="" className="size-full object-cover" />
          ) : (
            <video
              src={assetContentUrl(asset!)}
              muted
              preload="metadata"
              className="size-full object-cover"
            />
          )}
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 items-center gap-1 px-1.5">
        <Icon className="size-3 shrink-0 opacity-70" />
        <span className="truncate">{label}</span>
      </div>

      {/* Transition-in badge */}
      {transitionLabel ? (
        <span className="absolute left-0 bottom-0 z-30 rounded-tr bg-primary/80 px-1 py-px text-[9px] uppercase leading-none text-primary-foreground">
          {transitionLabel}
        </span>
      ) : null}

      {/* Right trim handle */}
      <span
        onPointerDown={startDrag("trim-right")}
        className="absolute right-0 top-0 z-20 h-full w-1.5 cursor-ew-resize bg-primary/0 group-hover:bg-primary/60"
      />
    </div>
  );
}
