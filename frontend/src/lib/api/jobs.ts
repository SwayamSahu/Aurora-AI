import { apiFetch } from "@/lib/api/client";
import type { Asset } from "@/lib/api/assets";

export type JobType =
  | "generate_video"
  | "image_to_video"
  | "generate_image"
  | "tts"
  | "transcribe"
  | "music"
  | "export";

export type JobStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

export interface Job {
  id: string;
  project_id: string;
  type: JobType;
  status: JobStatus;
  progress: number;
  params: Record<string, unknown>;
  error: string | null;
  result_asset_id: string | null;
  created_at: string;
  updated_at: string;
  result_asset: Asset | null;
}

export const ACTIVE_STATUSES: JobStatus[] = ["queued", "running"];

export function createJob(
  projectId: string,
  type: JobType,
  params: Record<string, unknown>,
) {
  return apiFetch<Job>(`/projects/${projectId}/jobs`, {
    method: "POST",
    json: { type, params },
  });
}

export function listJobs(params?: {
  projectId?: string;
  status?: JobStatus;
  limit?: number;
}) {
  const q = new URLSearchParams();
  if (params?.projectId) q.set("project_id", params.projectId);
  if (params?.status) q.set("status", params.status);
  if (params?.limit) q.set("limit", String(params.limit));
  const qs = q.toString();
  return apiFetch<Job[]>(`/jobs${qs ? `?${qs}` : ""}`);
}

export function getJob(id: string) {
  return apiFetch<Job>(`/jobs/${id}`);
}

export function retryJob(id: string) {
  return apiFetch<Job>(`/jobs/${id}/retry`, { method: "POST" });
}

export function cancelJob(id: string) {
  return apiFetch<Job>(`/jobs/${id}/cancel`, { method: "POST" });
}
