import { apiFetch } from "@/lib/api/client";

export interface AdminModel {
  id: string;
  label: string;
  provider: string;
  kind: string;
  resolution: string;
  max_width: number;
  max_height: number;
  min_duration: number;
  max_duration: number;
  default_duration: number;
  supports_i2v: boolean;
  badges: string[];
  credit_cost: number;
  enabled: boolean;
  is_overridden: boolean;
}

export function listAdminModels() {
  return apiFetch<AdminModel[]>("/admin/models");
}

export function updateAdminModel(
  modelId: string,
  patch: { enabled?: boolean; credit_cost?: number },
) {
  return apiFetch<AdminModel>(`/admin/models/${modelId}`, {
    method: "PATCH",
    json: patch,
  });
}

export function clearAdminModelOverride(modelId: string) {
  return apiFetch<AdminModel>(`/admin/models/${modelId}/override`, {
    method: "DELETE",
  });
}
