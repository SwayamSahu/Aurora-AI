"use client";

import * as React from "react";
import { toast } from "sonner";

import { useEditorStore } from "@/lib/editor/store";
import { findClip } from "@/lib/editor/helpers";
import { assetContentUrl } from "@/lib/api/assets";
import { ApiError } from "@/lib/api/client";
import {
  type SelectionTool,
  type BrushSettings,
  DEFAULT_BRUSH,
  exportMask,
} from "@/lib/editor/ai-edit/mask";
import type { EditLayer } from "@/lib/editor/ai-edit/api";
import {
  useCreateEdit,
  useEditLayers,
} from "@/lib/editor/ai-edit/queries";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAsset } from "@/components/editor/assets-context";
import {
  EditCanvas,
  type EditCanvasHandle,
} from "@/components/editor/ai-edit/edit-canvas";
import { SelectionTools } from "@/components/editor/ai-edit/selection-tools";
import { BrushControls } from "@/components/editor/ai-edit/brush-controls";
import {
  PromptPanel,
  type AppliedEdit,
} from "@/components/editor/ai-edit/prompt-panel";
import { EditLayersPanel } from "@/components/editor/ai-edit/edit-layers-panel";
import { CompareSlider } from "@/components/editor/ai-edit/compare-slider";

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

export function AiEditWorkspace({ projectId }: { projectId: string }) {
  const document_ = useEditorStore((s) => s.document);
  const selectedClipId = useEditorStore((s) => s.selectedClipId);
  const clip = selectedClipId ? findClip(document_, selectedClipId) : undefined;
  const clipAsset = useAsset(clip?.asset_id);

  const [tool, setTool] = React.useState<SelectionTool>("brush");
  const [brush, setBrush] = React.useState<BrushSettings>(DEFAULT_BRUSH);
  const [hasInk, setHasInk] = React.useState(false);
  const [compare, setCompare] = React.useState<EditLayer | null>(null);
  const canvasRef = React.useRef<EditCanvasHandle>(null);

  const layersQuery = useEditLayers(projectId, clip?.id);
  const createEdit = useCreateEdit(projectId, clip?.id);

  // Tool shortcuts (B/E/L/R/O, [ ] size).
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (isTypingTarget(e.target) || e.metaKey || e.ctrlKey) return;
      const k = e.key.toLowerCase();
      const map: Record<string, SelectionTool> = {
        b: "brush",
        e: "eraser",
        l: "lasso",
        r: "rect",
        o: "ellipse",
      };
      if (map[k]) {
        e.preventDefault();
        setTool(map[k]);
      } else if (e.key === "[") {
        setBrush((b) => ({ ...b, size: Math.max(4, b.size - 6) }));
      } else if (e.key === "]") {
        setBrush((b) => ({ ...b, size: Math.min(200, b.size + 6) }));
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!clip || clip.kind !== "video") {
    return (
      <Card className="lg:col-span-2">
        <CardContent className="grid h-64 place-items-center p-6 text-center">
          <div>
            <p className="font-medium">Select a video clip to start AI editing</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Click a clip on the timeline below, then paint, pick a preset and
              describe the change.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  async function onApply(edit: AppliedEdit) {
    if (!clip?.asset_id) {
      toast.error("This clip has no source media to edit.");
      return;
    }
    // Send the painted mask only when there's ink (auto/full-frame presets
    // without a painted region run full-frame on the backend).
    let maskBase64: string | null = null;
    const mask = canvasRef.current?.getMaskCanvas();
    if (hasInk && mask) maskBase64 = exportMask(mask);

    try {
      await createEdit.mutateAsync({
        clip_id: clip.id,
        engine: edit.engine,
        preset_id: edit.presetId,
        label: edit.label,
        prompt: edit.prompt,
        source_asset_id: clip.asset_id,
        mask_base64: maskBase64,
      });
      canvasRef.current?.clear();
      toast.success("Edit queued — processing on the render backend.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Couldn't queue edit.");
    }
  }

  const layers = layersQuery.data ?? [];

  return (
    <>
      {/* Center: canvas + tool strip */}
      <div className="min-w-0 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border bg-card px-3 py-2">
          <SelectionTools
            tool={tool}
            onTool={setTool}
            onClear={() => canvasRef.current?.clear()}
            canClear={hasInk}
          />
          <div className="w-full max-w-sm">
            <BrushControls brush={brush} onChange={setBrush} />
          </div>
        </div>

        <EditCanvas
          ref={canvasRef}
          clip={clip}
          tool={tool}
          brush={brush}
          onInkChange={setHasInk}
        />

        <EditLayersPanel
          projectId={projectId}
          clipId={clip.id}
          layers={layers}
          onCompare={setCompare}
        />
      </div>

      {/* Right: prompt/preset panel */}
      <Card>
        <CardContent className="p-4">
          <PromptPanel
            hasInk={hasInk}
            applying={createEdit.isPending}
            onApply={onApply}
          />
          <p className="mt-2 text-center text-[11px] text-muted-foreground">
            Tip: paint a region for local edits, or apply a preset to the whole
            clip.
          </p>
        </CardContent>
      </Card>

      {/* Before/after compare */}
      <Dialog open={!!compare} onOpenChange={(o) => !o && setCompare(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>{compare?.label || "Compare"}</DialogTitle>
          </DialogHeader>
          {compare?.result_asset && clipAsset ? (
            <CompareSlider
              beforeUrl={assetContentUrl(clipAsset)}
              afterUrl={assetContentUrl(compare.result_asset)}
            />
          ) : null}
        </DialogContent>
      </Dialog>
    </>
  );
}
