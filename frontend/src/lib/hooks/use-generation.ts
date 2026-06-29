"use client";

import * as React from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import type { Job, JobType } from "@/lib/api/jobs";
import { useCreateJob, jobKeys } from "@/lib/query/jobs";
import { useJobProgress } from "@/lib/ws/use-job-progress";

const TERMINAL = ["succeeded", "failed", "cancelled"];

/**
 * Encapsulates: start a generation job, stream live progress over WebSocket,
 * and invalidate caches when it finishes. Works in both eager (job already
 * terminal on create) and async-worker modes.
 */
export function useGeneration(projectId: string) {
  const qc = useQueryClient();
  const create = useCreateJob(projectId);
  const [activeJobId, setActiveJobId] = React.useState<string | null>(null);

  const progress = useJobProgress(activeJobId, (event) => {
    setActiveJobId(null);
    qc.invalidateQueries({ queryKey: jobKeys.all });
    qc.invalidateQueries({ queryKey: ["assets", projectId] });
    if (event.status === "succeeded") toast.success("Generation complete!");
    else if (event.status === "failed") toast.error("Generation failed.");
  });

  const generate = React.useCallback(
    async (
      type: JobType,
      params: Record<string, unknown>,
    ): Promise<Job | null> => {
      try {
        const job = await create.mutateAsync({ type, params });
        if (TERMINAL.includes(job.status)) {
          if (job.status === "succeeded") toast.success("Generation complete!");
          else if (job.status === "failed")
            toast.error(job.error ?? "Generation failed.");
          return job;
        }
        setActiveJobId(job.id);
        return job;
      } catch (err) {
        toast.error(
          err instanceof Error ? err.message : "Could not start generation.",
        );
        return null;
      }
    },
    [create],
  );

  return {
    generate,
    isStarting: create.isPending,
    activeJobId,
    progress,
    busy: create.isPending || activeJobId !== null,
  };
}
