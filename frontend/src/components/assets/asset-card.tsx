"use client";

import * as React from "react";
import {
  MoreVertical,
  Download,
  Pencil,
  Trash2,
  Music,
  Captions,
  Video,
  Image as ImageIcon,
} from "lucide-react";
import { toast } from "sonner";

import {
  type Asset,
  type AssetKind,
  assetContentUrl,
} from "@/lib/api/assets";
import { useDeleteAsset, useRenameAsset } from "@/lib/query/assets";
import { formatDuration } from "@/lib/format";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";

const KIND_ICON: Record<AssetKind, React.ComponentType<{ className?: string }>> = {
  video: Video,
  image: ImageIcon,
  audio: Music,
  subtitles: Captions,
};

function Preview({ asset }: { asset: Asset }) {
  const url = assetContentUrl(asset);
  if (asset.kind === "image") {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={url} alt={asset.name} className="size-full object-cover" />;
  }
  if (asset.kind === "video") {
    return (
      <video
        src={url}
        preload="metadata"
        muted
        playsInline
        className="size-full object-cover"
      />
    );
  }
  const Icon = KIND_ICON[asset.kind];
  return (
    <div className="flex size-full items-center justify-center">
      <Icon className="size-8 text-muted-foreground/60" />
    </div>
  );
}

export function AssetCard({
  asset,
  projectId,
}: {
  asset: Asset;
  projectId: string;
}) {
  const [renaming, setRenaming] = React.useState(false);
  const [name, setName] = React.useState(asset.name);
  const [confirmingDelete, setConfirmingDelete] = React.useState(false);
  const rename = useRenameAsset(projectId);
  const del = useDeleteAsset(projectId);

  async function handleRename() {
    try {
      await rename.mutateAsync({ id: asset.id, name });
      toast.success("Asset renamed.");
      setRenaming(false);
    } catch {
      toast.error("Could not rename asset.");
    }
  }

  async function handleDelete() {
    try {
      await del.mutateAsync(asset.id);
      toast.success("Asset deleted.");
      setConfirmingDelete(false);
    } catch {
      toast.error("Could not delete asset.");
    }
  }

  return (
    <>
      <Card className="group relative overflow-hidden">
        <div className="flex aspect-video items-center justify-center bg-muted">
          <Preview asset={asset} />
          <Badge
            variant="secondary"
            className="absolute left-2 top-2 capitalize"
          >
            {asset.kind}
          </Badge>
          {asset.duration_seconds ? (
            <Badge className="absolute bottom-2 right-2 bg-black/70 text-white">
              {formatDuration(asset.duration_seconds)}
            </Badge>
          ) : null}
        </div>
        <div className="flex items-center gap-2 p-3">
          <p className="min-w-0 flex-1 truncate text-sm font-medium" title={asset.name}>
            {asset.name}
          </p>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                size="icon"
                variant="ghost"
                className="size-7 shrink-0"
                aria-label="Asset actions"
              >
                <MoreVertical className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <a href={assetContentUrl(asset)} target="_blank" rel="noreferrer">
                  <Download /> Download
                </a>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setRenaming(true)}>
                <Pencil /> Rename
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => setConfirmingDelete(true)}
              >
                <Trash2 /> Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </Card>

      <Dialog open={renaming} onOpenChange={setRenaming}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename asset</DialogTitle>
          </DialogHeader>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleRename()}
            autoFocus
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setRenaming(false)}>
              Cancel
            </Button>
            <Button onClick={handleRename} loading={rename.isPending}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={confirmingDelete}
        onOpenChange={setConfirmingDelete}
        title="Delete asset?"
        description={`"${asset.name}" will be permanently removed.`}
        confirmLabel="Delete"
        destructive
        loading={del.isPending}
        onConfirm={handleDelete}
      />
    </>
  );
}
