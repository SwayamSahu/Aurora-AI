import { apiFetch } from "@/lib/api/client";

export interface AuditActor {
  id: string;
  full_name: string | null;
  email: string;
}

export interface AdminAction {
  id: string;
  actor: AuditActor | null;
  action: string;
  target_type: string;
  target_id: string | null;
  action_metadata: Record<string, unknown>;
  created_at: string;
}

export interface AuditLogResponse {
  items: AdminAction[];
  total: number;
  next_offset: number | null;
}

export function getAuditLog(params: {
  action?: string;
  target_type?: string;
  actor_id?: string;
  limit?: number;
  offset?: number;
}) {
  const qs = new URLSearchParams();
  if (params.action) qs.set("action", params.action);
  if (params.target_type) qs.set("target_type", params.target_type);
  if (params.actor_id) qs.set("actor_id", params.actor_id);
  qs.set("limit", String(params.limit ?? 50));
  qs.set("offset", String(params.offset ?? 0));
  return apiFetch<AuditLogResponse>(`/admin/audit?${qs.toString()}`);
}
