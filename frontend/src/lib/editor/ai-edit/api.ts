import { apiFetch } from "@/lib/api/client";
import type { Asset } from "@/lib/api/assets";

export type EditLayerStatus = "queued" | "running" | "succeeded" | "failed";

export interface EditLayer {
  id: string;
  project_id: string;
  clip_id: string;
  engine: string;
  preset_id: string | null;
  label: string;
  prompt: string;
  params: Record<string, unknown>;
  status: EditLayerStatus;
  progress: number;
  error: string | null;
  position: number;
  enabled: boolean;
  result_asset_id: string | null;
  result_asset: Asset | null;
}

export interface CreateEditInput {
  clip_id: string;
  engine: string;
  preset_id?: string | null;
  label?: string;
  prompt?: string;
  params?: Record<string, unknown>;
  source_asset_id?: string | null;
  /** PNG mask as a data URL (white = edit region). */
  mask_base64?: string | null;
}

export function createEdit(projectId: string, input: CreateEditInput) {
  return apiFetch<EditLayer>(`/projects/${projectId}/edits`, {
    method: "POST",
    json: input,
  });
}

export function listEdits(projectId: string, clipId: string) {
  return apiFetch<EditLayer[]>(
    `/projects/${projectId}/edits?clip_id=${encodeURIComponent(clipId)}`,
  );
}

export function patchEdit(
  layerId: string,
  patch: { enabled?: boolean; position?: number; prompt?: string },
) {
  return apiFetch<EditLayer>(`/edits/${layerId}`, {
    method: "PATCH",
    json: patch,
  });
}

export function deleteEdit(layerId: string) {
  return apiFetch<void>(`/edits/${layerId}`, { method: "DELETE" });
}

export interface DetectedObject {
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  confidence: number;
}

export type DetectInput =
  | { mode: "click"; x: number; y: number }
  | { mode: "text"; query: string };

/**
 * `assetId` is the clip's source asset — real (CUDA) detection runs on its
 * first frame. Harmless for the mock backend, which ignores it.
 */
export function detectObjects(
  projectId: string,
  input: DetectInput,
  assetId?: string | null,
) {
  return apiFetch<DetectedObject[]>(`/projects/${projectId}/detect-objects`, {
    method: "POST",
    json: { ...input, asset_id: assetId ?? null },
  });
}
