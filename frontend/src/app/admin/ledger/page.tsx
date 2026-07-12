"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/components/auth/auth-provider";
import { isAdmin } from "@/lib/admin/access";
import { searchLedger, type LedgerTxType } from "@/lib/admin/ledger";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const TX_TYPES: LedgerTxType[] = [
  "topup",
  "plan_purchase",
  "purchase_spend",
  "sale_earning",
  "platform_fee",
  "refund",
  "admin_adjust",
];

const PAGE_SIZE = 50;

export default function AdminLedgerPage() {
  const { user, status } = useAuth();
  const [q, setQ] = React.useState("");
  const [type, setType] = React.useState("all");
  const [offset, setOffset] = React.useState(0);

  const params = {
    q: q || undefined,
    type: type === "all" ? undefined : (type as LedgerTxType),
    limit: PAGE_SIZE,
    offset,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["admin-ledger", params],
    queryFn: () => searchLedger(params),
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
      <h1 className="mb-2 text-3xl font-extrabold tracking-tight">
        Credit Ledger
      </h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Search every wallet&apos;s transaction history in one place.
      </p>

      <div className="mb-6 flex flex-wrap gap-3">
        <Input
          placeholder="Search by user email or name…"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOffset(0);
          }}
          className="max-w-xs"
        />
        <Select
          value={type}
          onValueChange={(v) => {
            setType(v);
            setOffset(0);
          }}
        >
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            {TX_TYPES.map((t) => (
              <SelectItem key={t} value={t}>
                {t}
              </SelectItem>
            ))}
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
                <th className="px-4 py-3">When</th>
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Amount</th>
                <th className="px-4 py-3">Balance after</th>
                <th className="px-4 py-3">Note</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items ?? []).map((tx) => (
                <tr
                  key={tx.id}
                  className="border-b border-[var(--mk-border)] last:border-0"
                >
                  <td className="whitespace-nowrap px-4 py-3 text-xs text-muted-foreground">
                    {new Date(tx.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-medium">{tx.user.full_name ?? "Unnamed"}</p>
                    <p className="text-xs text-muted-foreground">{tx.user.email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-mk-lavender/15 px-2 py-0.5 font-mono text-xs text-mk-lavender">
                      {tx.type}
                    </span>
                  </td>
                  <td
                    className={`px-4 py-3 font-mono ${
                      tx.amount < 0 ? "text-destructive" : "text-mk-lavender"
                    }`}
                  >
                    {tx.amount > 0 ? "+" : ""}
                    {tx.amount}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {tx.balance_after}
                  </td>
                  <td className="max-w-xs truncate px-4 py-3 text-xs text-muted-foreground">
                    {tx.note ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && data.items.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No transactions match this filter.
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
