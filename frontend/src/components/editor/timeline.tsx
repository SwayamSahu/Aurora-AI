"use client";

import * as React from "react";
import { Music, Captions, Film, VolumeX } from "lucide-react";

import { cn } from "@/lib/utils";
import { useEditorStore } from "@/lib/editor/store";
import { totalDuration } from "@/lib/editor/helpers";
import {
  RULER_HEIGHT,
  TRACK_HEIGHT,
  TrackRow,
} from "@/components/editor/track-row";

const TRACK_ICON = { video: Film, text: Captions, audio: Music };
const HEADER_WIDTH = 112;

function Ruler({ seconds, pxPerSec }: { seconds: number; pxPerSec: number }) {
  // A tick every second; label every 5s (or every second if zoomed in).
  const step = pxPerSec >= 80 ? 1 : pxPerSec >= 40 ? 2 : 5;
  const ticks: number[] = [];
  for (let s = 0; s <= seconds; s += step) ticks.push(s);
  return (
    <div
      className="relative border-b border-border bg-muted/30"
      style={{ height: RULER_HEIGHT }}
    >
      {ticks.map((s) => (
        <div
          key={s}
          className="absolute top-0 h-full border-l border-border/70 pl-1 text-[10px] text-muted-foreground"
          style={{ left: s * pxPerSec }}
        >
          {s}s
        </div>
      ))}
    </div>
  );
}

export function Timeline() {
  const document = useEditorStore((s) => s.document);
  const pxPerSec = useEditorStore((s) => s.pxPerSec);
  const playhead = useEditorStore((s) => s.playhead);
  const setPlayhead = useEditorStore((s) => s.setPlayhead);
  const selectClip = useEditorStore((s) => s.selectClip);

  const lanesRef = React.useRef<HTMLDivElement>(null);

  const total = totalDuration(document);
  const visibleSeconds = Math.max(total + 5, 20);
  const contentWidth = visibleSeconds * pxPerSec;

  // Snap targets: timeline start, playhead, and every clip edge.
  const snapTargets = React.useMemo(() => {
    const targets = [0, playhead];
    for (const t of document.tracks)
      for (const c of t.clips) targets.push(c.start, c.start + c.duration);
    return targets;
  }, [document, playhead]);

  function seekFromEvent(clientX: number) {
    const el = lanesRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = clientX - rect.left + el.scrollLeft;
    setPlayhead(Math.max(0, x / pxPerSec));
  }

  function startPlayheadDrag(e: React.PointerEvent) {
    e.preventDefault();
    seekFromEvent(e.clientX);
    const onMove = (ev: PointerEvent) => seekFromEvent(ev.clientX);
    const onUp = () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
  }

  return (
    <div className="flex overflow-hidden rounded-xl border border-border bg-card">
      {/* Track headers */}
      <div className="shrink-0 border-r border-border" style={{ width: HEADER_WIDTH }}>
        <div style={{ height: RULER_HEIGHT }} className="border-b border-border" />
        {document.tracks.map((track) => {
          const Icon = TRACK_ICON[track.type];
          return (
            <div
              key={track.id}
              className="flex items-center gap-2 border-b border-border/60 px-3 text-xs font-medium"
              style={{ height: TRACK_HEIGHT }}
            >
              <Icon className="size-3.5 text-muted-foreground" />
              <span className="truncate">{track.name}</span>
              {track.muted ? (
                <VolumeX className="ml-auto size-3.5 text-muted-foreground" />
              ) : null}
            </div>
          );
        })}
      </div>

      {/* Lanes (scrollable) */}
      <div ref={lanesRef} className="relative flex-1 overflow-x-auto scrollbar-thin">
        <div
          style={{ width: contentWidth }}
          className="relative"
          onPointerDown={(e) => {
            // Click on empty lane area: seek + clear selection.
            if (e.target === e.currentTarget) {
              selectClip(null);
            }
          }}
        >
          <div onPointerDown={startPlayheadDrag} className="cursor-text">
            <Ruler seconds={visibleSeconds} pxPerSec={pxPerSec} />
          </div>

          {document.tracks.map((track) => (
            <TrackRow key={track.id} track={track} snapTargets={snapTargets} />
          ))}

          {/* Playhead */}
          <div
            className="pointer-events-none absolute top-0 z-30 w-px bg-primary"
            style={{
              left: playhead * pxPerSec,
              height:
                RULER_HEIGHT + document.tracks.length * TRACK_HEIGHT,
            }}
          >
            <div
              className={cn(
                "absolute -left-1.5 -top-0 size-3 rounded-sm bg-primary",
              )}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
