"use client";

import * as React from "react";

import type { Asset } from "@/lib/api/assets";

const AssetsContext = React.createContext<Record<string, Asset>>({});

export function EditorAssetsProvider({
  assets,
  children,
}: {
  assets: Asset[];
  children: React.ReactNode;
}) {
  const map = React.useMemo(() => {
    const m: Record<string, Asset> = {};
    for (const a of assets) m[a.id] = a;
    return m;
  }, [assets]);
  return (
    <AssetsContext.Provider value={map}>{children}</AssetsContext.Provider>
  );
}

export function useAsset(assetId?: string | null): Asset | undefined {
  const map = React.useContext(AssetsContext);
  return assetId ? map[assetId] : undefined;
}
