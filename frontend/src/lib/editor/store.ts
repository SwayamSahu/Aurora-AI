import { create } from "zustand";

import type { Clip, ClipKind, TimelineDoc, TrackType } from "@/lib/api/timeline";
import { MIN_CLIP_DURATION, findClip, uid } from "@/lib/editor/helpers";

export type SaveStatus = "idle" | "dirty" | "saving" | "saved";

const HISTORY_LIMIT = 50;

function clone(doc: TimelineDoc): TimelineDoc {
  return structuredClone(doc);
}

function trackTypeForKind(kind: ClipKind): TrackType {
  if (kind === "text") return "text";
  if (kind === "audio") return "audio";
  return "video"; // video + image
}

interface EditorState {
  projectId: string | null;
  document: TimelineDoc;
  selectedClipId: string | null;
  playhead: number;
  playing: boolean;
  pxPerSec: number;
  past: TimelineDoc[];
  future: TimelineDoc[];
  saveStatus: SaveStatus;
  loaded: boolean;

  load: (projectId: string, doc: TimelineDoc) => void;
  snapshot: () => void;
  undo: () => void;
  redo: () => void;

  addClipFromAsset: (input: {
    assetId: string;
    kind: ClipKind;
    duration: number;
  }) => void;
  addTextClip: () => void;
  addCaptionClips: (
    captions: { start: number; duration: number; text: string }[],
  ) => void;
  updateClip: (clipId: string, patch: Partial<Clip>, history?: boolean) => void;
  removeClip: (clipId: string) => void;
  splitAtPlayhead: () => void;
  duplicateSelected: () => void;

  selectClip: (id: string | null) => void;
  setPlayhead: (t: number) => void;
  togglePlay: () => void;
  setPlaying: (b: boolean) => void;
  setPxPerSec: (n: number) => void;
  setSaveStatus: (s: SaveStatus) => void;
}

const EMPTY_DOC: TimelineDoc = { version: 1, tracks: [] };

