"use client";

import * as React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { ArrowLeft } from "lucide-react";

import { getTimeline, saveTimeline } from "@/lib/api/timeline";
import { useProject } from "@/lib/query/projects";
import { useAssets } from "@/lib/query/assets";
import { useEditorStore } from "@/lib/editor/store";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { EditorAssetsProvider } from "@/components/editor/assets-context";
import { EditorToolbar } from "@/components/editor/toolbar";
import { PreviewCanvas } from "@/components/editor/preview-canvas";
import { Timeline } from "@/components/editor/timeline";
import { Inspector } from "@/components/editor/inspector";
import { AssetTray } from "@/components/editor/asset-tray";
import { AiPanel } from "@/components/editor/ai-panel";
import { ExportDialog } from "@/components/editor/export-dialog";
import { Separator } from "@/components/ui/separator";

function isTypingTarget(el: EventTarget | null): boolean {
  const node = el as HTMLElement | null;
  if (!node) return false;
  const tag = node.tagName;
  return (
    tag === "INPUT" ||
    tag === "TEXTAREA" ||
    tag === "SELECT" ||
    node.isContentEditable
  );
}

function EditorWorkspace({ projectId }: { projectId: string }) {
  const project = useProject(projectId);
  const assets = useAssets(projectId);
  const [exporting, setExporting] = React.useState(false);

  const load = useEditorStore((s) => s.load);
  const loaded = useEditorStore((s) => s.loaded);
  const storeProjectId = useEditorStore((s) => s.projectId);
  const document = useEditorStore((s) => s.document);
  const saveStatus = useEditorStore((s) => s.saveStatus);
  const setSaveStatus = useEditorStore((s) => s.setSaveStatus);

  const timeline = useQuery({
    queryKey: ["timeline", projectId],
    queryFn: () => getTimeline(projectId),
  });

  // Load the document into the editor store once fetched.
  React.useEffect(() => {
    if (timeline.data && storeProjectId !== projectId) {
      load(projectId, timeline.data.document);
    }
  }, [timeline.data, storeProjectId, projectId, load]);

  // Debounced autosave.
  React.useEffect(() => {
    if (!loaded || storeProjectId !== projectId || saveStatus !== "dirty") return;
    const t = setTimeout(async () => {
      setSaveStatus("saving");
      try {
        await saveTimeline(projectId, useEditorStore.getState().document);
        setSaveStatus("saved");
      } catch {
        setSaveStatus("dirty");
        toast.error("Couldn't save changes.");
      }
    }, 800);
    return () => clearTimeout(t);
  }, [document, saveStatus, loaded, storeProjectId, projectId, setSaveStatus]);

  // Keyboard shortcuts.
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (isTypingTarget(e.target)) return;
      const s = useEditorStore.getState();
      const meta = e.metaKey || e.ctrlKey;
      if (meta && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) s.redo();
        else s.undo();
      } else if (e.key === " ") {
        e.preventDefault();
        s.togglePlay();
      } else if (e.key === "Delete" || e.key === "Backspace") {
        if (s.selectedClipId) {
          e.preventDefault();
          s.removeClip(s.selectedClipId);
        }
      } else if (e.key.toLowerCase() === "s" && !meta) {
        e.preventDefault();
        s.splitAtPlayhead();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const ready = timeline.isSuccess && loaded && storeProjectId === projectId;

  return (
    <EditorAssetsProvider assets={assets.data ?? []}>
      <div className="mb-2 flex items-center justify-between">
        <Button
          asChild
          variant="ghost"
          size="sm"
          className="-ml-2 text-muted-foreground"
        >
          <Link href={`/projects/${projectId}`}>
            <ArrowLeft className="size-4" /> {project.data?.name ?? "Project"}
          </Link>
        </Button>
      </div>

      <EditorToolbar onExport={() => setExporting(true)} />

      {!ready ? (
        <div className="mt-4 space-y-4">
          <Skeleton className="h-64 w-full rounded-xl" />
          <Skeleton className="h-48 w-full rounded-xl" />
        </div>
      ) : (
        <>
          <div className="mt-4 grid gap-4 lg:grid-cols-[15rem_minmax(0,1fr)_17rem]">
            <Card className="hidden lg:block">
              <CardContent className="space-y-3 p-3">
                <AiPanel projectId={projectId} />
                <Separator />
                <div>
                  <p className="mb-2 px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Media
                  </p>
                  <ScrollArea className="h-[320px] pr-2">
                    <AssetTray projectId={projectId} />
                  </ScrollArea>
                </div>
              </CardContent>
            </Card>

            <PreviewCanvas />

            <Card>
              <CardContent className="p-4">
                <Inspector />
              </CardContent>
            </Card>
          </div>

          <div className="mt-4">
            <Timeline />
          </div>
        </>
      )}
      <ExportDialog
        projectId={projectId}
        projectName={project.data?.name ?? "Project"}
        open={exporting}
        onOpenChange={setExporting}
      />
    </EditorAssetsProvider>
  );
}

export default function EditorPage() {
  const params = useParams<{ id: string }>();
  return <EditorWorkspace projectId={params.id} />;
}
