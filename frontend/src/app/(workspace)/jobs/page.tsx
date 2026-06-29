"use client";

import * as React from "react";
import { ListChecks, Sparkles } from "lucide-react";

import { useJobs } from "@/lib/query/jobs";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { JobListItem } from "@/components/jobs/job-list-item";
import { GenerationDialog } from "@/components/generation/generation-dialog";

export default function JobsPage() {
  const { data: jobs, isLoading, isError, refetch } = useJobs();
  const [generating, setGenerating] = React.useState(false);

  return (
    <>
      <PageHeader
        title="Jobs"
        description="Generation, transcription and export jobs and their progress."
        actions={
          <Button onClick={() => setGenerating(true)}>
            <Sparkles className="size-4" />
            New generation
          </Button>
        }
      />

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-xl" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState description="Couldn't load jobs." onRetry={() => refetch()} />
      ) : jobs && jobs.length > 0 ? (
        <div className="space-y-3">
          {jobs.map((job) => (
            <JobListItem key={job.id} job={job} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={ListChecks}
          title="No jobs yet"
          description="Start a generation and it will appear here with live progress."
          action={
            <Button onClick={() => setGenerating(true)}>
              <Sparkles className="size-4" />
              New generation
            </Button>
          }
        />
      )}

      <GenerationDialog open={generating} onOpenChange={setGenerating} />
    </>
  );
}
