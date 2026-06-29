import { apiFetch } from "@/lib/api/client";
import { API_BASE } from "@/lib/api/config";
import { getToken } from "@/lib/api/token";

export type AssetKind = "video" | "image" | "audio" | "subtitles";
export type AssetSource = "generated" | "uploaded" | "derived";

export interface Asset {
  id: string;
  project_id: string;
  name: string;
  kind: AssetKind;
  source: AssetSource;
  content_type: string;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  created_at: string;
  /** Relative API path to the bytes. Use assetContentUrl() to load. */
  url: string;
}

/** Absolute, authenticated URL usable directly in <img>/<video> src. */
export function assetContentUrl(asset: Asset): string {
  const token = getToken();
  return `${API_BASE}${asset.url}${token ? `?token=${encodeURIComponent(token)}` : ""}`;
}

export function listAssets(projectId: string, kind?: AssetKind) {
  const qs = kind ? `?kind=${kind}` : "";
  return apiFetch<Asset[]>(`/projects/${projectId}/assets${qs}`);
}

export async function uploadAsset(projectId: string, file: File): Promise<Asset> {
  const form = new FormData();
  form.append("file", file);
  const token = getToken();
  const res = await fetch(
    `${API_BASE}/api/v1/projects/${projectId}/assets`,
    {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      body: form,
    },
  );
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json())?.detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export function renameAsset(assetId: string, name: string) {
  return apiFetch<Asset>(`/assets/${assetId}`, { method: "PATCH", json: { name } });
}

export function deleteAsset(assetId: string) {
  return apiFetch<void>(`/assets/${assetId}`, { method: "DELETE" });
}