export const useEditorStore = create<EditorState>((set, get) => ({
  projectId: null,
  document: EMPTY_DOC,
  selectedClipId: null,
  playhead: 0,
  playing: false,
  pxPerSec: 60,
  past: [],
  future: [],
  saveStatus: "idle",
  loaded: false,

  load: (projectId, doc) =>
    set({
      projectId,
      document: doc,
      past: [],
      future: [],
      selectedClipId: null,
      playhead: 0,
      playing: false,
      saveStatus: "idle",
      loaded: true,
    }),

  snapshot: () => {
    const { document, past } = get();
    const next = [...past, clone(document)].slice(-HISTORY_LIMIT);
    set({ past: next, future: [] });
  },

  undo: () => {
    const { past, future, document } = get();
    if (past.length === 0) return;
    const previous = past[past.length - 1];
    set({
      document: previous,
      past: past.slice(0, -1),
      future: [clone(document), ...future],
      saveStatus: "dirty",
      selectedClipId: null,
    });
  },

  redo: () => {
    const { past, future, document } = get();
    if (future.length === 0) return;
    const next = future[0];
    set({
      document: next,
      future: future.slice(1),
      past: [...past, clone(document)],
      saveStatus: "dirty",
    });
  },

  addClipFromAsset: ({ assetId, kind, duration }) => {
    get().snapshot();
    const { document, playhead } = get();
    const type = trackTypeForKind(kind);
    const clip: Clip = {
      id: uid(),
      kind,
      asset_id: assetId,
      start: Math.max(0, playhead),
      duration: Math.max(MIN_CLIP_DURATION, duration || 4),
      trim_start: 0,
    };
    const tracks = document.tracks.map((t) =>
      t.type === type ? { ...t, clips: [...t.clips, clip] } : t,
    );
    set({
      document: { ...document, tracks },
      selectedClipId: clip.id,
      saveStatus: "dirty",
    });
  },

  addTextClip: () => {
    get().snapshot();
    const { document, playhead } = get();
    const clip: Clip = {
      id: uid("text"),
      kind: "text",
      start: Math.max(0, playhead),
      duration: 3,
      trim_start: 0,
      text: "New text",
      style: { fontSize: 48, color: "#ffffff", align: "center", y: 50 },
    };
    const tracks = document.tracks.map((t) =>
      t.type === "text" ? { ...t, clips: [...t.clips, clip] } : t,
    );
    set({
      document: { ...document, tracks },
      selectedClipId: clip.id,
      saveStatus: "dirty",
    });
  },

  addCaptionClips: (captions) => {
    if (captions.length === 0) return;
    get().snapshot();
    const { document } = get();
    const newClips: Clip[] = captions.map((c) => ({
      id: uid("cap"),
      kind: "text",
      start: Math.max(0, c.start),
      duration: Math.max(MIN_CLIP_DURATION, c.duration),
      trim_start: 0,
      text: c.text,
      style: { fontSize: 42, color: "#ffffff", align: "center", y: 85 },
    }));
    const tracks = document.tracks.map((t) =>
      t.type === "text" ? { ...t, clips: [...t.clips, ...newClips] } : t,
    );
    set({ document: { ...document, tracks }, saveStatus: "dirty" });
  },

  updateClip: (clipId, patch, history = true) => {
    if (history) get().snapshot();
    const { document } = get();
    const tracks = document.tracks.map((t) => ({
      ...t,
      clips: t.clips.map((c) => {
        if (c.id !== clipId) return c;
        const next = { ...c, ...patch };
        if (next.start < 0) next.start = 0;
        if (next.duration < MIN_CLIP_DURATION) next.duration = MIN_CLIP_DURATION;
        if (next.trim_start < 0) next.trim_start = 0;
        return next;
      }),
    }));
    set({ document: { ...document, tracks }, saveStatus: "dirty" });
  },

  removeClip: (clipId) => {
    get().snapshot();
    const { document, selectedClipId } = get();
    const tracks = document.tracks.map((t) => ({
      ...t,
      clips: t.clips.filter((c) => c.id !== clipId),
    }));
    set({
      document: { ...document, tracks },
      selectedClipId: selectedClipId === clipId ? null : selectedClipId,
      saveStatus: "dirty",
    });
  },

  splitAtPlayhead: () => {
    const { document, playhead, selectedClipId } = get();
    const clip = selectedClipId ? findClip(document, selectedClipId) : undefined;
    if (!clip) return;
    if (playhead <= clip.start + MIN_CLIP_DURATION) return;
    if (playhead >= clip.start + clip.duration - MIN_CLIP_DURATION) return;

    get().snapshot();
    const offset = playhead - clip.start;
    const left: Clip = { ...clip, duration: offset };
    const right: Clip = {
      ...clip,
      id: uid(clip.kind),
      start: playhead,
      duration: clip.duration - offset,
      trim_start: clip.trim_start + offset,
    };
    const tracks = get().document.tracks.map((t) => ({
      ...t,
      clips: t.clips.flatMap((c) => (c.id === clip.id ? [left, right] : [c])),
    }));
    set({
      document: { ...get().document, tracks },
      selectedClipId: right.id,
      saveStatus: "dirty",
    });
  },

  duplicateSelected: () => {
    const { document, selectedClipId } = get();
    const clip = selectedClipId ? findClip(document, selectedClipId) : undefined;
    if (!clip) return;
    get().snapshot();
    const copy: Clip = {
      ...clip,
      id: uid(clip.kind),
      start: clip.start + clip.duration,
    };
    const tracks = get().document.tracks.map((t) =>
      t.clips.some((c) => c.id === clip.id)
        ? { ...t, clips: [...t.clips, copy] }
        : t,
    );
    set({
      document: { ...get().document, tracks },
      selectedClipId: copy.id,
      saveStatus: "dirty",
    });
  },

  selectClip: (id) => set({ selectedClipId: id }),
  setPlayhead: (t) => set({ playhead: Math.max(0, t) }),
  togglePlay: () => set((s) => ({ playing: !s.playing })),
  setPlaying: (b) => set({ playing: b }),
  setPxPerSec: (n) => set({ pxPerSec: Math.max(20, Math.min(240, n)) }),
  setSaveStatus: (s) => set({ saveStatus: s }),
}));
