"use client";

import { Loader2, Eye, EyeOff, Trash2, AlertCircle, Check } from "lucide-react";

import { cn } from "@/lib/utils";
import type { EditLayer } from "@/lib/editor/ai-edit/api";
import {
  useDeleteEdit,
  usePatchEdit,
} from "@/lib/editor/ai-edit/queries";
import { Button } from "@/components/ui/button";

function StatusDot({ layer }: { layer: EditLayer }) {
  if (layer.status === "running" || layer.status === "queued")
    return <Loader2 className="size-3.5 animate-spin text-primary" />;
  if (layer.status === "failed")
    return <AlertCircle className="size-3.5 text-destructive" />;
  return <Check className="size-3.5 text-success" />;
}

export function EditLayersPanel({
  projectId,
  clipId,
  layers,
  onCompare,
}: {
  projectId: string;
  clipId: string;
  layers: EditLayer[];
  onCompare: (layer: EditLayer) => void;
}) {
  const patch = usePatchEdit(projectId, clipId);
  const remove = useDeleteEdit(projectId, clipId);

  if (layers.length === 0) return null;

  return (
    <div className="rounded-lg border bg-card p-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Edit layers · {layers.length}
      </p>
      <ul className="space-y-1.5">
        {layers.map((layer) => (
          <li
            key={layer.id}
            className={cn(
              "flex items-center gap-2 rounded-md px-2 py-1.5 text-xs",
              layer.enabled ? "bg-accent/40" : "bg-muted/30 opacity-60",
            )}
          >
            <StatusDot layer={layer} />
            <button
              type="button"
              onClick={() => layer.result_asset && onCompare(layer)}
              disabled={!layer.result_asset}
              className="min-w-0 flex-1 truncate text-left hover:underline disabled:cursor-default disabled:no-underline"
              title={layer.prompt || layer.label}
            >
              {layer.label || layer.engine}
              {layer.status === "running" || layer.status === "queued" ? (
                <span className="ml-1 tabular-nums text-muted-foreground">
                  {Math.round(layer.progress * 100)}%
                </span>
              ) : null}
              {layer.status === "failed" && layer.error ? (
                <span className="ml-1 text-destructive">— {layer.error}</span>
              ) : null}
            </button>

            <Button
              variant="ghost"
              size="icon"
              className="size-6"
              aria-label={layer.enabled ? "Hide layer" : "Show layer"}
              onClick={() =>
                patch.mutate({ id: layer.id, patch: { enabled: !layer.enabled } })
              }
            >
              {layer.enabled ? (
                <Eye className="size-3.5" />
              ) : (
                <EyeOff className="size-3.5" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="size-6"
              aria-label="Delete layer"
              onClick={() => remove.mutate(layer.id)}
            >
              <Trash2 className="size-3.5" />
            </Button>
          </li>
        ))}
      </ul>
    </div>
  );
}
