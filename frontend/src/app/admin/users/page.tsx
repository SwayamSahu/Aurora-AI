"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/components/auth/auth-provider";
import { isAdmin } from "@/lib/admin/access";
import { listAdminUsers } from "@/lib/admin/users";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const PAGE_SIZE = 50;

export default function AdminUsersPage() {
  const { user, status } = useAuth();
  const [q, setQ] = React.useState("");
  const [role, setRole] = React.useState("all");
  const [activeFilter, setActiveFilter] = React.useState("all");
  const [offset, setOffset] = React.useState(0);

  const params = {
    q: q || undefined,
    role: role === "all" ? undefined : (role as "user" | "moderator" | "admin"),
    is_active: activeFilter === "all" ? undefined : activeFilter === "active",
    limit: PAGE_SIZE,
    offset,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["admin-users", params],
    queryFn: () => listAdminUsers(params),
    enabled: isAdmin(user),
  });

  if (status === "loading") {
    return (
      <div className="mx-auto w-full max-w-[900px] space-y-3 px-4 py-12">
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
    <div className="mx-auto w-full max-w-[900px] px-4 py-12 md:px-8">
      <h1 className="mb-2 text-3xl font-extrabold tracking-tight">Users</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Search all accounts, view aggregated activity, and manage role/status.
      </p>

      <div className="mb-6 flex flex-wrap gap-3">
        <Input
          placeholder="Search email or name…"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOffset(0);
          }}
          className="max-w-xs"
        />
        <Select
          value={role}
          onValueChange={(v) => {
            setRole(v);
            setOffset(0);
          }}
        >
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All roles</SelectItem>
            <SelectItem value="user">User</SelectItem>
            <SelectItem value="moderator">Moderator</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={activeFilter}
          onValueChange={(v) => {
            setActiveFilter(v);
            setOffset(0);
          }}
        >
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Active + suspended</SelectItem>
            <SelectItem value="active">Active only</SelectItem>
            <SelectItem value="suspended">Suspended only</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-[var(--mk-border)]">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--mk-border)] text-left text-xs uppercase tracking-wide text-muted-foreground">
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Joined</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {(data?.items ?? []).map((u) => (
                <tr
                  key={u.id}
                  className="border-b border-[var(--mk-border)] last:border-0"
                >
                  <td className="px-4 py-3">
                    <p className="font-medium">{u.full_name ?? "Unnamed"}</p>
                    <p className="text-xs text-muted-foreground">{u.email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={u.role === "user" ? "outline" : "default"}>
                      {u.role}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    {u.is_active ? (
                      <span className="text-xs text-mk-lavender">Active</span>
                    ) : (
                      <span className="text-xs text-destructive">Suspended</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-xs text-muted-foreground">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/admin/users/${u.id}`}>Manage</Link>
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && data.items.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No users match this filter.
            </p>
          ) : null}
        </div>
      )}

      {data ? (
        <div className="mt-4 flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Showing {offset + 1}–{Math.min(offset + PAGE_SIZE, data.total)} of{" "}
            {data.total}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={data.next_offset === null}
              onClick={() => {
                if (data.next_offset !== null) setOffset(data.next_offset);
              }}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
