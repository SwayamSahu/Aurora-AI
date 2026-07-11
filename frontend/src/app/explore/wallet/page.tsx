"use client";

import Link from "next/link";
import { Coins, ArrowDownLeft, ArrowUpRight } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { useWallet, useWalletTransactions } from "@/lib/marketplace/queries";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

function formatType(type: string): string {
  return type
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export default function WalletPage() {
  const { status } = useAuth();
  const { data: wallet, isLoading: walletLoading } = useWallet();
  const { data: history, isLoading: historyLoading } = useWalletTransactions();

  if (status === "loading" || walletLoading) {
    return (
      <div className="mx-auto w-full max-w-[720px] space-y-4 px-4 py-12">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (status !== "authenticated") {
    return (
      <p className="py-24 text-center text-muted-foreground">
        <a href="/login" className="text-mk-lavender hover:underline">
          Sign in
        </a>{" "}
        to see your wallet.
      </p>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[720px] px-4 py-12 md:px-8">
      <h1 className="font-mono text-[12px] font-semibold uppercase tracking-[1.5px] text-mk-lavender">
        Wallet
      </h1>

      <div className="mt-4 rounded-2xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-4xl font-extrabold tracking-tight text-mk-lavender">
              <Coins className="size-8" />
              {(wallet?.balance_credits ?? 0).toLocaleString()}
            </div>
            <p className="mt-1 text-[12px] font-semibold uppercase tracking-[1.5px] text-muted-foreground">
              Credits available
            </p>
          </div>
          <Button asChild>
            <Link href="/explore/plans">Buy credits</Link>
          </Button>
        </div>

        <p className="mt-4 text-[13px] text-muted-foreground">
          Listing quota: <strong>{wallet?.listing_quota ?? 0}</strong> active
          listing{wallet?.listing_quota === 1 ? "" : "s"}
        </p>
      </div>

      <h2 className="mt-10 mb-3 text-lg font-bold">Activity</h2>
      {historyLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
          <Skeleton className="h-14 w-full" />
        </div>
      ) : history && history.items.length > 0 ? (
        <div className="space-y-2">
          {history.items.map((tx) => (
            <div
              key={tx.id}
              className="flex items-center justify-between gap-4 rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] px-4 py-3"
            >
              <div className="flex items-center gap-3">
                {tx.amount >= 0 ? (
                  <ArrowDownLeft className="size-4 text-emerald-500" />
                ) : (
                  <ArrowUpRight className="size-4 text-mk-coral" />
                )}
                <div>
                  <p className="text-sm font-medium">{formatType(tx.type)}</p>
                  {tx.note ? (
                    <p className="text-xs text-muted-foreground">{tx.note}</p>
                  ) : null}
                </div>
              </div>
              <div className="text-right">
                <p
                  className={
                    tx.amount >= 0
                      ? "font-mono text-sm font-semibold text-emerald-500"
                      : "font-mono text-sm font-semibold text-mk-coral"
                  }
                >
                  {tx.amount >= 0 ? "+" : ""}
                  {tx.amount}
                </p>
                <p className="text-xs text-muted-foreground">
                  bal. {tx.balance_after}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="py-8 text-center text-sm text-muted-foreground">
          No activity yet.
        </p>
      )}
    </div>
  );
}
