"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { isModerator } from "@/lib/admin/access";
import { listAdminReports, resolveReport, type ReportRead } from "@/lib/reports";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const TARGET_TYPES = ["blog_post", "blog_comment", "listing", "listing_comment"];

const TARGET_LABELS: Record<string, string> = {
  blog_post: "Blog post",
  blog_comment: "Blog comment",
  listing: "Listing",
  listing_comment: "Listing comment",
};

function ReportRow({ report }: { report: ReportRead }) {
  const qc = useQueryClient();
  const [note, setNote] = React.useState("");
  const resolve = useMutation({
    mutationFn: (status: "resolved" | "dismissed") =>
      resolveReport(report.id, { status, resolution_note: note.trim() || undefined }),
    onSuccess: () => {
      toast.success("Report updated.");
      qc.invalidateQueries({ queryKey: ["admin-reports"] });
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Failed.");
    },
  });

  return (
    <div className="rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{TARGET_LABELS[report.target_type]}</Badge>
            <Badge variant={report.reason === "other" ? "outline" : "secondary"}>
              {report.reason}
            </Badge>
            {report.status !== "open" ? (
              <Badge variant={report.status === "resolved" ? "success" : "outline"}>
                {report.status}
              </Badge>
            ) : null}
          </div>
          <p className="mt-2 text-sm font-medium">
            {report.target_preview ? report.target_preview.title : "(content deleted)"}
          </p>
          {report.note ? (
            <p className="mt-1 text-sm text-muted-foreground">
              &ldquo;{report.note}&rdquo;
            </p>
          ) : null}
          <p className="mt-2 text-xs text-muted-foreground">
            Reported by{" "}
            {report.reporter
              ? (report.reporter.full_name ?? report.reporter.email)
              : "a deleted user"}{" "}
            · {new Date(report.created_at).toLocaleString()}
          </p>
          {report.resolution_note ? (
            <p className="mt-2 text-xs text-muted-foreground">
              Resolution: {report.resolution_note}
            </p>
          ) : null}
        </div>

        {report.status === "open" ? (
          <div className="flex shrink-0 flex-col items-end gap-2">
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Resolution note (optional)"
              className="h-9 w-56 rounded-lg border border-[var(--mk-border)] bg-[var(--mk-surface-2)] px-3 text-xs placeholder:text-muted-foreground focus:border-[var(--mk-border-strong)] focus:outline-none"
            />
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => resolve.mutate("dismissed")}
                loading={resolve.isPending}
              >
                Dismiss
              </Button>
              <Button
                size="sm"
                onClick={() => resolve.mutate("resolved")}
                loading={resolve.isPending}
              >
                Resolve
              </Button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function AdminReportsPage() {
  const { user, status } = useAuth();
  const [statusFilter, setStatusFilter] = React.useState("open");
  const [targetFilter, setTargetFilter] = React.useState("all");

  const { data, isLoading } = useQuery({
    queryKey: [
      "admin-reports",
      { status: statusFilter, target_type: targetFilter },
    ],
    queryFn: () =>
      listAdminReports({
        status: statusFilter === "all" ? undefined : statusFilter,
        target_type: targetFilter === "all" ? undefined : targetFilter,
      }),
    enabled: isModerator(user),
  });

  if (status === "loading") {
    return (
      <div className="mx-auto w-full max-w-[900px] space-y-3 px-4 py-12">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (status !== "authenticated" || !isModerator(user)) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        Admin access required.
      </p>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[900px] px-4 py-12 md:px-8">
      <h1 className="mb-2 text-3xl font-extrabold tracking-tight">Reports</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        User-flagged posts, comments, and listings awaiting review.
      </p>

      <div className="mb-6 flex flex-wrap gap-3">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="resolved">Resolved</SelectItem>
            <SelectItem value="dismissed">Dismissed</SelectItem>
            <SelectItem value="all">All</SelectItem>
          </SelectContent>
        </Select>
        <Select value={targetFilter} onValueChange={setTargetFilter}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All content types</SelectItem>
            {TARGET_TYPES.map((t) => (
              <SelectItem key={t} value={t}>
                {TARGET_LABELS[t]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <div className="space-y-3">
          {(data?.items ?? []).map((r) => (
            <ReportRow key={r.id} report={r} />
          ))}
          {data && data.items.length === 0 ? (
            <p className="py-16 text-center text-sm text-muted-foreground">
              No reports match this filter.
            </p>
          ) : null}
        </div>
      )}
    </div>
  );
}
