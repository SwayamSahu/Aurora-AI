"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Clapperboard, Download, Pencil, Sparkles, ImageOff } from "lucide-react";

import type { AssetKind } from "@/lib/api/assets";
import { useProject } from "@/lib/query/projects";
import { useAssets } from "@/lib/query/assets";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { ProjectFormDialog } from "@/components/projects/project-form-dialog";
import { AssetUploader } from "@/components/assets/asset-uploader";
import { AssetCard } from "@/components/assets/asset-card";
import { GenerationDialog } from "@/components/generation/generation-dialog";
import { ExportDialog } from "@/components/editor/export-dialog";

const KINDS: { value: "all" | AssetKind; label: string }[] = [
  { value: "all", label: "All" },
  { value: "video", label: "Video" },
  { value: "image", label: "Images" },
  { value: "audio", label: "Audio" },
  { value: "subtitles", label: "Subtitles" },
];

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const [editing, setEditing] = React.useState(false);
  const [generating, setGenerating] = React.useState(false);
  const [exporting, setExporting] = React.useState(false);
  const [kind, setKind] = React.useState<"all" | AssetKind>("all");

  const project = useProject(projectId);
  const assets = useAssets(
    projectId,
    kind === "all" ? undefined : kind,
  );

  if (project.isError) {
    return (
      <ErrorState
        title="Project not found"
        description="This project doesn't exist or you don't have access."
        onRetry={() => project.refetch()}
      />
    );
  }

  return (
    <>
      <div className="mb-2">
        <Button asChild variant="ghost" size="sm" className="-ml-2 text-muted-foreground">
          <Link href="/projects">
            <ArrowLeft className="size-4" /> Projects
          </Link>
        </Button>
      </div>

      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          {project.isLoading ? (
            <Skeleton className="h-8 w-64" />
          ) : (
            <h1 className="text-2xl font-semibold tracking-tight">
              {project.data?.name}
            </h1>
          )}
          {project.data?.description ? (
            <p className="max-w-2xl text-sm text-muted-foreground">
              {project.data.description}
            </p>
          ) : null}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setEditing(true)}>
            <Pencil className="size-4" /> Edit
          </Button>
          <Button variant="outline" onClick={() => setExporting(true)}>
            <Download className="size-4" /> Export
          </Button>
          <Button asChild variant="outline">
            <Link href={`/projects/${projectId}/editor`}>
              <Clapperboard className="size-4" /> Editor
            </Link>
          </Button>
          <Button onClick={() => setGenerating(true)}>
            <Sparkles className="size-4" /> Generate
          </Button>
        </div>
      </div>

      <div className="mb-6">
        <AssetUploader projectId={projectId} />
      </div>

      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Asset library</h2>
        <Tabs value={kind} onValueChange={(v) => setKind(v as typeof kind)}>
          <TabsList>
            {KINDS.map((k) => (
              <TabsTrigger key={k.value} value={k.value}>
                {k.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {assets.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="aspect-[4/3] w-full rounded-xl" />
          ))}
        </div>
      ) : assets.isError ? (
        <ErrorState
          description="Couldn't load assets."
          onRetry={() => assets.refetch()}
        />
      ) : assets.data && assets.data.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {assets.data.map((a) => (
            <AssetCard key={a.id} asset={a} projectId={projectId} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={ImageOff}
          title={kind === "all" ? "No assets yet" : `No ${kind} assets`}
          description="Upload media above, or generate clips in the studio. They'll appear here."
        />
      )}

      {project.data ? (
        <ProjectFormDialog
          open={editing}
          onOpenChange={setEditing}
          project={project.data}
        />
      ) : null}
      <GenerationDialog
        open={generating}
        onOpenChange={setGenerating}
        projectId={projectId}
      />
      <ExportDialog
        projectId={projectId}
        projectName={project.data?.name ?? "Project"}
        open={exporting}
        onOpenChange={setExporting}
      />
    </>
  );
}
