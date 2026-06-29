"use client";

import * as React from "react";
import { Play, Pause, SkipBack } from "lucide-react";

import type { Clip } from "@/lib/api/timeline";
import { assetContentUrl } from "@/lib/api/assets";
import {
  activeClipAt,
  formatTimecode,
  totalDuration,
} from "@/lib/editor/helpers";
import { useEditorStore } from "@/lib/editor/store";
import { useAsset } from "@/components/editor/assets-context";
import { Button } from "@/components/ui/button";

const REFERENCE_HEIGHT = 720;

function TextOverlay({ clip }: { clip: Clip }) {
  const style = clip.style ?? {};
  const fontSize = (Number(style.fontSize) || 48) / REFERENCE_HEIGHT;
  const y = Number(style.y ?? 50);
  const align = (style.align as string) ?? "center";
  return (
    <div
      className="pointer-events-none absolute inset-x-0 px-[5%]"
      style={{ top: `${y}%`, transform: "translateY(-50%)", textAlign: align as never }}
    >
      <span
        style={{
          color: (style.color as string) ?? "#fff",
          fontSize: `${fontSize * 100}cqh`,
          fontWeight: 700,
          textShadow: "0 2px 8px rgba(0,0,0,0.6)",
          lineHeight: 1.1,
        }}
      >
        {clip.text}
      </span>
    </div>
  );
}

function VisualLayer() {
  const document = useEditorStore((s) => s.document);
  const playhead = useEditorStore((s) => s.playhead);
  const playing = useEditorStore((s) => s.playing);
  const videoRef = React.useRef<HTMLVideoElement>(null);

  const videoTrack = document.tracks.find((t) => t.type === "video");
  const clip = videoTrack ? activeClipAt(videoTrack, playhead) : undefined;
  const asset = useAsset(clip?.asset_id);

  const targetTime =
    clip && asset ? clip.trim_start + (playhead - clip.start) : 0;

  // Seek when scrubbing (paused) or when the active clip changes.
  React.useEffect(() => {
    const v = videoRef.current;
    if (!v || clip?.kind !== "video") return;
    if (!playing && Math.abs(v.currentTime - targetTime) > 0.05) {
      v.currentTime = Math.max(0, targetTime);
    }
  }, [playing, targetTime, clip?.kind]);

  // Play / pause the underlying element with the transport.
  React.useEffect(() => {
    const v = videoRef.current;
    if (!v || clip?.kind !== "video") return;
    if (playing) {
      v.currentTime = Math.max(0, targetTime);
      v.play().catch(() => {});
    } else {
      v.pause();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, clip?.id]);

  if (!clip || !asset) {
    return (
      <div className="flex size-full items-center justify-center text-xs text-muted-foreground">
        No clip at playhead
      </div>
    );
  }

  if (clip.kind === "image") {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={assetContentUrl(asset)}
        alt=""
        className="size-full object-contain"
      />
    );
  }

  return (
    <video
      key={clip.id}
      ref={videoRef}
      src={assetContentUrl(asset)}
      muted
      playsInline
      preload="auto"
      className="size-full object-contain"
    />
  );
}

export function PreviewCanvas() {
  const document = useEditorStore((s) => s.document);
  const playhead = useEditorStore((s) => s.playhead);
  const playing = useEditorStore((s) => s.playing);
  const setPlayhead = useEditorStore((s) => s.setPlayhead);
  const setPlaying = useEditorStore((s) => s.setPlaying);
  const togglePlay = useEditorStore((s) => s.togglePlay);

  const total = totalDuration(document);

  const textClips = document.tracks
    .filter((t) => t.type === "text")
    .flatMap((t) => t.clips)
    .filter((c) => playhead >= c.start && playhead < c.start + c.duration);

  // Playback clock (source of truth for the playhead).
  React.useEffect(() => {
    if (!playing) return;
    let raf = 0;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      const next = useEditorStore.getState().playhead + dt;
      if (next >= total) {
        setPlayhead(total);
        setPlaying(false);
        return;
      }
      setPlayhead(next);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, total, setPlayhead, setPlaying]);

  return (
    <div className="space-y-3">
      <div
        className="relative aspect-video overflow-hidden rounded-xl border border-border bg-black"
        style={{ containerType: "size" }}
      >
        <VisualLayer />
        {textClips.map((c) => (
          <TextOverlay key={c.id} clip={c} />
        ))}
      </div>

      <div className="flex items-center gap-3">
        <Button
          size="icon"
          variant="outline"
          aria-label="Back to start"
          onClick={() => {
            setPlaying(false);
            setPlayhead(0);
          }}
        >
          <SkipBack className="size-4" />
        </Button>
        <Button
          size="icon"
          aria-label={playing ? "Pause" : "Play"}
          onClick={() => {
            if (total === 0) return;
            if (playhead >= total) setPlayhead(0);
            togglePlay();
          }}
        >
          {playing ? <Pause className="size-4" /> : <Play className="size-4" />}
        </Button>
        <span className="font-mono text-xs tabular-nums text-muted-foreground">
          {formatTimecode(playhead)} / {formatTimecode(total)}
        </span>
      </div>
    </div>
  );
}
