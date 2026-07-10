"use client";

import * as React from "react";
import { X, ArrowLeft, ArrowRight, Sparkles } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export const EDITOR_TOUR_SEEN_KEY = "aurora.editorTourSeen";

export interface TourStep {
  /** data-tour id of the element to spotlight; omit for a centered card. */
  target?: string;
  title: string;
  body: string;
}

/** Ordered walkthrough of the editor. Targets map to `data-tour` attributes. */
export const EDITOR_TOUR_STEPS: TourStep[] = [
  {
    title: "Welcome to the editor",
    body: "This quick tour points out the main areas so you can start cutting and enhancing your video. You can skip any time and replay it later from the “Guide” button.",
  },
  {
    target: "mode-switch",
    title: "Two editing modes",
    body: "“Timeline” is for cutting and arranging clips. “AI Edit” lets you change what’s in the footage — remove objects, restyle, relight and more. Switch here anytime.",
  },
  {
    target: "toolbar",
    title: "Editing tools",
    body: "Add text, split a clip at the playhead (S), duplicate, delete, undo/redo (⌘Z), and zoom the timeline. Your work autosaves as you go.",
  },
  {
    target: "media",
    title: "Media & generation",
    body: "Generate video, images and voiceover with AI, and browse your project’s assets. Drag any asset down onto the timeline to add it to your cut.",
  },
  {
    target: "preview",
    title: "Preview",
    body: "Play, pause and scrub your video here (Space to play). What you see is exactly what will export.",
  },
  {
    target: "inspector",
    title: "Clip settings",
    body: "Select a clip to fine-tune it — trim its length, add a transition (crossfade, wipe…), or style text overlays.",
  },
  {
    target: "timeline",
    title: "The timeline",
    body: "Your multi-track canvas: stack video, text and audio. Click a clip to select it, drag to move, and split to cut. This is where your edit comes together.",
  },
  {
    target: "export",
    title: "Export when you’re done",
    body: "Render your finished video to MP4 with a quality preset for social, web or cinema. That’s it — you’re ready to edit!",
  },
];

interface Rect {
  top: number;
  left: number;
  width: number;
  height: number;
}

const PAD = 8; // spotlight padding around the target
const CARD_W = 340;
const GAP = 14;

export function EditorTour({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [index, setIndex] = React.useState(0);
  const [rect, setRect] = React.useState<Rect | null>(null);
  const step = EDITOR_TOUR_STEPS[index];
  const isFirst = index === 0;
  const isLast = index === EDITOR_TOUR_STEPS.length - 1;

  const finish = React.useCallback(() => {
    try {
      window.localStorage.setItem(EDITOR_TOUR_SEEN_KEY, "1");
    } catch {
      /* ignore private-mode storage errors */
    }
    setIndex(0);
    onClose();
  }, [onClose]);

  // Note: `finish()` resets the index to 0 on every close path, so the tour
  // always (re)opens at the first step — no reset effect needed.

  // Measure the current target and keep it in sync with layout changes.
  React.useEffect(() => {
    if (!open) return;
    let raf = 0;
    const measure = () => {
      if (!step.target) {
        setRect(null);
        return;
      }
      const el = document.querySelector<HTMLElement>(
        `[data-tour="${step.target}"]`,
      );
      if (!el) {
        setRect(null);
        return;
      }
      el.scrollIntoView({ block: "nearest", behavior: "smooth" });
      const r = el.getBoundingClientRect();
      setRect({ top: r.top, left: r.left, width: r.width, height: r.height });
    };
    const schedule = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(measure);
    };
    schedule();
    // Re-measure after the smooth scroll settles.
    const t = window.setTimeout(schedule, 320);
    window.addEventListener("resize", schedule);
    window.addEventListener("scroll", schedule, true);
    return () => {
      cancelAnimationFrame(raf);
      window.clearTimeout(t);
      window.removeEventListener("resize", schedule);
      window.removeEventListener("scroll", schedule, true);
    };
  }, [open, index, step.target]);

  // Esc closes.
  React.useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") finish();
      if (e.key === "ArrowRight" && !isLast) setIndex((i) => i + 1);
      if (e.key === "ArrowLeft" && !isFirst) setIndex((i) => i - 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, finish, isFirst, isLast]);

  if (!open) return null;

  // Card placement: below the target if there's room, else above; centered
  // when there's no target (welcome step).
  const vw = typeof window !== "undefined" ? window.innerWidth : 1280;
  const vh = typeof window !== "undefined" ? window.innerHeight : 800;

  let cardStyle: React.CSSProperties;
  if (rect) {
    const below = rect.top + rect.height + GAP;
    const placeBelow = below + 190 < vh;
    const top = placeBelow ? below : Math.max(GAP, rect.top - 190 - GAP);
    const left = Math.min(
      Math.max(GAP, rect.left + rect.width / 2 - CARD_W / 2),
      vw - CARD_W - GAP,
    );
    cardStyle = { top, left, width: CARD_W };
  } else {
    cardStyle = {
      top: vh / 2 - 110,
      left: vw / 2 - CARD_W / 2,
      width: CARD_W,
    };
  }

  return (
    <div className="fixed inset-0 z-[70]" role="dialog" aria-modal="true" aria-label="Editor guide">
      {/* Spotlight: a transparent hole punched with a huge box-shadow. */}
      {rect ? (
        <div
          className="pointer-events-none fixed rounded-lg ring-2 ring-primary transition-all duration-200"
          style={{
            top: rect.top - PAD,
            left: rect.left - PAD,
            width: rect.width + PAD * 2,
            height: rect.height + PAD * 2,
            boxShadow: "0 0 0 9999px rgba(0,0,0,0.6)",
          }}
        />
      ) : (
        <div className="fixed inset-0 bg-black/60" />
      )}

      {/* Coach card */}
      <div
        className="fixed rounded-xl border border-border bg-popover p-4 text-popover-foreground shadow-2xl"
        style={cardStyle}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-1.5 text-sm font-semibold">
            <Sparkles className="size-4 text-primary" />
            {step.title}
          </div>
          <button
            type="button"
            aria-label="Skip tour"
            onClick={finish}
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            <X className="size-4" />
          </button>
        </div>

        <p className="mt-2 text-sm text-muted-foreground">{step.body}</p>

        <div className="mt-4 flex items-center justify-between">
          {/* Step dots */}
          <div className="flex items-center gap-1">
            {EDITOR_TOUR_STEPS.map((_, i) => (
              <span
                key={i}
                className={cn(
                  "size-1.5 rounded-full transition-colors",
                  i === index ? "bg-primary" : "bg-muted-foreground/30",
                )}
              />
            ))}
          </div>

          <div className="flex items-center gap-2">
            {!isFirst ? (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIndex((i) => i - 1)}
              >
                <ArrowLeft className="size-4" />
                Back
              </Button>
            ) : (
              <Button variant="ghost" size="sm" onClick={finish}>
                Skip
              </Button>
            )}
            {isLast ? (
              <Button size="sm" onClick={finish}>
                Done
              </Button>
            ) : (
              <Button size="sm" onClick={() => setIndex((i) => i + 1)}>
                Next
                <ArrowRight className="size-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
