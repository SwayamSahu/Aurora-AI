import { beforeEach, describe, expect, it } from "vitest";

import type { TimelineDoc } from "@/lib/api/timeline";
import { useEditorStore } from "@/lib/editor/store";
import { findClip, totalDuration } from "@/lib/editor/helpers";

function baseDoc(): TimelineDoc {
  return {
    version: 1,
    tracks: [
      {
        id: "v",
        type: "video",
        name: "Video",
        clips: [
          {
            id: "c1",
            kind: "video",
            asset_id: "a1",
            start: 0,
            duration: 6,
            trim_start: 0,
          },
        ],
      },
      { id: "t", type: "text", name: "Text", clips: [] },
      { id: "a", type: "audio", name: "Audio", clips: [] },
    ],
  };
}

const store = () => useEditorStore.getState();

beforeEach(() => {
  useEditorStore.getState().load("p1", baseDoc());
});

describe("editor store", () => {
  it("loads a document", () => {
    expect(store().document.tracks).toHaveLength(3);
    expect(totalDuration(store().document)).toBe(6);
  });

  it("updates a clip and marks dirty", () => {
    store().updateClip("c1", { start: 2 });
    expect(findClip(store().document, "c1")!.start).toBe(2);
    expect(store().saveStatus).toBe("dirty");
  });

  it("clamps duration to the minimum", () => {
    store().updateClip("c1", { duration: 0 });
    expect(findClip(store().document, "c1")!.duration).toBeGreaterThan(0);
  });

  it("splits the selected clip at the playhead", () => {
    store().selectClip("c1");
    store().setPlayhead(2);
    store().splitAtPlayhead();
    const clips = store().document.tracks[0].clips;
    expect(clips).toHaveLength(2);
    expect(clips[0].duration).toBeCloseTo(2);
    expect(clips[1].duration).toBeCloseTo(4);
    // Right half's source in-point advances by the split offset.
    expect(clips[1].trim_start).toBeCloseTo(2);
  });

  it("does not split outside the clip bounds", () => {
    store().selectClip("c1");
    store().setPlayhead(0); // at the very start
    store().splitAtPlayhead();
    expect(store().document.tracks[0].clips).toHaveLength(1);
  });

  it("undo and redo restore document state", () => {
    store().updateClip("c1", { start: 3 });
    expect(findClip(store().document, "c1")!.start).toBe(3);
    store().undo();
    expect(findClip(store().document, "c1")!.start).toBe(0);
    store().redo();
    expect(findClip(store().document, "c1")!.start).toBe(3);
  });

  it("adds a text clip at the playhead", () => {
    store().setPlayhead(1.5);
    store().addTextClip();
    const textClips = store().document.tracks[1].clips;
    expect(textClips).toHaveLength(1);
    expect(textClips[0].kind).toBe("text");
    expect(textClips[0].start).toBe(1.5);
  });

  it("adds a clip from an asset to the video track", () => {
    store().addClipFromAsset({ assetId: "a2", kind: "image", duration: 3 });
    const videoClips = store().document.tracks[0].clips;
    expect(videoClips).toHaveLength(2);
    expect(videoClips[1].asset_id).toBe("a2");
  });

  it("removes a clip", () => {
    store().removeClip("c1");
    expect(store().document.tracks[0].clips).toHaveLength(0);
  });

  it("duplicates the selected clip after itself", () => {
    store().selectClip("c1");
    store().duplicateSelected();
    const clips = store().document.tracks[0].clips;
    expect(clips).toHaveLength(2);
    expect(clips[1].start).toBeCloseTo(6); // placed after the original
  });
});
