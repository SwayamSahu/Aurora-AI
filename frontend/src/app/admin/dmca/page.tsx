"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { isModerator } from "@/lib/admin/access";
import {
  listAdminDmcaRequests,
  resolveDmcaRequest,
  type DmcaRequestRead,
} from "@/lib/dmca";
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

const TARGET_LABELS: Record<string, string> = {
  blog_post: "Blog post",
  blog_comment: "Blog comment",
  listing: "Listing",
  listing_comment: "Listing comment",
};

function DmcaRow({ request }: { request: DmcaRequestRead }) {
  const qc = useQueryClient();
  const [note, setNote] = React.useState("");
  const resolve = useMutation({
    mutationFn: (status: "content_removed" | "rejected") =>
      resolveDmcaRequest(request.id, { status, resolution_note: note.trim() || undefined }),
    onSuccess: () => {
      toast.success("Request updated.");
      qc.invalidateQueries({ queryKey: ["admin-dmca"] });
    },
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed."),
  });

  return (
    <div className="rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{TARGET_LABELS[request.target_type]}</Badge>
            {request.status !== "open" ? (
              <Badge variant={request.status === "content_removed" ? "destructive" : "outline"}>
                {request.status}
              </Badge>
            ) : null}
          </div>
          <p className="mt-2 text-sm font-medium">
            {request.target_preview ? request.target_preview.title : "(content deleted)"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {request.work_description}
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            {request.claimant_name} ({request.claimant_email}) ·{" "}
            {new Date(request.created_at).toLocaleString()}
          </p>
          {request.resolution_note ? (
            <p className="mt-2 text-xs text-muted-foreground">
              Resolution: {request.resolution_note}
            </p>
          ) : null}
        </div>

        {request.status === "open" ? (
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
                onClick={() => resolve.mutate("rejected")}
                loading={resolve.isPending}
              >
                Reject
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => resolve.mutate("content_removed")}
                loading={resolve.isPending}
              >
                Remove content
              </Button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function AdminDmcaPage() {
  const { user, status } = useAuth();
  const [statusFilter, setStatusFilter] = React.useState("open");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-dmca", statusFilter],
    queryFn: () =>
      listAdminDmcaRequests({
        status: statusFilter === "all" ? undefined : statusFilter,
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
      <h1 className="mb-2 text-3xl font-extrabold tracking-tight">
        DMCA Takedowns
      </h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Formal copyright takedown notices awaiting review.
      </p>

      <div className="mb-6">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="open">Open</SelectItem>
            <SelectItem value="content_removed">Content removed</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
            <SelectItem value="all">All</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <div className="space-y-3">
          {(data?.items ?? []).map((r) => (
            <DmcaRow key={r.id} request={r} />
          ))}
          {data && data.items.length === 0 ? (
            <p className="py-16 text-center text-sm text-muted-foreground">
              No requests match this filter.
            </p>
          ) : null}
        </div>
      )}
    </div>
  );
}
