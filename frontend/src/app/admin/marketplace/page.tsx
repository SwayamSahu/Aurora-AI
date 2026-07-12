"use client";

import * as React from "react";
import Link from "next/link";
import { toast } from "sonner";
import { MessageSquare, Pencil, Trash2 } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { isAdmin, isModerator } from "@/lib/admin/access";
import {
  useAdminAdjustWallet,
  useAdminDelistListing,
  useAdminListingComments,
  useAdminListings,
  useAdminPlans,
  useAdminRefundOrder,
  useCreateAdminPlan,
  useDeleteListing,
  useDeleteListingComment,
  useModerateListingComment,
  useUpdateAdminPlan,
} from "@/lib/marketplace/queries";
import { AdminCommentModeration } from "@/components/admin/comment-moderation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  DialogTrigger,
} from "@/components/ui/dialog";

function PlansTab() {
  const { data: plans, isLoading } = useAdminPlans();
  const update = useUpdateAdminPlan();
  const create = useCreateAdminPlan();
  const [form, setForm] = React.useState({
    name: "",
    price_cents: "",
    credits_granted: "",
    listing_quota: "",
  });

  async function onCreate() {
    if (!form.name.trim()) {
      toast.error("Give the plan a name.");
      return;
    }
    try {
      await create.mutateAsync({
        name: form.name.trim(),
        price_cents: Number(form.price_cents) || 0,
        credits_granted: Number(form.credits_granted) || 0,
        listing_quota: Number(form.listing_quota) || 0,
      });
      toast.success("Plan created.");
      setForm({ name: "", price_cents: "", credits_granted: "", listing_quota: "" });
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't create plan.");
    }
  }

  if (isLoading) return <Skeleton className="h-40 w-full" />;

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        {(plans ?? []).map((plan) => (
          <div
            key={plan.id}
            className="flex flex-wrap items-center gap-4 rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4"
          >
            <div className="min-w-[140px] flex-1">
              <p className="font-semibold">{plan.name}</p>
              <p className="text-xs text-muted-foreground">
                ${(plan.price_cents / 100).toFixed(2)} · {plan.credits_granted} credits ·{" "}
                {plan.listing_quota} listings
              </p>
            </div>
            <label className="flex items-center gap-2 text-sm">
              Active
              <Switch
                checked={plan.is_active}
                onCheckedChange={(checked) =>
                  update.mutate({ id: plan.id, input: { is_active: checked } })
                }
              />
            </label>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-dashed border-[var(--mk-border-strong)] p-4">
        <p className="mb-3 text-sm font-semibold">New plan</p>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Input
            placeholder="Name"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
          <Input
            type="number"
            placeholder="Price (cents)"
            value={form.price_cents}
            onChange={(e) => setForm((f) => ({ ...f, price_cents: e.target.value }))}
          />
          <Input
            type="number"
            placeholder="Credits granted"
            value={form.credits_granted}
            onChange={(e) => setForm((f) => ({ ...f, credits_granted: e.target.value }))}
          />
          <Input
            type="number"
            placeholder="Listing quota"
            value={form.listing_quota}
            onChange={(e) => setForm((f) => ({ ...f, listing_quota: e.target.value }))}
          />
        </div>
        <Button className="mt-3" onClick={onCreate} loading={create.isPending}>
          Create plan
        </Button>
      </div>
    </div>
  );
}

function CommentsPanel({ listingId }: { listingId: string }) {
  const { data: comments, isLoading } = useAdminListingComments(listingId);
  const moderate = useModerateListingComment(listingId);
  const del = useDeleteListingComment(listingId);

  return (
    <div className="mt-3 border-t border-[var(--mk-border)] pt-3">
      <AdminCommentModeration
        comments={comments}
        isLoading={isLoading}
        onToggleHidden={(id, hidden) =>
          moderate.mutate(
            { commentId: id, input: { is_hidden: hidden } },
            {
              onError: (err) =>
                toast.error(err instanceof Error ? err.message : "Failed."),
            },
          )
        }
        onEditBody={(id, body) =>
          moderate.mutate(
            { commentId: id, input: { body } },
            {
              onSuccess: () => toast.success("Comment updated."),
              onError: (err) =>
                toast.error(err instanceof Error ? err.message : "Failed."),
            },
          )
        }
        onDelete={(id) =>
          del.mutate(id, {
            onSuccess: () => toast.success("Comment deleted."),
            onError: (err) =>
              toast.error(err instanceof Error ? err.message : "Failed."),
          })
        }
      />
    </div>
  );
}

function DeleteListingButton({ listingId }: { listingId: string }) {
  const remove = useDeleteListing();
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="text-destructive hover:text-destructive"
        >
          <Trash2 className="size-3.5" /> Delete
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete this listing?</DialogTitle>
          <DialogDescription>
            This can&apos;t be undone. Sold listings can&apos;t be deleted —
            delist instead to keep order history intact.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button
            variant="destructive"
            onClick={() =>
              remove.mutate(listingId, {
                onSuccess: () => toast.success("Listing deleted."),
                onError: (err) =>
                  toast.error(err instanceof Error ? err.message : "Failed."),
              })
            }
          >
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ListingsTab() {
  const [status, setStatus] = React.useState<string>("all");
  const [openComments, setOpenComments] = React.useState<string | null>(null);
  const { data: listings, isLoading } = useAdminListings(
    status === "all" ? undefined : status,
  );
  const delist = useAdminDelistListing();

  return (
    <div className="space-y-4">
      <Select value={status} onValueChange={setStatus}>
        <SelectTrigger className="w-44">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All statuses</SelectItem>
          <SelectItem value="draft">Draft</SelectItem>
          <SelectItem value="active">Active</SelectItem>
          <SelectItem value="sold">Sold</SelectItem>
          <SelectItem value="delisted">Delisted</SelectItem>
        </SelectContent>
      </Select>

      {isLoading ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <div className="space-y-2">
          {(listings ?? []).map((listing) => (
            <div
              key={listing.id}
              className="rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="font-semibold">{listing.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {listing.status} · {listing.price_credits} credits ·{" "}
                    {listing.comment_count} comments · seller{" "}
                    {listing.seller.full_name ?? listing.seller.id}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      setOpenComments(
                        openComments === listing.id ? null : listing.id,
                      )
                    }
                  >
                    <MessageSquare className="size-3.5" /> Comments
                  </Button>
                  <Button variant="outline" size="sm" asChild>
                    <Link href={`/explore/me/${listing.id}/edit`}>
                      <Pencil className="size-3.5" /> Edit
                    </Link>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={listing.status === "delisted" || delist.isPending}
                    onClick={() =>
                      delist.mutate(listing.id, {
                        onSuccess: () => toast.success("Listing delisted."),
                        onError: (err) =>
                          toast.error(
                            err instanceof Error ? err.message : "Failed.",
                          ),
                      })
                    }
                  >
                    Delist
                  </Button>
                  <DeleteListingButton listingId={listing.id} />
                </div>
              </div>

              {openComments === listing.id ? (
                <CommentsPanel listingId={listing.id} />
              ) : null}
            </div>
          ))}
          {listings && listings.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No listings match this filter.
            </p>
          ) : null}
        </div>
      )}
    </div>
  );
}

