"use client";

import * as React from "react";
import { useReducedMotion } from "motion/react";

import { cn } from "@/lib/utils";
import { media } from "@/lib/landing/content";

/** Max seconds to show a single clip before advancing (clips may be shorter). */
const MAX_CLIP_SECONDS = 8;

/**
 * Cinematic hero slideshow: stacks the showreel clips and crossfades between
 * them, advancing when a clip ends or after MAX_CLIP_SECONDS — whichever comes
 * first. Under prefers-reduced-motion it shows the first poster, statically.
 */
export function HeroShowreel() {
  const reduce = useReducedMotion();
  const clips = media.showreel;
  const [active, setActive] = React.useState(0);
  const videoRefs = React.useRef<(HTMLVideoElement | null)[]>([]);

  const advance = React.useCallback(() => {
    setActive((i) => (i + 1) % clips.length);
  }, [clips.length]);

  // Drive the active clip: rewind, play, and guarantee advancement via a timer.
  React.useEffect(() => {
    if (reduce || clips.length < 2) return;
    const el = videoRefs.current[active];
    if (el) {
      el.currentTime = 0;
      void el.play().catch(() => {});
    }
    const timer = window.setTimeout(advance, MAX_CLIP_SECONDS * 1000);
    return () => window.clearTimeout(timer);
  }, [active, advance, reduce, clips.length]);

  return (
    <div className="relative aspect-video overflow-hidden rounded-xl bg-background">
      {/* Stacked, crossfading clips */}
      {clips.map((clip, i) => (
        <video
          key={clip.src}
          ref={(node) => {
            videoRefs.current[i] = node;
          }}
          className={cn(
            "absolute inset-0 size-full object-cover transition-opacity duration-1000 ease-out",
            i === active ? "opacity-100" : "opacity-0",
          )}
          src={clip.src}
          poster={clip.poster}
          // Only the first clip autoplays on mount; the rest are driven on activation.
          autoPlay={!reduce && i === 0}
          muted
          playsInline
          loop={reduce || clips.length < 2}
          preload={i === 0 ? "metadata" : "none"}
          onEnded={i === active && !reduce ? advance : undefined}
          aria-label={clip.alt}
          aria-hidden={i === active ? undefined : true}
        />
      ))}

      {/* Brand wash + legibility gradient over the footage */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(60%_60%_at_30%_20%,oklch(0.7_0.19_285/0.22),transparent),radial-gradient(50%_50%_at_80%_80%,oklch(0.62_0.2_320/0.2),transparent)]" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-background/70 via-transparent to-background/5" />

      {/* Live badge */}
      <div className="absolute left-4 top-4 inline-flex items-center gap-2 rounded-full border border-border bg-background/70 px-3 py-1 text-xs font-medium backdrop-blur">
        <span className="relative flex size-2">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary/70" />
          <span className="relative inline-flex size-2 rounded-full bg-primary" />
        </span>
        Live showreel
      </div>

      {/* Slideshow progress indicator (doubles as faux editor scrubber) */}
      <div className="absolute inset-x-0 bottom-0 flex h-14 items-center gap-2 border-t border-border bg-background/60 px-4 backdrop-blur">
        {clips.map((clip, i) => (
          <button
            key={clip.src}
            type="button"
            aria-label={`Show clip ${i + 1}: ${clip.alt}`}
            aria-current={i === active}
            onClick={() => setActive(i)}
            className="group relative h-2 flex-1 overflow-hidden rounded-full bg-muted-foreground/20"
          >
            <span
              className={cn(
                "absolute inset-y-0 left-0 rounded-full bg-primary transition-all",
                i < active && "w-full opacity-60",
                i === active && "w-full",
                i > active && "w-0",
              )}
              style={
                i === active && !reduce
                  ? { animation: `showreel-fill ${MAX_CLIP_SECONDS}s linear forwards` }
                  : undefined
              }
            />
          </button>
        ))}
      </div>
    </div>
  );
}
