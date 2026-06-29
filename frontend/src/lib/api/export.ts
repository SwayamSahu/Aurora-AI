import { apiFetch } from "@/lib/api/client";
import type { Job } from "@/lib/api/jobs";

export interface ExportOptions {
  width?: number;
  height?: number;
  fps?: number;
  crf?: number;
  fade_duration?: number;
}

export function startExport(projectId: string, options: ExportOptions = {}) {
  return apiFetch<Job>(`/projects/${projectId}/export`, {
    method: "POST",
    json: {
      width: options.width ?? 1280,
      height: options.height ?? 720,
      fps: options.fps ?? 24,
      crf: options.crf ?? 23,
      fade_duration: options.fade_duration ?? 0.5,
    },
  });
}
