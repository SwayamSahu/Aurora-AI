import { apiFetch } from "@/lib/api/client";
import type { BlogPostSummary } from "@/lib/blog/api";
import type { MarketplaceListing } from "@/lib/marketplace/types";

export type AdminRole = "user" | "moderator" | "admin";

export interface AdminUserRead {
  id: string;
  email: string;
  full_name: string | null;
  role: AdminRole;
  is_active: boolean;
  erased_at: string | null;
  created_at: string;
}

export interface AdminUserListResponse {
  items: AdminUserRead[];
  total: number;
  next_offset: number | null;
}

export interface AdminUserDetail extends AdminUserRead {
  wallet_balance: number;
  listing_quota: number;
  post_count: number;
  listing_count: number;
  order_count: number;
  sales_count: number;
  recent_posts: BlogPostSummary[];
  recent_listings: MarketplaceListing[];
}

export function listAdminUsers(params: {
  q?: string;
  role?: AdminRole;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}) {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.role) qs.set("role", params.role);
  if (params.is_active !== undefined) qs.set("is_active", String(params.is_active));
  qs.set("limit", String(params.limit ?? 50));
  qs.set("offset", String(params.offset ?? 0));
  return apiFetch<AdminUserListResponse>(`/admin/users?${qs.toString()}`);
}

export function getAdminUserDetail(userId: string) {
  return apiFetch<AdminUserDetail>(`/admin/users/${userId}`);
}

export function updateAdminUser(
  userId: string,
  input: { role?: AdminRole; is_active?: boolean },
) {
  return apiFetch<AdminUserDetail>(`/admin/users/${userId}`, {
    method: "PATCH",
    json: input,
  });
}

export function eraseAdminUser(userId: string) {
  return apiFetch<AdminUserDetail>(`/admin/users/${userId}/erase`, {
    method: "POST",
  });
}
