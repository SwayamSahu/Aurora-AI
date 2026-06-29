"use client";

import * as React from "react";
import { useSearchParams } from "next/navigation";
import { FolderPlus, Plus } from "lucide-react";

import type { Job } from "@/lib/api/jobs";
import { STYLE_PRESETS } from "@/lib/generation-options";
import { useProjects } from "@/lib/query/projects";
import { useJobs } from "@/lib/query/jobs";
import { useGeneration } from "@/lib/hooks/use-generation";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EmptyState } from "@/components/shared/empty-state";
import { ProjectFormDialog } from "@/components/projects/project-form-dialog";
import {
  PromptComposer,
  type ComposerState,
  type GenerationType,
  initialComposerState,
} from "@/components/studio/prompt-composer";
import { PreviewPanel } from "@/components/studio/preview-panel";
import { GenerationHistory } from "@/components/studio/generation-history";

function buildParams(state: ComposerState): Record<string, unknown> {
  const presets = STYLE_PRESETS.filter((p) => state.presets.has(p.id));
  const prompt = [state.prompt.trim(), ...presets.map((p) => p.promptSuffix)]
    .filter(Boolean)
    .join(", ");
  const negative = [
    state.negativePrompt.trim(),
    ...presets.map((p) => p.negativePrompt).filter(Boolean),
  ]
    .filter(Boolean)
    .join(", ");
  const seed = state.seed ? Number(state.seed) : undefined;

  if (state.type === "generate_video") {
    const [w, h] = state.resolution.split("x").map(Number);
    return {
      prompt,
      negative_prompt: negative || undefined,
      model: state.model,
      width: w,
      height: h,
      duration_seconds: Number(state.duration),
      seed,
    };
  }
  return { prompt, negative_prompt: negative || undefined, seed };
}

function StudioInner() {
  const searchParams = useSearchParams();
  const mode = searchParams.get("mode");
  const initialType: GenerationType =
    mode === "image" ? "generate_image" : "generate_video";

  const projectsQuery = useProjects("", "recent");
  const [projectId, setProjectId] = React.useState<string>("");
  const [creatingProject, setCreatingProject] = React.useState(false);

  // Default to the first project once loaded.
  React.useEffect(() => {
    if (!projectId && projectsQuery.data && projectsQuery.data.length > 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setProjectId(projectsQuery.data[0].id);
    }
  }, [projectId, projectsQuery.data]);

  const [state, setState] = React.useState<ComposerState>(() =>
    initialComposerState(initialType),
  );
  const update = (patch: Partial<ComposerState>) =>
    setState((prev) => ({ ...prev, ...patch }));

  const history = useJobs(projectId || undefined);
  const generation = useGeneration(projectId || "_");

  const [previewJobId, setPreviewJobId] = React.useState<string | null>(null);
  const [recentJob, setRecentJob] = React.useState<Job | null>(null);

  // Preview follows the most recent job until the user picks another.
  React.useEffect(() => {
    if (!previewJobId && history.data && history.data.length > 0) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPreviewJobId(history.data[0].id);
    }
  }, [previewJobId, history.data]);

  const previewJob =
    recentJob && recentJob.id === previewJobId
      ? recentJob
      : (history.data?.find((j) => j.id === previewJobId) ?? null);

  async function handleGenerate() {
    if (!projectId) return;
    const job = await generation.generate(state.type, buildParams(state));
    if (job) {
      setRecentJob(job);
      setPreviewJobId(job.id);
    }
  }

  if (projectsQuery.isLoading) {
    return (
      <>
        <PageHeader title="Generation studio" />
        <Skeleton className="h-96 w-full rounded-xl" />
      </>
    );
  }

  if (!projectsQuery.data || projectsQuery.data.length === 0) {
    return (
      <>
        <PageHeader
          title="Generation studio"
          description="Describe what you want and let Aurora generate it."
        />
        <EmptyState
          icon={FolderPlus}
          title="Create a project first"
          description="Generations live inside a project. Create one to get started."
          action={
            <Button onClick={() => setCreatingProject(true)}>
              <Plus className="size-4" /> New project
            </Button>
          }
        />
        <ProjectFormDialog
          open={creatingProject}
          onOpenChange={setCreatingProject}
          onCreated={(p) => setProjectId(p.id)}
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Generation studio"
        description="Describe what you want and let Aurora generate it."
        actions={
          <div className="flex items-center gap-2">
            <Select value={projectId} onValueChange={setProjectId}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select project" />
              </SelectTrigger>
              <SelectContent>
                {projectsQuery.data.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="icon"
              aria-label="New project"
              onClick={() => setCreatingProject(true)}
            >
              <Plus className="size-4" />
            </Button>
          </div>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
        <Card>
          <CardContent className="p-5">
            <PromptComposer
              state={state}
              onChange={update}
              onGenerate={handleGenerate}
              busy={generation.busy}
            />
          </CardContent>
        </Card>

        <div className="space-y-6">
          <PreviewPanel
            job={previewJob}
            progressEvent={generation.progress}
            busy={generation.busy}
            projectId={projectId}
          />
          <div className="space-y-3">
            <h2 className="text-sm font-semibold">History</h2>
            <GenerationHistory
              jobs={history.data ?? []}
              selectedId={previewJobId}
              onSelect={(job) => {
                setRecentJob(job);
                setPreviewJobId(job.id);
              }}
            />
          </div>
        </div>
      </div>

      <ProjectFormDialog
        open={creatingProject}
        onOpenChange={setCreatingProject}
        onCreated={(p) => setProjectId(p.id)}
      />
    </>
  );
}

export default function StudioPage() {
  return (
    <React.Suspense>
      <StudioInner />
    </React.Suspense>
  );
}
