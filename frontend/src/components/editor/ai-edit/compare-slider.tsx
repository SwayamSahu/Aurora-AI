"use client";

import * as React from "react";

/**
 * Before/after split-screen comparison. Drag the divider to reveal the edited
 * result over the original. Both are contained videos looping muted.
 */
export function CompareSlider({
  beforeUrl,
  afterUrl,
}: {
  beforeUrl: string;
  afterUrl: string;
}) {
  const [pos, setPos] = React.useState(50);

  return (
    <div className="relative aspect-video w-full select-none overflow-hidden rounded-xl border bg-black">
      {/* After (full, underneath) */}
      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <video
        src={afterUrl}
        muted
        loop
        autoPlay
        playsInline
        className="absolute inset-0 size-full object-contain"
      />
      {/* Before (clipped to the left of the divider) */}
      <div
        className="absolute inset-0 overflow-hidden"
        style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}
      >
        <video
          src={beforeUrl}
          muted
          loop
          autoPlay
          playsInline
          className="absolute inset-0 size-full object-contain"
        />
      </div>

      {/* Labels */}
      <span className="absolute left-2 top-2 rounded bg-black/60 px-1.5 py-0.5 text-[10px] font-medium text-white backdrop-blur">
        Before
      </span>
      <span className="absolute right-2 top-2 rounded bg-primary/80 px-1.5 py-0.5 text-[10px] font-medium text-primary-foreground backdrop-blur">
        After
      </span>

      {/* Divider handle */}
      <div
        className="pointer-events-none absolute inset-y-0 w-0.5 bg-white/90"
        style={{ left: `${pos}%` }}
      >
        <div className="absolute left-1/2 top-1/2 size-6 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-black/40" />
      </div>

      <input
        type="range"
        min={0}
        max={100}
        value={pos}
        onChange={(e) => setPos(Number(e.target.value))}
        aria-label="Compare before and after"
        className="absolute inset-0 size-full cursor-ew-resize opacity-0"
      />
    </div>
  );
}
