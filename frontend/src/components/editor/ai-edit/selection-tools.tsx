"use client";

import {
  Brush,
  Eraser,
  Lasso,
  Square,
  Circle,
  Trash2,
} from "lucide-react";

import { cn } from "@/lib/utils";
import type { SelectionTool } from "@/lib/editor/ai-edit/mask";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const TOOLS: { id: SelectionTool; label: string; keys: string; icon: typeof Brush }[] = [
  { id: "brush", label: "AI Pencil (brush)", keys: "B", icon: Brush },
  { id: "eraser", label: "Eraser", keys: "E", icon: Eraser },
  { id: "lasso", label: "Lasso", keys: "L", icon: Lasso },
  { id: "rect", label: "Rectangle", keys: "R", icon: Square },
  { id: "ellipse", label: "Ellipse", keys: "O", icon: Circle },
];

export function SelectionTools({
  tool,
  onTool,
  onClear,
  canClear,
}: {
  tool: SelectionTool;
  onTool: (t: SelectionTool) => void;
  onClear: () => void;
  canClear: boolean;
}) {
  return (
    <div className="flex items-center gap-1">
      {TOOLS.map((t) => (
        <Tooltip key={t.id}>
          <TooltipTrigger asChild>
            <Button
              variant={tool === t.id ? "default" : "ghost"}
              size="icon"
              aria-label={t.label}
              aria-pressed={tool === t.id}
              onClick={() => onTool(t.id)}
              className={cn("size-8", tool === t.id && "shadow-sm")}
            >
              <t.icon className="size-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            {t.label} <kbd className="ml-1 opacity-70">{t.keys}</kbd>
          </TooltipContent>
        </Tooltip>
      ))}
      <div className="mx-1 h-5 w-px bg-border" />
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Clear selection"
            onClick={onClear}
            disabled={!canClear}
            className="size-8"
          >
            <Trash2 className="size-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent side="bottom">Clear selection</TooltipContent>
      </Tooltip>
    </div>
  );
}
