import { apiFetch } from "@/lib/api/client";

export interface RevenuePoint {
  date: string;
  revenue_credits: number;
  gmv_credits: number;
  order_count: number;
}

export interface RevenueSummary {
  total_revenue_credits: number;
  total_gmv_credits: number;
  total_orders: number;
  total_refunded_credits: number;
  active_sellers: number;
  active_buyers: number;
  current_platform_fee: number;
  daily: RevenuePoint[];
}

export function getRevenueSummary(days = 30) {
  return apiFetch<RevenueSummary>(`/admin/analytics/revenue?days=${days}`);
}
