"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";

import {
  useCreateListing,
  useDeleteListing,
  useMyListings,
  useUpdateListing,
  useWallet,
} from "@/lib/marketplace/queries";
import { absoluteMediaUrl } from "@/lib/marketplace/api";
import type { ListingDetail } from "@/lib/marketplace/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
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
import { AssetPicker } from "@/components/marketplace/asset-picker";
import { CoverUploader } from "@/components/marketplace/cover-uploader";

const CATEGORY_SUGGESTIONS = [
  "fantasy",
  "landscapes",
  "portraits",
  "anime",
  "animals",
  "sci-fi",
  "fashion",
  "food",
];

export function ListingEditorForm({ existing }: { existing?: ListingDetail }) {
  const router = useRouter();
  const isEdit = !!existing;

  const [title, setTitle] = React.useState(existing?.title ?? "");
  const [description, setDescription] = React.useState(existing?.description ?? "");
  const [category, setCategory] = React.useState(existing?.category ?? "");
  const [tagsInput, setTagsInput] = React.useState((existing?.tags ?? []).join(", "));
  const [priceCredits, setPriceCredits] = React.useState(
    existing ? String(existing.price_credits) : "",
  );
  const [stock, setStock] = React.useState(existing ? String(existing.stock) : "1");
  const [assetId, setAssetId] = React.useState<string | null>(null);
  const [coverMediaId, setCoverMediaId] = React.useState<string | null>(
    existing?.cover_media_id ?? null,
  );
  const [coverUrl, setCoverUrl] = React.useState<string | null>(
    existing?.cover_url ? absoluteMediaUrl(existing.cover_url) : null,
  );

  const { data: wallet } = useWallet();
  const { data: myListings } = useMyListings();
  const activeCount = (myListings ?? []).filter((l) => l.status === "active").length;

  const create = useCreateListing();
  const update = useUpdateListing(existing?.id);
  const remove = useDeleteListing();
  const [saving, setSaving] = React.useState(false);

  async function onSave(status: "draft" | "active") {
    if (!title.trim()) {
      toast.error("Give your listing a title first.");
      return;
    }
    const price = Number(priceCredits);
    if (!Number.isFinite(price) || price <= 0) {
      toast.error("Set a price in credits (greater than 0).");
      return;
    }
    if (!isEdit && !assetId) {
      toast.error("Pick which of your creations you're listing.");
      return;
    }
    if (status === "active" && !coverMediaId) {
      toast.error("Add a preview image before publishing.");
      return;
    }

    const tags = tagsInput
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    setSaving(true);
    try {
      if (isEdit && existing) {
        await update.mutateAsync({
          id: existing.id,
          input: {
            title: title.trim(),
            description: description.trim() || null,
            category: category.trim() || undefined,
            tags,
            price_credits: price,
            stock: Number(stock) || 1,
            cover_media_id: coverMediaId,
            status,
          },
        });
        toast.success(status === "active" ? "Listing published." : "Draft saved.");
      } else {
        await create.mutateAsync({
          title: title.trim(),
          description: description.trim() || null,
          category: category.trim() || undefined,
          tags,
          price_credits: price,
          stock: Number(stock) || 1,
          source_asset_id: assetId!,
          cover_media_id: coverMediaId,
          status,
        });
        toast.success(status === "active" ? "Listing published." : "Draft saved.");
      }
      router.push("/explore/me");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't save the listing.");
    } finally {
      setSaving(false);
    }
  }

  async function onDelete() {
    if (!existing) return;
    try {
      await remove.mutateAsync(existing.id);
      toast.success("Listing deleted.");
      router.push("/explore/me");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't delete the listing.");
    }
  }

  // Publishing only costs a quota slot if this listing isn't already
  // active — matches the backend's `_ensure_quota`, which only checks on
  // a transition *into* active, not on re-saving an already-active listing.
  const wouldConsumeQuotaSlot = !existing || existing.status !== "active";
  const quotaExceeded =
    wouldConsumeQuotaSlot && !!wallet && activeCount >= wallet.listing_quota;

  return (
    <div className="mx-auto w-full max-w-[720px] px-4 py-10 md:px-8">
      {wallet ? (
        <p className="mb-6 text-sm text-muted-foreground">
          Active listings: <strong>{activeCount}</strong> / {wallet.listing_quota}
          {quotaExceeded ? (
            <>
              {" "}
              — quota reached.{" "}
              <Link href="/explore/plans" className="text-mk-lavender hover:underline">
                Buy a plan
              </Link>{" "}
              for more room, or publish as a draft.
            </>
          ) : null}
        </p>
      ) : null}

      {!isEdit ? (
        <div className="mb-6">
          <label className="mb-2 block text-sm font-semibold">
            Which creation are you listing?
          </label>
          <AssetPicker value={assetId} onChange={(id) => setAssetId(id)} />
        </div>
      ) : null}

      <label className="mb-2 block text-sm font-semibold">Preview image</label>
      <CoverUploader
        mediaId={coverMediaId}
        coverUrl={coverUrl}
        onChange={(id, url) => {
          setCoverMediaId(id);
          setCoverUrl(url);
        }}
      />

      <Input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Listing title"
        className="mt-6 h-auto border-none bg-transparent px-0 text-3xl font-extrabold shadow-none focus-visible:ring-0"
      />
      <Textarea
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="Describe what makes this worth buying…"
        className="mt-2 min-h-24 border-none bg-transparent px-0 shadow-none focus-visible:ring-0"
      />

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Category</label>
          <Input
            list="mk-category-suggestions"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="e.g. sci-fi"
          />
          <datalist id="mk-category-suggestions">
            {CATEGORY_SUGGESTIONS.map((c) => (
              <option key={c} value={c} />
            ))}
          </datalist>
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">
            Price (credits)
          </label>
          <Input
            type="number"
            min={1}
            value={priceCredits}
            onChange={(e) => setPriceCredits(e.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Stock</label>
          <Input
            type="number"
            min={1}
            value={stock}
            onChange={(e) => setStock(e.target.value)}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Tags</label>
          <Input
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="comma, separated"
          />
        </div>
      </div>

      <div className="mt-8 flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={() => onSave("draft")} loading={saving}>
            Save draft
          </Button>
          <Button
            onClick={() => onSave("active")}
            loading={saving}
            disabled={quotaExceeded}
          >
            {isEdit ? "Save & publish" : "Publish"}
          </Button>
        </div>

        {isEdit ? (
          <Dialog>
            <DialogTrigger asChild>
              <Button
                variant="ghost"
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="size-4" /> Delete
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Delete this listing?</DialogTitle>
                <DialogDescription>
                  This can&apos;t be undone. Sold listings can&apos;t be deleted
                  (delist instead) to keep order history intact.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="outline">Cancel</Button>
                </DialogClose>
                <Button variant="destructive" onClick={onDelete}>
                  Delete
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        ) : null}
      </div>
    </div>
  );
}
