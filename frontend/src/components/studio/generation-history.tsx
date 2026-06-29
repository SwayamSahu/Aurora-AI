"use client";

import { Loader2, AlertTriangle, Film } from "lucide-react";

import { cn } from "@/lib/utils";
import type { Job } from "@/lib/api/jobs";
import { assetContentUrl } from "@/lib/api/assets";

export function GenerationHistory({
  jobs,
  selectedId,
  onSelect,
}: {
  jobs: Job[];
  selectedId: string | null;
  onSelect: (job: Job) => void;
}) {
  if (jobs.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-border px-4 py-6 text-center text-xs text-muted-foreground">
        No generations yet. Your history appears here.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
      {jobs.map((job) => {
        const asset = job.result_asset;
        const active = job.status === "queued" || job.status === "running";
        return (
          <button
            key={job.id}
            onClick={() => onSelect(job)}
            title={(job.params?.prompt as string) ?? ""}
            className={cn(
              "group relative aspect-square overflow-hidden rounded-lg border bg-muted transition-colors",
              selectedId === job.id
                ? "border-primary ring-2 ring-primary/30"
                : "border-border hover:border-primary/50",
            )}
          >
            {asset?.kind === "image" ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={assetContentUrl(asset)}
                alt=""
                className="size-full object-cover"
              />
            ) : asset?.kind === "video" ? (
              <video
                src={assetContentUrl(asset)}
                muted
                playsInline
                preload="metadata"
                className="size-full object-cover"
              />
            ) : (
              <div className="flex size-full items-center justify-center">
                {active ? (
                  <Loader2 className="size-5 animate-spin text-muted-foreground" />
                ) : job.status === "failed" ? (
                  <AlertTriangle className="size-5 text-destructive" />
                ) : (
                  <Film className="size-5 text-muted-foreground/60" />
                )}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
