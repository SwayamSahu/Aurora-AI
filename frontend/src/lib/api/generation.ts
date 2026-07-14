import { apiFetch } from "@/lib/api/client";

/** A selectable video-generation model. Mirrors the backend model catalog
 * (`GET /generation/models`). Drives the Studio model picker and its
 * per-model duration/resolution constraints. */
export interface VideoModelSpec {
  id: string;
  label: string;
  provider: string;
  /** "local" (own GPU) or "api" (hosted third-party model). */
  kind: string;
  /** Resolution tier label, e.g. "720p", "1080p", "4K". */
  resolution: string;
  max_width: number;
  max_height: number;
  min_duration: number;
  max_duration: number;
  default_duration: number;
  supports_i2v: boolean;
  badges: string[];
  /** Credits debited from the user's wallet per generation with this model. */
  credit_cost: number;
}

export function listVideoModels() {
  return apiFetch<VideoModelSpec[]>("/generation/models");
}
