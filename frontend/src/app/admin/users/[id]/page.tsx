"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { isAdmin } from "@/lib/admin/access";
import { getAdminUserDetail, updateAdminUser, type AdminRole } from "@/lib/admin/users";
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
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

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

export default function AdminUserDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user: me, status } = useAuth();
  const qc = useQueryClient();
  const [pendingRole, setPendingRole] = React.useState<AdminRole | null>(null);

  const { data: detail, isLoading } = useQuery({
    queryKey: ["admin-user-detail", params.id],
    queryFn: () => getAdminUserDetail(params.id),
    enabled: isAdmin(me) && !!params.id,
  });

  async function applyRole(role: AdminRole) {
    try {
      await updateAdminUser(params.id, { role });
      toast.success(`Role updated to ${role}.`);
      qc.invalidateQueries({ queryKey: ["admin-user-detail", params.id] });
      qc.invalidateQueries({ queryKey: ["admin-users"] });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update role.");
    } finally {
      setPendingRole(null);
    }
  }

  async function toggleActive() {
    if (!detail) return;
    try {
      await updateAdminUser(params.id, { is_active: !detail.is_active });
      toast.success(detail.is_active ? "User suspended." : "User reactivated.");
      qc.invalidateQueries({ queryKey: ["admin-user-detail", params.id] });
      qc.invalidateQueries({ queryKey: ["admin-users"] });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update status.");
    }
  }

  if (status === "loading" || (isAdmin(me) && isLoading)) {
    return (
      <div className="mx-auto w-full max-w-[800px] space-y-3 px-4 py-12">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (status !== "authenticated" || !isAdmin(me)) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        Admin access required.
      </p>
    );
  }

  if (!detail) {
    return (
      <p className="py-24 text-center text-muted-foreground">User not found.</p>
    );
  }

  const isSelf = detail.id === me?.id;

  return (
    <div className="mx-auto w-full max-w-[800px] px-4 py-12 md:px-8">
      <Button variant="ghost" size="sm" onClick={() => router.push("/admin/users")}>
        ← Back to users
      </Button>

      <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">
            {detail.full_name ?? "Unnamed"}
          </h1>
          <p className="text-sm text-muted-foreground">{detail.email}</p>
          <div className="mt-2 flex items-center gap-2">
            <Badge variant={detail.role === "user" ? "outline" : "default"}>
              {detail.role}
            </Badge>
            {detail.is_active ? (
              <Badge variant="outline" className="text-mk-lavender">
                Active
              </Badge>
            ) : (
              <Badge variant="destructive">Suspended</Badge>
            )}
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          <Select
            value={detail.role}
            onValueChange={(v) => setPendingRole(v as AdminRole)}
            disabled={isSelf}
          >
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="user">User</SelectItem>
              <SelectItem value="moderator">Moderator</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
            </SelectContent>
          </Select>
          {isSelf ? (
            <p className="text-xs text-muted-foreground">
              You can&apos;t change your own role or status.
            </p>
          ) : (
            <Button
              variant="outline"
              size="sm"
              className={
                detail.is_active
                  ? "text-destructive hover:text-destructive"
                  : undefined
              }
              onClick={toggleActive}
            >
              {detail.is_active ? "Suspend account" : "Reactivate account"}
            </Button>
          )}
        </div>
      </div>

      <Dialog open={pendingRole !== null} onOpenChange={(open) => !open && setPendingRole(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change role to {pendingRole}?</DialogTitle>
            <DialogDescription>
              This changes what {detail.email} can access across the platform
              immediately.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose asChild>
              <Button variant="outline">Cancel</Button>
            </DialogClose>
            <Button onClick={() => pendingRole && applyRole(pendingRole)}>
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Wallet balance" value={detail.wallet_balance} />
        <StatCard label="Listing quota" value={detail.listing_quota} />
        <StatCard label="Posts" value={detail.post_count} />
        <StatCard label="Listings" value={detail.listing_count} />
        <StatCard label="Orders" value={detail.order_count} />
        <StatCard label="Sales" value={detail.sales_count} />
      </div>

      <div className="mt-8">
        <h2 className="mb-3 text-lg font-semibold">Recent posts</h2>
        {detail.recent_posts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No blog posts.</p>
        ) : (
          <ul className="space-y-2">
            {detail.recent_posts.map((p) => (
              <li
                key={p.id}
                className="rounded-lg border border-[var(--mk-border)] p-3 text-sm"
              >
                <Link href={`/blog/${p.slug}`} className="hover:underline">
                  {p.title}
                </Link>
                <span className="ml-2 text-xs text-muted-foreground">
                  {p.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-8">
        <h2 className="mb-3 text-lg font-semibold">Recent listings</h2>
        {detail.recent_listings.length === 0 ? (
          <p className="text-sm text-muted-foreground">No marketplace listings.</p>
        ) : (
          <ul className="space-y-2">
            {detail.recent_listings.map((l) => (
              <li
                key={l.id}
                className="rounded-lg border border-[var(--mk-border)] p-3 text-sm"
              >
                <Link href={`/explore/me/${l.id}/edit`} className="hover:underline">
                  {l.title}
                </Link>
                <span className="ml-2 text-xs text-muted-foreground">
                  {l.status} · {l.price_credits} credits
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
