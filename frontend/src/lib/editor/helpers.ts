import type { Clip, TimelineDoc, Track } from "@/lib/api/timeline";

export const MIN_CLIP_DURATION = 0.2;

export function uid(prefix = "clip"): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

/** Total timeline length = furthest clip end (seconds). */
export function totalDuration(doc: TimelineDoc): number {
  let max = 0;
  for (const track of doc.tracks) {
    for (const clip of track.clips) {
      max = Math.max(max, clip.start + clip.duration);
    }
  }
  return max;
}

export function findTrackOfClip(
  doc: TimelineDoc,
  clipId: string,
): Track | undefined {
  return doc.tracks.find((t) => t.clips.some((c) => c.id === clipId));
}

export function findClip(doc: TimelineDoc, clipId: string): Clip | undefined {
  for (const track of doc.tracks) {
    const clip = track.clips.find((c) => c.id === clipId);
    if (clip) return clip;
  }
  return undefined;
}

/** The clip active at time `t` on a given track (last one wins on overlap). */
export function activeClipAt(track: Track, t: number): Clip | undefined {
  let found: Clip | undefined;
  for (const clip of track.clips) {
    if (t >= clip.start && t < clip.start + clip.duration) found = clip;
  }
  return found;
}

/** Snap a time to nearby targets within `threshold` seconds. */
export function snapTime(
  time: number,
  targets: number[],
  threshold: number,
): number {
  let best = time;
  let bestDist = threshold;
  for (const target of targets) {
    const dist = Math.abs(time - target);
    if (dist < bestDist) {
      bestDist = dist;
      best = target;
    }
  }
  return best;
}

export function formatTimecode(seconds: number): string {
  const s = Math.max(0, seconds);
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  const cs = Math.floor((s * 100) % 100);
  return `${m}:${sec.toString().padStart(2, "0")}.${cs
    .toString()
    .padStart(2, "0")}`;
}
