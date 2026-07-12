"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/components/auth/auth-provider";
import { isAdmin } from "@/lib/admin/access";
import { getRevenueSummary } from "@/lib/admin/analytics";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

function StatCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-2xl font-bold">{value}</p>
    </div>
  );
}

function RevenueChart({
  daily,
}: {
  daily: { date: string; revenue_credits: number; gmv_credits: number }[];
}) {
  if (daily.length === 0) {
    return (
      <p className="py-12 text-center text-sm text-muted-foreground">
        No sales in this window yet.
      </p>
    );
  }
  const max = Math.max(...daily.map((d) => d.gmv_credits), 1);
  return (
    <div className="flex h-48 items-end gap-1 overflow-x-auto">
      {daily.map((d) => (
        <div
          key={d.date}
          className="group relative flex h-full min-w-[10px] flex-1 flex-col items-center justify-end"
          title={`${d.date}: ${d.gmv_credits} GMV, ${d.revenue_credits} revenue`}
        >
          <div
            className="w-full rounded-t bg-[var(--mk-border-strong)]"
            style={{ height: `${(d.gmv_credits / max) * 100}%` }}
          />
          <div
            className="w-full rounded-t bg-mk-lavender"
            style={{
              height: `${(d.revenue_credits / max) * 100}%`,
              marginTop: `-${(d.revenue_credits / max) * 100}%`,
            }}
          />
        </div>
      ))}
    </div>
  );
}

export default function AdminRevenuePage() {
  const { user, status } = useAuth();
  const [days, setDays] = React.useState("30");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-revenue", days],
    queryFn: () => getRevenueSummary(Number(days)),
    enabled: isAdmin(user),
  });

  if (status === "loading") {
    return (
      <div className="mx-auto w-full max-w-[1000px] space-y-3 px-4 py-12">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-64 w-full" />
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
    <div className="mx-auto w-full max-w-[1000px] px-4 py-12 md:px-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Revenue</h1>
          <p className="text-sm text-muted-foreground">
            Platform revenue and marketplace activity.
          </p>
        </div>
        <Select value={days} onValueChange={setDays}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7">Last 7 days</SelectItem>
            <SelectItem value="30">Last 30 days</SelectItem>
            <SelectItem value="90">Last 90 days</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading || !data ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <StatCard
              label="Total revenue"
              value={`${data.total_revenue_credits} cr`}
            />
            <StatCard label="Total GMV" value={`${data.total_gmv_credits} cr`} />
            <StatCard label="Orders" value={data.total_orders} />
            <StatCard
              label="Refunded"
              value={`${data.total_refunded_credits} cr`}
            />
            <StatCard label="Active sellers" value={data.active_sellers} />
            <StatCard label="Active buyers" value={data.active_buyers} />
          </div>

          <p className="mt-6 text-sm text-muted-foreground">
            Current platform fee:{" "}
            <strong>{Math.round(data.current_platform_fee * 100)}%</strong>
          </p>

          <div className="mt-4 rounded-xl border border-[var(--mk-border)] p-4">
            <div className="mb-3 flex items-center gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <span className="inline-block size-2.5 rounded-sm bg-[var(--mk-border-strong)]" />
                GMV
              </span>
              <span className="flex items-center gap-1.5">
                <span className="inline-block size-2.5 rounded-sm bg-mk-lavender" />
                Platform revenue
              </span>
            </div>
            <RevenueChart daily={data.daily} />
          </div>
        </>
      )}
    </div>
  );
}