function WalletAdjustTab() {
  const [userId, setUserId] = React.useState("");
  const [amount, setAmount] = React.useState("");
  const [note, setNote] = React.useState("");
  const [result, setResult] = React.useState<number | null>(null);
  const adjust = useAdminAdjustWallet();

  async function submit() {
    const amt = Number(amount);
    if (!userId.trim() || !amt || !note.trim()) {
      toast.error("Fill in user id, a non-zero amount, and a note.");
      return;
    }
    try {
      const res = await adjust.mutateAsync({ userId: userId.trim(), amount: amt, note });
      setResult(res.balance_credits);
      toast.success(`Wallet adjusted. New balance: ${res.balance_credits}.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Adjustment failed.");
    }
  }

  return (
    <div className="max-w-md space-y-3">
      <Input
        placeholder="User ID"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
      />
      <Input
        type="number"
        placeholder="Amount (negative to debit)"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
      />
      <Input
        placeholder="Note (required, shown in their ledger)"
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
      <Button onClick={submit} loading={adjust.isPending}>
        Apply adjustment
      </Button>
      {result !== null ? (
        <p className="text-sm text-muted-foreground">
          New balance: <strong>{result}</strong>
        </p>
      ) : null}
    </div>
  );
}

function RefundTab() {
  const [orderId, setOrderId] = React.useState("");
  const refund = useAdminRefundOrder();

  async function submit() {
    if (!orderId.trim()) {
      toast.error("Enter an order id.");
      return;
    }
    try {
      const order = await refund.mutateAsync(orderId.trim());
      toast.success(`Order refunded — status: ${order.status}.`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Refund failed.");
    }
  }

  return (
    <div className="max-w-md space-y-3">
      <Input
        placeholder="Order ID"
        value={orderId}
        onChange={(e) => setOrderId(e.target.value)}
      />
      <Button onClick={submit} loading={refund.isPending} variant="destructive">
        Refund order
      </Button>
      <p className="text-xs text-muted-foreground">
        Credits the buyer back in full and reclaims each seller&apos;s earning
        where they still have the balance to cover it. Doesn&apos;t restock or
        reactivate the listing.
      </p>
    </div>
  );
}

export default function AdminMarketplacePage() {
  const { user, status } = useAuth();

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

  // Finance tabs (plans, wallet, refunds) are admin-only; moderators only
  // get listing + comment moderation.
  const admin = isAdmin(user);

  return (
    <div className="mx-auto w-full max-w-[900px] px-4 py-12 md:px-8">
      <h1 className="mb-8 text-3xl font-extrabold tracking-tight">
        Marketplace Admin
      </h1>

      <Tabs defaultValue="listings">
        <TabsList>
          <TabsTrigger value="listings">Listings</TabsTrigger>
          {admin ? <TabsTrigger value="plans">Plans</TabsTrigger> : null}
          {admin ? <TabsTrigger value="wallet">Wallet Adjust</TabsTrigger> : null}
          {admin ? <TabsTrigger value="refund">Refund</TabsTrigger> : null}
        </TabsList>
        <TabsContent value="listings">
          <ListingsTab />
        </TabsContent>
        {admin ? (
          <>
            <TabsContent value="plans">
              <PlansTab />
            </TabsContent>
            <TabsContent value="wallet">
              <WalletAdjustTab />
            </TabsContent>
            <TabsContent value="refund">
              <RefundTab />
            </TabsContent>
          </>
        ) : null}
      </Tabs>
    </div>
  );
}
