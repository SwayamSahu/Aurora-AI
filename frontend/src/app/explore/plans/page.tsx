"use client";

import { useRouter } from "next/navigation";
import { Check, Coins } from "lucide-react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";
import { usePlans, usePurchasePlan, useWallet } from "@/lib/marketplace/queries";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

function formatPrice(cents: number): string {
  if (cents === 0) return "Free";
  return `$${(cents / 100).toFixed(2)}`;
}

export default function PlansPage() {
  const router = useRouter();
  const { status } = useAuth();
  const { data: plans, isLoading } = usePlans();
  const { data: wallet } = useWallet();
  const purchase = usePurchasePlan();

  async function buy(planId: string) {
    if (status !== "authenticated") {
      router.push("/login");
      return;
    }
    try {
      const result = await purchase.mutateAsync(planId);
      toast.success(`+${result.credits_granted} credits added to your wallet.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't complete the purchase.");
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1000px] px-4 py-14 md:px-8">
      <div className="text-center">
        <p className="font-mono text-[12px] font-semibold uppercase tracking-[1.5px] text-mk-lavender">
          Plans
        </p>
        <h1 className="mt-2 text-4xl font-extrabold tracking-tight sm:text-5xl">
          Buy credits, sell more
        </h1>
        <p className="mt-3 text-muted-foreground">
          Credits are how you buy on the marketplace. Your plan also sets how
          many active listings you can sell at once.
        </p>
      </div>

      {isLoading ? (
        <div className="mt-10 grid gap-5 sm:grid-cols-3">
          <Skeleton className="h-80 w-full" />
          <Skeleton className="h-80 w-full" />
          <Skeleton className="h-80 w-full" />
        </div>
      ) : (
        <div className="mt-10 grid gap-5 sm:grid-cols-3">
          {(plans ?? []).map((plan) => {
            const isActive = wallet?.active_plan_id === plan.id;
            return (
              <div
                key={plan.id}
                className={cn(
                  "flex flex-col rounded-2xl border p-6",
                  isActive
                    ? "border-mk-lavender bg-mk-lavender/5 shadow-[0_0_30px_-10px_var(--mk-lavender)]"
                    : "border-[var(--mk-border)] bg-[var(--mk-surface-1)]",
                )}
              >
                <h2 className="text-xl font-bold">{plan.name}</h2>
                <p className="mt-2 text-3xl font-extrabold tracking-tight">
                  {formatPrice(plan.price_cents)}
                </p>

                <ul className="mt-6 flex-1 space-y-3 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <Coins className="size-4 text-mk-lavender" />
                    {plan.credits_granted.toLocaleString()} credits
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="size-4 text-mk-lavender" />
                    Up to {plan.listing_quota} active listing
                    {plan.listing_quota === 1 ? "" : "s"}
                  </li>
                </ul>

                <Button
                  className="mt-6"
                  variant={isActive ? "outline" : "default"}
                  disabled={purchase.isPending}
                  onClick={() => buy(plan.id)}
                >
                  {isActive ? "Buy again" : "Get " + plan.name}
                </Button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
