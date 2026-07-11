"use client";

import { Check } from "lucide-react";

import { cn } from "@/lib/utils";
import { getToken } from "@/lib/api/token";
import { absoluteMediaUrl } from "@/lib/marketplace/api";
import { useMySellableAssets } from "@/lib/marketplace/queries";
import type { SellableAsset } from "@/lib/marketplace/types";
import { Skeleton } from "@/components/ui/skeleton";

export function AssetPicker({
  value,
  onChange,
}: {
  value: string | null;
  onChange: (assetId: string, asset: SellableAsset) => void;
}) {
  const { data: assets, isLoading } = useMySellableAssets();
  const token = getToken();

  if (isLoading) {
    return (
      <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="aspect-square w-full" />
        ))}
      </div>
    );
  }

  if (!assets || assets.length === 0) {
    return (
      <p className="rounded-xl border border-dashed border-[var(--mk-border-strong)] p-6 text-center text-sm text-muted-foreground">
        You don&apos;t have any generated videos or images yet.{" "}
        <a href="/studio" className="text-mk-lavender hover:underline">
          Create one
        </a>{" "}
        first.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-3 sm:grid-cols-4">
      {assets.map((asset) => {
        const selected = value === asset.id;
        const url = absoluteMediaUrl(asset.content_url);
        const previewUrl = token ? `${url}?token=${token}` : url;
        return (
          <button
            key={asset.id}
            type="button"
            onClick={() => onChange(asset.id, asset)}
            className={cn(
              "relative aspect-square overflow-hidden rounded-lg border-2 bg-[var(--mk-surface-2)]",
              selected
                ? "border-mk-lavender"
                : "border-transparent hover:border-[var(--mk-border-strong)]",
            )}
          >
            {asset.kind === "image" ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={previewUrl} alt={asset.name} className="size-full object-cover" />
            ) : (
              <video src={previewUrl} muted className="size-full object-cover" />
            )}
            {selected ? (
              <span className="absolute right-1.5 top-1.5 grid size-5 place-items-center rounded-full bg-mk-lavender text-black">
                <Check className="size-3.5" />
              </span>
            ) : null}
            <span className="absolute inset-x-0 bottom-0 truncate bg-black/60 px-1.5 py-1 text-[10px] text-white">
              {asset.name}
            </span>
          </button>
        );
      })}
    </div>
  );
}
