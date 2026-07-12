import { apiFetch } from "@/lib/api/client";

export type LedgerTxType =
  | "topup"
  | "plan_purchase"
  | "purchase_spend"
  | "sale_earning"
  | "platform_fee"
  | "refund"
  | "admin_adjust";

export interface LedgerEntryUser {
  id: string;
  email: string;
  full_name: string | null;
}

export interface LedgerEntryRead {
  id: string;
  wallet_id: string;
  user: LedgerEntryUser;
  type: LedgerTxType;
  amount: number;
  balance_after: number;
  note: string | null;
  related_order_id: string | null;
  created_at: string;
}

export interface LedgerSearchResponse {
  items: LedgerEntryRead[];
  total: number;
  next_offset: number | null;
}

export function searchLedger(params: {
  q?: string;
  type?: LedgerTxType;
  user_id?: string;
  limit?: number;
  offset?: number;
}) {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.type) qs.set("type", params.type);
  if (params.user_id) qs.set("user_id", params.user_id);
  qs.set("limit", String(params.limit ?? 50));
  qs.set("offset", String(params.offset ?? 0));
  return apiFetch<LedgerSearchResponse>(`/admin/ledger?${qs.toString()}`);
}
