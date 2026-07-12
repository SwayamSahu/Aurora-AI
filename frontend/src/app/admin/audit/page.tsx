"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/components/auth/auth-provider";
import { isAdmin } from "@/lib/admin/access";
import { getAuditLog } from "@/lib/admin/audit";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const TARGET_TYPES = [
  "all",
  "blog_post",
  "blog_comment",
  "listing",
  "listing_comment",
  "plan",
  "wallet",
  "order",
];

export default function AdminAuditPage() {
  const { user, status } = useAuth();
  const [targetType, setTargetType] = React.useState("all");
  const [actionFilter, setActionFilter] = React.useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-audit", targetType, actionFilter],
    queryFn: () =>
      getAuditLog({
        target_type: targetType === "all" ? undefined : targetType,
        action: actionFilter || undefined,
      }),
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
      <h1 className="mb-2 text-3xl font-extrabold tracking-tight">Audit Log</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Append-only record of every privileged admin and moderator action.
      </p>

      <div className="mb-6 flex flex-wrap gap-3">
        <Select value={targetType} onValueChange={setTargetType}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {TARGET_TYPES.map((t) => (
              <SelectItem key={t} value={t}>
                {t === "all" ? "All targets" : t}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Input
          placeholder="Filter by action (e.g. wallet.adjust)"
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="max-w-xs"
        />
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-[var(--mk-border)]">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--mk-border)] text-left text-xs uppercase tracking-wide text-muted-foreground">
                <th className="px-4 py-3">When</th>
                <th className="px-4 py-3">Actor</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Target</th>
                <th className="px-4 py-3">Details</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items ?? []).map((a) => (
                <tr
                  key={a.id}
                  className="border-b border-[var(--mk-border)] last:border-0"
                >
                  <td className="whitespace-nowrap px-4 py-3 text-xs text-muted-foreground">
                    {new Date(a.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    {a.actor?.full_name ?? a.actor?.email ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-mk-lavender/15 px-2 py-0.5 font-mono text-xs text-mk-lavender">
                      {a.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {a.target_type}
                    {a.target_id ? `:${a.target_id.slice(0, 8)}` : ""}
                  </td>
                  <td className="max-w-xs truncate px-4 py-3 font-mono text-xs text-muted-foreground">
                    {JSON.stringify(a.action_metadata)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && data.items.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No audit entries match this filter.
            </p>
          ) : null}
        </div>
      )}
    </div>
  );
}
