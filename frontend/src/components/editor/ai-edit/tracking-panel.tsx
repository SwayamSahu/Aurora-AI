"use client";

import { X } from "lucide-react";

import { formatTimecode } from "@/lib/editor/helpers";
import type { TrackedObject } from "@/lib/editor/ai-edit/mask";
import { Button } from "@/components/ui/button";

/**
 * Tracked-object list: one row per detected chip, each with a presence
 * range within the clip. Mock detection has no real per-frame tracking, so
 * the range defaults to the full clip and is manually adjustable — this is
 * the seam real tracking (Phase 9, SAM 2) will feed automatically.
 */
export function TrackingPanel({
  objects,
  clipDuration,
  onChangeRange,
  onRemove,
}: {
  objects: TrackedObject[];
  clipDuration: number;
  onChangeRange: (id: string, startTime: number, endTime: number) => void;
  onRemove: (id: string) => void;
}) {
  if (objects.length === 0) return null;

  return (
    <div className="rounded-lg border bg-card p-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Tracked objects · {objects.length}
      </p>
      <ul className="space-y-3">
        {objects.map((obj) => (
          <li key={obj.id} className="space-y-1.5">
            <div className="flex items-center justify-between gap-2 text-xs">
              <span className="font-medium">{obj.label}</span>
              <div className="flex items-center gap-2">
                <span className="font-mono text-[11px] text-muted-foreground">
                  {formatTimecode(obj.startTime)}–{formatTimecode(obj.endTime)}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-5"
                  aria-label={`Remove ${obj.label}`}
                  onClick={() => onRemove(obj.id)}
                >
                  <X className="size-3.5" />
                </Button>
              </div>
            </div>
            {/* Dual-handle presence range (start/end within the clip) */}
            <div className="relative h-4">
              <input
                type="range"
                min={0}
                max={clipDuration}
                step={0.1}
                value={obj.startTime}
                aria-label={`${obj.label} start time`}
                onChange={(e) =>
                  onChangeRange(
                    obj.id,
                    Math.min(Number(e.target.value), obj.endTime - 0.1),
                    obj.endTime,
                  )
                }
                className="absolute inset-x-0 top-0 h-1.5 w-full cursor-pointer appearance-none rounded-full bg-transparent accent-primary"
              />
              <input
                type="range"
                min={0}
                max={clipDuration}
                step={0.1}
                value={obj.endTime}
                aria-label={`${obj.label} end time`}
                onChange={(e) =>
                  onChangeRange(
                    obj.id,
                    obj.startTime,
                    Math.max(Number(e.target.value), obj.startTime + 0.1),
                  )
                }
                className="absolute inset-x-0 top-0 h-1.5 w-full cursor-pointer appearance-none rounded-full bg-muted accent-primary/60"
              />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
