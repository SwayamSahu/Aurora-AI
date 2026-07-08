"use client";

import * as React from "react";
import { toast } from "sonner";
import { Layers, X } from "lucide-react";

import { useEditorStore } from "@/lib/editor/store";
import { findClip } from "@/lib/editor/helpers";
import {
  type SelectionTool,
  type BrushSettings,
  DEFAULT_BRUSH,
} from "@/lib/editor/ai-edit/mask";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  EditCanvas,
  type EditCanvasHandle,
} from "@/components/editor/ai-edit/edit-canvas";
import { SelectionTools } from "@/components/editor/ai-edit/selection-tools";
import { BrushControls } from "@/components/editor/ai-edit/brush-controls";
import { PromptPanel } from "@/components/editor/ai-edit/prompt-panel";

interface DraftEdit {
  id: string;
  summary: string;
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

/**
 * The AI Edit mode workspace: canvas + tool strip in the center column,
 * prompt/preset panel on the right. Draft edit layers are kept locally in
 * E1; they become persisted, rendered layers in E2.
 */
export function AiEditWorkspace() {
  const document_ = useEditorStore((s) => s.document);
  const selectedClipId = useEditorStore((s) => s.selectedClipId);
  const clip = selectedClipId ? findClip(document_, selectedClipId) : undefined;

  const [tool, setTool] = React.useState<SelectionTool>("brush");
  const [brush, setBrush] = React.useState<BrushSettings>(DEFAULT_BRUSH);
  const [hasInk, setHasInk] = React.useState(false);
  const [drafts, setDrafts] = React.useState<DraftEdit[]>([]);
  const canvasRef = React.useRef<EditCanvasHandle>(null);

  // Tool shortcuts (B/E/L/R/O, [ ] size) — only while AI Edit is mounted.
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

        {/* Draft layers (local in E1) */}
        {drafts.length > 0 ? (
          <div className="rounded-lg border bg-card p-3">
            <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              <Layers className="size-3.5" /> Edit layers · {drafts.length}
            </p>
            <ul className="space-y-1.5">
              {drafts.map((d) => (
                <li
                  key={d.id}
                  className="flex items-center justify-between gap-2 rounded-md bg-accent/40 px-2.5 py-1.5 text-xs"
                >
                  <span className="truncate">{d.summary}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label="Remove draft edit"
                    className="size-6 shrink-0"
                    onClick={() =>
                      setDrafts((ds) => ds.filter((x) => x.id !== d.id))
                    }
                  >
                    <X className="size-3.5" />
                  </Button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>

      {/* Right: prompt/preset panel */}
      <Card>
        <CardContent className="p-4">
          <PromptPanel
            hasInk={hasInk}
            onApplied={(summary) => {
              setDrafts((ds) => [
                ...ds,
                { id: `draft-${Date.now()}`, summary },
              ]);
              canvasRef.current?.clear();
              toast.success(
                "Edit queued as a draft layer. Rendering lands with the edit backend (E2).",
              );
            }}
          />
        </CardContent>
      </Card>
    </>
  );
}
