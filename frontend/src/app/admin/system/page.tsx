"use client";

import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, XCircle } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { isAdmin } from "@/lib/admin/access";
import { getSystemHealth, type HealthCheck } from "@/lib/admin/system";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

function ServiceCard({ label, check }: { label: string; check: HealthCheck }) {
  return (
    <div className="rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold">{label}</p>
        {check.ok ? (
          <CheckCircle2 className="size-5 text-mk-lavender" />
        ) : (
          <XCircle className="size-5 text-destructive" />
        )}
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        {check.ok
          ? `${check.latency_ms ?? "—"} ms`
          : (check.error ?? "Unreachable")}
      </p>
    </div>
  );
}

function CountCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-2xl font-bold">{value}</p>
    </div>
  );
}

export default function AdminSystemPage() {
  const { user, status } = useAuth();

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["admin-system-health"],
    queryFn: getSystemHealth,
    enabled: isAdmin(user),
    refetchInterval: 30_000,
  });

  if (status === "loading") {
    return (
      <div className="mx-auto w-full max-w-[900px] space-y-3 px-4 py-12">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (status !== "authenticated" || !isAdmin(user)) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        Admin access required.
      </p>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[900px] px-4 py-12 md:px-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">
            System Health
          </h1>
          <p className="text-sm text-muted-foreground">
            Live status of core infrastructure and platform-scale counts.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          loading={isFetching}
        >
          Refresh
        </Button>
      </div>

      {isLoading || !data ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <ServiceCard label="Database" check={data.database} />
            <ServiceCard label="Redis" check={data.redis} />
            <ServiceCard label="Storage" check={data.storage} />
          </div>

          <p className="mt-6 text-sm text-muted-foreground">
            Generator backend: <strong>{data.generator_backend}</strong> ·
            Environment: <strong>{data.environment}</strong>
          </p>

          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <CountCard label="Users" value={data.counts.total_users} />
            <CountCard
              label="Active listings"
              value={data.counts.active_listings}
            />
            <CountCard
              label="Published posts"
              value={data.counts.published_posts}
            />
            <CountCard label="Orders" value={data.counts.total_orders} />
            <CountCard label="Open reports" value={data.counts.open_reports} />
            <CountCard label="Failed jobs" value={data.counts.failed_jobs} />
            <CountCard label="Total jobs" value={data.counts.total_jobs} />
          </div>
        </>
      )}
    </div>
  );
}
