import { apiFetch } from "@/lib/api/client";

export type ClipKind = "video" | "image" | "audio" | "text";
export type TrackType = "video" | "text" | "audio";

export interface Clip {
  id: string;
  kind: ClipKind;
  asset_id?: string | null;
  /** Position on the timeline (seconds). */
  start: number;
  /** Length on the timeline (seconds). */
  duration: number;
  /** In-point within the source media (seconds). */
  trim_start: number;
  text?: string | null;
  style?: Record<string, unknown>;
  /** FFmpeg xfade transition name applied at this clip's start, or null for a hard cut. */
  transition_in?: string | null;
}

export interface Track {
  id: string;
  type: TrackType;
  name: string;
  clips: Clip[];
  muted?: boolean;
}

export interface TimelineDoc {
  version: number;
  tracks: Track[];
}

export interface TimelineRead {
  id: string;
  project_id: string;
  version: number;
  document: TimelineDoc;
  updated_at: string;
}

export function getTimeline(projectId: string) {
  return apiFetch<TimelineRead>(`/projects/${projectId}/timeline`);
}

export function saveTimeline(projectId: string, document: TimelineDoc) {
  return apiFetch<TimelineRead>(`/projects/${projectId}/timeline`, {
    method: "PUT",
    json: document,
  });
}
