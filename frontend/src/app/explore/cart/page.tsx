"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Trash2, Coins, ArrowRight } from "lucide-react";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { absoluteMediaUrl } from "@/lib/marketplace/api";
import {
  useCart,
  useCheckout,
  useRemoveFromCart,
  useWallet,
} from "@/lib/marketplace/queries";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export default function CartPage() {
  const router = useRouter();
  const { status } = useAuth();
  const { data: cart, isLoading } = useCart();
  const { data: wallet } = useWallet();
  const remove = useRemoveFromCart();
  const checkout = useCheckout();

  async function onCheckout() {
    try {
      const order = await checkout.mutateAsync();
      toast.success(`Purchased for ${order.total_credits} credits.`);
      router.push("/explore/me");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Checkout failed.");
    }
  }

  if (status === "loading" || isLoading) {
    return (
      <div className="mx-auto w-full max-w-[720px] space-y-3 px-4 py-12">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (status !== "authenticated") {
    return (
      <p className="py-24 text-center text-muted-foreground">
        <a href="/login" className="text-mk-lavender hover:underline">
          Sign in
        </a>{" "}
        to see your cart.
      </p>
    );
  }

  const items = cart?.items ?? [];
  const insufficientCredits = (wallet?.balance_credits ?? 0) < (cart?.total_credits ?? 0);

  return (
    <div className="mx-auto w-full max-w-[720px] px-4 py-12 md:px-8">
      <h1 className="text-3xl font-extrabold tracking-tight">Cart</h1>

      {items.length === 0 ? (
        <p className="py-16 text-center text-muted-foreground">
          Your cart is empty.{" "}
          <Link href="/explore" className="text-mk-lavender hover:underline">
            Browse the marketplace
          </Link>
          .
        </p>
      ) : (
        <>
          <div className="mt-6 space-y-3">
            {items.map((item) => (
              <div
                key={item.id}
                className="flex items-center gap-4 rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4"
              >
                <Link
                  href={`/explore/p/${item.listing.id}`}
                  className="size-16 shrink-0 overflow-hidden rounded-lg bg-[var(--mk-surface-2)]"
                >
                  {item.listing.cover_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={absoluteMediaUrl(item.listing.cover_url)}
                      alt=""
                      className="size-full object-cover"
                    />
                  ) : null}
                </Link>

                <div className="min-w-0 flex-1">
                  <Link
                    href={`/explore/p/${item.listing.id}`}
                    className="truncate font-semibold hover:underline"
                  >
                    {item.listing.title}
                  </Link>
                  <p className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
                    <Coins className="size-3.5" /> {item.listing.price_credits} credits
                  </p>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  className="text-destructive hover:text-destructive"
                  disabled={remove.isPending}
                  onClick={() => remove.mutate(item.id)}
                >
                  <Trash2 className="size-4" />
                </Button>
              </div>
            ))}
          </div>

          <div className="mt-6 flex items-center justify-between border-t border-[var(--mk-border)] pt-6">
            <div>
              <p className="text-sm text-muted-foreground">Total</p>
              <p className="flex items-center gap-1.5 text-2xl font-extrabold">
                <Coins className="size-5 text-mk-lavender" />
                {cart?.total_credits ?? 0}
              </p>
            </div>
            <Button
              size="lg"
              disabled={checkout.isPending || insufficientCredits}
              onClick={onCheckout}
              className="gap-2"
            >
              {checkout.isPending ? "Purchasing…" : "Checkout"}
              <ArrowRight className="size-4" />
            </Button>
          </div>

          {insufficientCredits ? (
            <p className="mt-3 text-right text-sm text-mk-coral">
              Not enough credits.{" "}
              <Link href="/explore/plans" className="underline">
                Buy more
              </Link>
              .
            </p>
          ) : null}
        </>
      )}
    </div>
  );
}
