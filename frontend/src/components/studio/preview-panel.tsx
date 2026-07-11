"use client";

import * as React from "react";
import Link from "next/link";
import { Sparkles, Download, Clapperboard, Loader2, RectangleHorizontal } from "lucide-react";

import type { Job } from "@/lib/api/jobs";
import { assetContentUrl } from "@/lib/api/assets";
import { ASPECT_RATIOS } from "@/lib/generation-options";
import type { JobProgressEvent } from "@/lib/ws/use-job-progress";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

interface Props {
  job: Job | null;
  progressEvent: JobProgressEvent | null;
  busy: boolean;
  projectId: string;
  /** Selected aspect ratio id — shapes the preview frame and shows a badge,
   * mirroring the chosen output shape (falls back to 16:9 when "auto"). */
  aspect?: string;
}

export function PreviewPanel({
  job,
  progressEvent,
  busy,
  projectId,
  aspect = "16:9",
}: Props) {
  const asset = job?.result_asset ?? null;
  const ratioDef = ASPECT_RATIOS.find((a) => a.id === aspect);
  const cssRatio = ratioDef?.ratio ?? 16 / 9;
  const badgeLabel = ratioDef && ratioDef.id !== "auto" ? ratioDef.label : "16:9";

  const AspectBadge = (
    <span className="inline-flex items-center gap-1.5 rounded-md bg-background/80 px-2 py-1 text-xs font-medium text-muted-foreground backdrop-blur">
      <RectangleHorizontal className="size-3.5" />
      {badgeLabel}
    </span>
  );

  if (busy) {
    const pct = Math.round(
      (progressEvent?.progress ?? job?.progress ?? 0.05) * 100,
    );
    return (
      <div
        className="relative flex flex-col items-center justify-center gap-4 rounded-xl border border-border bg-card"
        style={{ aspectRatio: cssRatio }}
      >
        <div className="absolute left-3 top-3">{AspectBadge}</div>
        <Loader2 className="size-7 animate-spin text-primary" />
        <div className="w-2/3 space-y-2 text-center">
          <p className="text-sm font-medium">Generating…</p>
          <Progress value={pct} />
          <p className="text-xs text-muted-foreground">{pct}%</p>
        </div>
      </div>
    );
  }

  if (!asset) {
    return (
      <div
        className="relative flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border bg-card/40 text-center"
        style={{ aspectRatio: cssRatio }}
      >
        <div className="absolute left-3 top-3">{AspectBadge}</div>
        <div className="flex size-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
          <Sparkles className="size-6" />
        </div>
        <div>
          <p className="text-sm font-medium">Your generation appears here</p>
          <p className="text-xs text-muted-foreground">
            Write a prompt and hit Generate.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="relative overflow-hidden rounded-xl border border-border bg-black">
        <div className="absolute left-3 top-3 z-10">{AspectBadge}</div>
        {asset.kind === "image" ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={assetContentUrl(asset)}
            alt={asset.name}
            className="aspect-video w-full object-contain"
          />
        ) : (
          <video
            key={asset.id}
            src={assetContentUrl(asset)}
            controls
            autoPlay
            loop
            muted
            playsInline
            className="aspect-video w-full object-contain"
          />
        )}
      </div>
      <div className="flex items-center justify-end gap-2">
        <Button asChild variant="outline">
          <a href={assetContentUrl(asset)} target="_blank" rel="noreferrer">
            <Download className="size-4" /> Download
          </a>
        </Button>
        <Button asChild>
          <Link href={`/projects/${projectId}/editor`}>
            <Clapperboard className="size-4" /> Send to editor
          </Link>
        </Button>
      </div>
    </div>
  );
}
