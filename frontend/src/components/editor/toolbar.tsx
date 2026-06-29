"use client";

import {
  Type,
  Scissors,
  Trash2,
  Copy,
  Undo2,
  Redo2,
  ZoomIn,
  ZoomOut,
  Check,
  Download,
  Loader2,
} from "lucide-react";

import { useEditorStore } from "@/lib/editor/store";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

function ToolButton({
  label,
  onClick,
  disabled,
  children,
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          size="icon"
          variant="ghost"
          className="size-8"
          onClick={onClick}
          disabled={disabled}
          aria-label={label}
        >
          {children}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{label}</TooltipContent>
    </Tooltip>
  );
}

function SaveIndicator() {
  const status = useEditorStore((s) => s.saveStatus);
  if (status === "saving")
    return (
      <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Loader2 className="size-3.5 animate-spin" /> Saving…
      </span>
    );
  if (status === "saved")
    return (
      <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
        <Check className="size-3.5 text-success" /> Saved
      </span>
    );
  if (status === "dirty")
    return <span className="text-xs text-muted-foreground">Unsaved changes</span>;
  return null;
}

interface EditorToolbarProps {
  onExport?: () => void;
}

export function EditorToolbar({ onExport }: EditorToolbarProps) {
  const addTextClip = useEditorStore((s) => s.addTextClip);
  const splitAtPlayhead = useEditorStore((s) => s.splitAtPlayhead);
  const duplicateSelected = useEditorStore((s) => s.duplicateSelected);
  const removeClip = useEditorStore((s) => s.removeClip);
  const undo = useEditorStore((s) => s.undo);
  const redo = useEditorStore((s) => s.redo);
  const setPxPerSec = useEditorStore((s) => s.setPxPerSec);
  const pxPerSec = useEditorStore((s) => s.pxPerSec);
  const selectedClipId = useEditorStore((s) => s.selectedClipId);
  const canUndo = useEditorStore((s) => s.past.length > 0);
  const canRedo = useEditorStore((s) => s.future.length > 0);

  return (
    <div className="flex items-center gap-1 rounded-lg border border-border bg-card px-2 py-1.5">
      <ToolButton label="Add text" onClick={addTextClip}>
        <Type className="size-4" />
      </ToolButton>
      <ToolButton
        label="Split at playhead (S)"
        onClick={splitAtPlayhead}
        disabled={!selectedClipId}
      >
        <Scissors className="size-4" />
      </ToolButton>
      <ToolButton
        label="Duplicate"
        onClick={duplicateSelected}
        disabled={!selectedClipId}
      >
        <Copy className="size-4" />
      </ToolButton>
      <ToolButton
        label="Delete (⌫)"
        onClick={() => selectedClipId && removeClip(selectedClipId)}
        disabled={!selectedClipId}
      >
        <Trash2 className="size-4" />
      </ToolButton>

      <Separator orientation="vertical" className="mx-1 h-6" />

      <ToolButton label="Undo (⌘Z)" onClick={undo} disabled={!canUndo}>
        <Undo2 className="size-4" />
      </ToolButton>
      <ToolButton label="Redo (⌘⇧Z)" onClick={redo} disabled={!canRedo}>
        <Redo2 className="size-4" />
      </ToolButton>

      <Separator orientation="vertical" className="mx-1 h-6" />

      <ToolButton label="Zoom out" onClick={() => setPxPerSec(pxPerSec - 20)}>
        <ZoomOut className="size-4" />
      </ToolButton>
      <ToolButton label="Zoom in" onClick={() => setPxPerSec(pxPerSec + 20)}>
        <ZoomIn className="size-4" />
      </ToolButton>

      <div className="ml-auto flex items-center gap-2 pr-1">
        <SaveIndicator />
        {onExport ? (
          <>
            <Separator orientation="vertical" className="mx-0.5 h-6" />
            <Button size="sm" onClick={onExport} className="gap-1.5">
              <Download className="size-3.5" /> Export
            </Button>
          </>
        ) : null}
      </div>
    </div>
  );
}
