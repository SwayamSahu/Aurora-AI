import { apiFetch } from "@/lib/api/client";

export interface HealthCheck {
  ok: boolean;
  latency_ms?: number;
  error?: string;
}

export interface SystemHealth {
  database: HealthCheck;
  redis: HealthCheck;
  storage: HealthCheck;
  counts: {
    total_users: number;
    active_listings: number;
    published_posts: number;
    total_orders: number;
    open_reports: number;
    failed_jobs: number;
    total_jobs: number;
  };
  generator_backend: string;
  environment: string;
}

export function getSystemHealth() {
  return apiFetch<SystemHealth>("/admin/system/health");
}
