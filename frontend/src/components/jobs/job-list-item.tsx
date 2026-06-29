"use client";

import * as React from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  Wand2,
  Image as ImageIcon,
  RotateCcw,
  Ban,
  FolderOpen,
  Film,
} from "lucide-react";

import { type Job, type JobType } from "@/lib/api/jobs";
import { assetContentUrl } from "@/lib/api/assets";
import { useCancelJob, useRetryJob } from "@/lib/query/jobs";
import { timeAgo } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { JobStatusBadge } from "@/components/jobs/job-status-badge";

const TYPE_META: Partial<Record<JobType, { label: string; icon: typeof Wand2 }>> = {
  generate_video: { label: "Text → Video", icon: Wand2 },
  generate_image: { label: "Text → Image", icon: ImageIcon },
};

export function JobListItem({ job }: { job: Job }) {
  const retry = useRetryJob(job.project_id);
  const cancel = useCancelJob(job.project_id);
  const meta = TYPE_META[job.type] ?? { label: job.type, icon: Film };
  const prompt = (job.params?.prompt as string) ?? "—";
  const active = job.status === "queued" || job.status === "running";

  async function handleRetry() {
    try {
      await retry.mutateAsync(job.id);
      toast.success("Re-queued generation.");
    } catch {
      toast.error("Could not retry.");
    }
  }

  async function handleCancel() {
    try {
      await cancel.mutateAsync(job.id);
    } catch {
      toast.error("Could not cancel.");
    }
  }

  return (
    <Card className="flex items-center gap-4 p-4">
      {/* Thumbnail */}
      <div className="flex size-16 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-muted">
        {job.result_asset?.kind === "image" ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={assetContentUrl(job.result_asset)}
            alt=""
            className="size-full object-cover"
          />
        ) : job.result_asset?.kind === "video" ? (
          <video
            src={assetContentUrl(job.result_asset)}
            muted
            playsInline
            preload="metadata"
            className="size-full object-cover"
          />
        ) : (
          <meta.icon className="size-6 text-muted-foreground/60" />
        )}
      </div>

      {/* Main */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">
            {meta.label}
          </span>
          <JobStatusBadge status={job.status} />
        </div>
        <p className="mt-0.5 truncate text-sm font-medium" title={prompt}>
          {prompt}
        </p>
        {active ? (
          <Progress value={Math.round(job.progress * 100)} className="mt-2 h-1.5" />
        ) : job.status === "failed" && job.error ? (
          <p className="mt-1 truncate text-xs text-destructive" title={job.error}>
            {job.error}
          </p>
        ) : (
          <p className="mt-0.5 text-xs text-muted-foreground">
            {timeAgo(job.created_at)}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex shrink-0 items-center gap-1.5">
        {job.status === "failed" || job.status === "cancelled" ? (
          <Button
            size="sm"
            variant="outline"
            onClick={handleRetry}
            loading={retry.isPending}
          >
            <RotateCcw className="size-4" /> Retry
          </Button>
        ) : null}
        {active ? (
          <Button
            size="sm"
            variant="outline"
            onClick={handleCancel}
            loading={cancel.isPending}
          >
            <Ban className="size-4" /> Cancel
          </Button>
        ) : null}
        <Button asChild size="icon" variant="ghost" aria-label="Open project">
          <Link href={`/projects/${job.project_id}`}>
            <FolderOpen className="size-4" />
          </Link>
        </Button>
      </div>
    </Card>
  );
}
