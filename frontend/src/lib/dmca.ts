import { apiFetch } from "@/lib/api/client";

export type DmcaTargetType = "blog_post" | "blog_comment" | "listing" | "listing_comment";

export interface DmcaResolvedBy {
  id: string;
  email: string;
  full_name: string | null;
}

export interface DmcaTargetPreview {
  title: string;
  deleted: boolean;
}

export interface DmcaRequestRead {
  id: string;
  claimant_name: string;
  claimant_email: string;
  target_type: DmcaTargetType;
  target_id: string;
  target_preview: DmcaTargetPreview | null;
  work_description: string;
  status: "open" | "content_removed" | "rejected";
  resolution_note: string | null;
  resolved_by: DmcaResolvedBy | null;
  created_at: string;
}

export interface DmcaListResponse {
  items: DmcaRequestRead[];
  total: number;
  next_offset: number | null;
}

export function submitDmcaRequest(input: {
  claimant_name: string;
  claimant_email: string;
  target_type: DmcaTargetType;
  target_id: string;
  work_description: string;
  good_faith_statement: boolean;
  signature: string;
}) {
  return apiFetch<DmcaRequestRead>("/dmca", { method: "POST", json: input, auth: false });
}

export function listAdminDmcaRequests(params: { status?: string; limit?: number; offset?: number }) {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  qs.set("limit", String(params.limit ?? 50));
  qs.set("offset", String(params.offset ?? 0));
  return apiFetch<DmcaListResponse>(`/admin/dmca?${qs.toString()}`);
}

export function resolveDmcaRequest(
  id: string,
  input: { status: "content_removed" | "rejected"; resolution_note?: string },
) {
  return apiFetch<DmcaRequestRead>(`/admin/dmca/${id}`, { method: "PATCH", json: input });
}
