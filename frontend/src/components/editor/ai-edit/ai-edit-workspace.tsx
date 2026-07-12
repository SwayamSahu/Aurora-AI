"use client";

import * as React from "react";
import { toast } from "sonner";

import { Search, Loader2 } from "lucide-react";

import { useEditorStore } from "@/lib/editor/store";
import { findClip } from "@/lib/editor/helpers";
import { assetContentUrl } from "@/lib/api/assets";
import { ApiError } from "@/lib/api/client";
import {
  type SelectionTool,
  type BrushSettings,
  type TrackedObject,
  DEFAULT_BRUSH,
  exportMask,
} from "@/lib/editor/ai-edit/mask";
import { detectObjects, type EditLayer } from "@/lib/editor/ai-edit/api";
import {
  useCreateEdit,
  useEditLayers,
} from "@/lib/editor/ai-edit/queries";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { TrackingPanel } from "@/components/editor/ai-edit/tracking-panel";
import { CompareSlider } from "@/components/editor/ai-edit/compare-slider";

let objectIdSeq = 0;
function nextObjectId(): string {
  objectIdSeq += 1;
  return `obj-${Date.now()}-${objectIdSeq}`;
}

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
  const [objects, setObjects] = React.useState<TrackedObject[]>([]);
  const [objectsClipId, setObjectsClipId] = React.useState(clip?.id);
  const [query, setQuery] = React.useState("");
  const [detecting, setDetecting] = React.useState(false);
  const canvasRef = React.useRef<EditCanvasHandle>(null);

  const layersQuery = useEditLayers(projectId, clip?.id);
  const createEdit = useCreateEdit(projectId, clip?.id);

  // Tracked objects are per-clip — reset when the selected clip changes.
  // (React's recommended "adjust state during render" pattern, so this
  // doesn't cost an extra render like an effect-based reset would.)
  if (clip?.id !== objectsClipId) {
    setObjectsClipId(clip?.id);
    setObjects([]);
  }

  // Tool shortcuts (V select, B/E/L/R/O, [ ] size).
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (isTypingTarget(e.target) || e.metaKey || e.ctrlKey) return;
      const k = e.key.toLowerCase();
      const map: Record<string, SelectionTool> = {
        v: "select",
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

  function addObject(o: {
    label: string;
    x: number;
    y: number;
    w: number;
    h: number;
    confidence: number;
  }) {
    const tracked: TrackedObject = {
      id: nextObjectId(),
      ...o,
      startTime: 0,
      endTime: clip!.duration,
    };
    setObjects((prev) => [...prev, tracked]);
    canvasRef.current?.paintRect(o.x, o.y, o.w, o.h);
  }

  async function onSelectClick(xNorm: number, yNorm: number) {
    setDetecting(true);
    try {
      const [found] = await detectObjects(
        projectId,
        { mode: "click", x: xNorm, y: yNorm },
        clip!.asset_id,
      );
      if (found) addObject(found);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Detection failed.");
    } finally {
      setDetecting(false);
    }
  }

  async function onFindAll() {
    if (!query.trim()) return;
    setDetecting(true);
    try {
      const found = await detectObjects(
        projectId,
        { mode: "text", query: query.trim() },
        clip!.asset_id,
      );
      found.forEach(addObject);
      if (found.length === 0) toast.info("No matches found.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Detection failed.");
    } finally {
      setDetecting(false);
    }
  }

  function removeObject(id: string) {
    setObjects((prev) => prev.filter((o) => o.id !== id));
  }

  function updateObjectRange(id: string, startTime: number, endTime: number) {
    setObjects((prev) =>
      prev.map((o) => (o.id === id ? { ...o, startTime, endTime } : o)),
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
    if (hasInk && mask) maskBase64 = exportMask(mask, brush.feather);

    try {
      await createEdit.mutateAsync({
        clip_id: clip.id,
        engine: edit.engine,
        preset_id: edit.presetId,
        label: edit.label,
        prompt: edit.prompt,
        params: edit.params,
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

        {tool === "select" ? (
          <div className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2">
            <Search className="size-4 shrink-0 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onFindAll()}
              placeholder="Select all… e.g. “car”"
              className="h-8"
            />
            <Button size="sm" onClick={onFindAll} loading={detecting}>
              Find
            </Button>
          </div>
        ) : null}

        <EditCanvas
          ref={canvasRef}
          clip={clip}
          tool={tool}
          brush={brush}
          onInkChange={setHasInk}
          onSelectClick={onSelectClick}
          objects={objects}
          onRemoveObject={removeObject}
        />
        {detecting ? (
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Loader2 className="size-3 animate-spin" /> Detecting…
          </p>
        ) : null}

        <TrackingPanel
          objects={objects}
          clipDuration={clip.duration}
          onChangeRange={updateObjectRange}
          onRemove={removeObject}
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
