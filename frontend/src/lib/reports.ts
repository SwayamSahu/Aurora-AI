import { apiFetch } from "@/lib/api/client";

export type ReportTargetType =
  | "blog_post"
  | "blog_comment"
  | "listing"
  | "listing_comment";

export type ReportReason = "spam" | "abuse" | "inappropriate" | "copyright" | "other";

export interface ReportReporter {
  id: string;
  email: string;
  full_name: string | null;
}

export interface ReportTargetPreview {
  title: string;
  deleted: boolean;
}

export interface ReportRead {
  id: string;
  reporter: ReportReporter | null;
  target_type: ReportTargetType;
  target_id: string;
  target_preview: ReportTargetPreview | null;
  reason: ReportReason;
  note: string | null;
  status: "open" | "resolved" | "dismissed";
  resolution_note: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface ReportListResponse {
  items: ReportRead[];
  total: number;
  next_offset: number | null;
}

export function createReport(input: {
  target_type: ReportTargetType;
  target_id: string;
  reason: ReportReason;
  note?: string;
}) {
  return apiFetch<ReportRead>("/reports", { method: "POST", json: input });
}

export function listAdminReports(params: {
  status?: string;
  target_type?: string;
  limit?: number;
  offset?: number;
}) {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.target_type) qs.set("target_type", params.target_type);
  qs.set("limit", String(params.limit ?? 50));
  qs.set("offset", String(params.offset ?? 0));
  return apiFetch<ReportListResponse>(`/admin/reports?${qs.toString()}`);
}

export function resolveReport(
  reportId: string,
  input: { status: "resolved" | "dismissed"; resolution_note?: string },
) {
  return apiFetch<ReportRead>(`/admin/reports/${reportId}`, {
    method: "PATCH",
    json: input,
  });
}
