"use client";

import type { Track } from "@/lib/api/timeline";
import { ClipBlock } from "@/components/editor/clip-block";

export const TRACK_HEIGHT = 56;
export const RULER_HEIGHT = 28;

export function TrackRow({
  track,
  snapTargets,
}: {
  track: Track;
  snapTargets: number[];
}) {
  return (
    <div
      className="relative border-b border-border/60"
      style={{ height: TRACK_HEIGHT }}
    >
      {track.clips.map((clip) => (
        <ClipBlock key={clip.id} clip={clip} snapTargets={snapTargets} />
      ))}
    </div>
  );
}
