"use client";

import { Music, Plus, Video as VideoIcon, Image as ImageIcon } from "lucide-react";

import { type Asset, type AssetKind, assetContentUrl } from "@/lib/api/assets";
import { useAssets } from "@/lib/query/assets";
import { useEditorStore } from "@/lib/editor/store";
import { Skeleton } from "@/components/ui/skeleton";

const ADDABLE: AssetKind[] = ["video", "image", "audio"];
const ICON = { video: VideoIcon, image: ImageIcon, audio: Music, subtitles: Music };

export function AssetTray({ projectId }: { projectId: string }) {
  const { data: assets, isLoading } = useAssets(projectId);
  const addClipFromAsset = useEditorStore((s) => s.addClipFromAsset);

  const usable = (assets ?? []).filter((a) => ADDABLE.includes(a.kind));

  function add(asset: Asset) {
    addClipFromAsset({
      assetId: asset.id,
      kind: asset.kind === "audio" ? "audio" : asset.kind === "image" ? "image" : "video",
      duration: asset.duration_seconds ?? 4,
    });
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="aspect-video w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (usable.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-border px-3 py-6 text-center text-xs text-muted-foreground">
        No media yet. Generate or upload assets in the project, then add them here.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-2">
      {usable.map((asset) => {
        const Icon = ICON[asset.kind];
        return (
          <button
            key={asset.id}
            onClick={() => add(asset)}
            className="group relative overflow-hidden rounded-lg border border-border text-left transition-colors hover:border-primary/50"
            title={`Add ${asset.name}`}
          >
            <div className="flex aspect-video items-center justify-center bg-muted">
              {asset.kind === "image" ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={assetContentUrl(asset)} alt="" className="size-full object-cover" />
              ) : asset.kind === "video" ? (
                <video
                  src={assetContentUrl(asset)}
                  muted
                  preload="metadata"
                  className="size-full object-cover"
                />
              ) : (
                <Icon className="size-6 text-muted-foreground/60" />
              )}
              <div className="absolute inset-0 flex items-center justify-center bg-black/0 opacity-0 transition group-hover:bg-black/40 group-hover:opacity-100">
                <Plus className="size-6 text-white" />
              </div>
            </div>
            <p className="truncate px-2 py-1 text-xs">{asset.name}</p>
          </button>
        );
      })}
    </div>
  );
}
