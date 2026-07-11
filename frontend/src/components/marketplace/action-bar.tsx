"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, ChevronDown, Coins, ShoppingCart } from "lucide-react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";
import { useAddToCart, useCheckout } from "@/lib/marketplace/queries";
import type { ListingDetail } from "@/lib/marketplace/types";

export function ActionBar({ piece, pulse }: { piece: ListingDetail; pulse?: boolean }) {
  const [showDetails, setShowDetails] = React.useState(false);
  const router = useRouter();
  const { user, status } = useAuth();
  const addToCart = useAddToCart();
  const checkout = useCheckout();

  const sold = piece.status !== "active";
  const isOwnListing = user?.id === piece.seller.id;
  const busy = addToCart.isPending || checkout.isPending;

  async function buyNow() {
    if (status !== "authenticated") {
      router.push("/login");
      return;
    }
    try {
      await addToCart.mutateAsync(piece.id);
      const order = await checkout.mutateAsync();
      toast.success(`Purchased for ${order.total_credits} credits — added to your library.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't complete the purchase.");
    }
  }

  return (
    <div className="mt-8">
      <div className="flex flex-wrap items-center gap-3">
        {isOwnListing ? (
          <span className="inline-flex h-12 items-center rounded-full bg-[var(--mk-surface-2)] px-6 text-[14px] font-bold uppercase tracking-[1px] text-muted-foreground">
            This is your listing
          </span>
        ) : (
          <button
            type="button"
            disabled={sold || busy}
            onClick={buyNow}
            className={cn(
              "group inline-flex h-12 items-center gap-2 rounded-full px-6 text-[14px] font-bold uppercase tracking-[1px] text-black transition-transform hover:scale-[1.02]",
              pulse && "[animation:mk-pulse_1.4s_ease-out_1]",
              (sold || busy) && "pointer-events-none opacity-50",
            )}
            style={{ background: "var(--mk-grad-make-yours)" }}
          >
            <ShoppingCart className="size-4" />
            {sold
              ? "Sold out"
              : busy
                ? "Purchasing…"
                : `Buy now — ${piece.price_credits} credits`}
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
          </button>
        )}
      </div>

      <button
        type="button"
        onClick={() => setShowDetails((v) => !v)}
        aria-expanded={showDetails}
        className="mt-4 inline-flex h-10 items-center gap-2 rounded-full bg-[var(--mk-surface-2)] px-5 text-[13px] font-bold uppercase tracking-[1px] text-foreground transition-colors hover:bg-[var(--mk-surface-hover)]"
      >
        Details
        <ChevronDown
          className={cn("size-4 transition-transform", showDetails && "rotate-180")}
        />
      </button>

      {showDetails ? (
        <div className="mt-4 rounded-2xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-5">
          <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-[13px]">
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Category</dt>
              <dd className="font-mono capitalize">{piece.category}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Type</dt>
              <dd className="font-mono capitalize">{piece.kind}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Seller</dt>
              <dd className="font-mono">{piece.seller.full_name ?? "Anonymous"}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted-foreground">Price</dt>
              <dd className="inline-flex items-center gap-1 font-mono">
                <Coins className="size-3.5" /> {piece.price_credits}
              </dd>
            </div>
          </dl>
          {piece.tags.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {piece.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-[var(--mk-surface-2)] px-2.5 py-1 text-[11px] text-muted-foreground"
                >
                  #{tag}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
