"use client";

import Link from "next/link";
import { Pencil, PlusCircle, Coins } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import {
  useMyListings,
  useMyOrders,
  useMySales,
  useWallet,
} from "@/lib/marketplace/queries";
import { absoluteMediaUrl } from "@/lib/marketplace/api";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const STATUS_STYLE: Record<string, string> = {
  active: "bg-emerald-500/15 text-emerald-500",
  draft: "bg-amber-500/15 text-amber-500",
  sold: "bg-mk-lavender/15 text-mk-lavender",
  delisted: "bg-[var(--mk-surface-2)] text-muted-foreground",
};

function ListingsTab() {
  const { data: listings, isLoading } = useMyListings();
  const { data: wallet } = useWallet();
  const activeCount = (listings ?? []).filter((l) => l.status === "active").length;

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  return (
    <div>
      {wallet ? (
        <p className="mb-4 text-sm text-muted-foreground">
          Active listings: <strong>{activeCount}</strong> / {wallet.listing_quota}
        </p>
      ) : null}

      {!listings || listings.length === 0 ? (
        <p className="py-16 text-center text-muted-foreground">
          You haven&apos;t listed anything yet.{" "}
          <Link href="/explore/new" className="text-mk-lavender hover:underline">
            List your first creation
          </Link>
          .
        </p>
      ) : (
        <div className="space-y-3">
          {listings.map((listing) => (
            <div
              key={listing.id}
              className="flex items-center gap-4 rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4"
            >
              <div className="size-16 shrink-0 overflow-hidden rounded-lg bg-[var(--mk-surface-2)]">
                {listing.cover_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={absoluteMediaUrl(listing.cover_url)}
                    alt=""
                    className="size-full object-cover"
                  />
                ) : null}
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <Link
                    href={`/explore/p/${listing.id}`}
                    className="truncate font-semibold hover:underline"
                  >
                    {listing.title}
                  </Link>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${STATUS_STYLE[listing.status]}`}
                  >
                    {listing.status}
                  </span>
                </div>
                <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                  <Coins className="size-3.5" /> {listing.price_credits} ·{" "}
                  {listing.like_count} likes · {listing.comment_count} comments
                </p>
              </div>

              <Button variant="outline" size="sm" asChild>
                <Link href={`/explore/me/${listing.id}/edit`}>
                  <Pencil className="size-3.5" /> Edit
                </Link>
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SalesTab() {
  const { data: sales, isLoading } = useMySales();

  if (isLoading) return <Skeleton className="h-20 w-full" />;

  if (!sales || sales.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">No sales yet.</p>
    );
  }

  return (
    <div className="space-y-3">
      {sales.map((sale) => (
        <div
          key={sale.id}
          className="flex items-center justify-between gap-4 rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4"
        >
          <div>
            <p className="font-semibold">{sale.title}</p>
            <p className="text-xs text-muted-foreground">
              {new Date(sale.created_at).toLocaleDateString()}
            </p>
          </div>
          <p className="flex items-center gap-1 font-mono font-semibold text-emerald-500">
            <Coins className="size-4" /> +{sale.price_credits}
          </p>
        </div>
      ))}
    </div>
  );
}

function OrdersTab() {
  const { data: orders, isLoading } = useMyOrders();

  if (isLoading) return <Skeleton className="h-20 w-full" />;

  if (!orders || orders.length === 0) {
    return (
      <p className="py-16 text-center text-muted-foreground">
        No purchases yet.{" "}
        <Link href="/explore" className="text-mk-lavender hover:underline">
          Browse the marketplace
        </Link>
        .
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {orders.map((order) => (
        <div
          key={order.id}
          className="rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4"
        >
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">
              {new Date(order.created_at).toLocaleDateString()}
            </p>
            <p className="flex items-center gap-1 font-mono font-semibold">
              <Coins className="size-4 text-mk-lavender" /> {order.total_credits}
            </p>
          </div>
          <ul className="mt-2 space-y-1">
            {order.items.map((item) => (
              <li key={item.id} className="text-sm">
                {item.title}
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-muted-foreground">
            Available in your{" "}
            <Link href="/projects" className="text-mk-lavender hover:underline">
              Purchased project
            </Link>
            .
          </p>
        </div>
      ))}
    </div>
  );
}

export default function MyMarketplacePage() {
  const { status } = useAuth();

  if (status === "loading") {
    return (
      <div className="mx-auto w-full max-w-[820px] space-y-3 px-4 py-12">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (status !== "authenticated") {
    return (
      <p className="py-24 text-center text-muted-foreground">
        <a href="/login" className="text-mk-lavender hover:underline">
          Sign in
        </a>{" "}
        to see your marketplace activity.
      </p>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[820px] px-4 py-12 md:px-8">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-extrabold tracking-tight">My Marketplace</h1>
        <Button asChild size="sm" className="gap-1.5">
          <Link href="/explore/new">
            <PlusCircle className="size-3.5" /> List a creation
          </Link>
        </Button>
      </div>

      <Tabs defaultValue="listings">
        <TabsList>
          <TabsTrigger value="listings">Listings</TabsTrigger>
          <TabsTrigger value="sales">Sales</TabsTrigger>
          <TabsTrigger value="orders">Purchases</TabsTrigger>
        </TabsList>
        <TabsContent value="listings">
          <ListingsTab />
        </TabsContent>
        <TabsContent value="sales">
          <SalesTab />
        </TabsContent>
        <TabsContent value="orders">
          <OrdersTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
