"use client";

import { Heart } from "lucide-react";

import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/auth-provider";
import { useToggleListingLike } from "@/lib/marketplace/queries";
import type { ListingDetail } from "@/lib/marketplace/types";
import { formatCount } from "@/lib/marketplace/format";

export function LikeButton({ piece }: { piece: ListingDetail }) {
  const { status } = useAuth();
  const toggle = useToggleListingLike(piece.id);

  function onClick() {
    if (status !== "authenticated") {
      window.location.href = "/login";
      return;
    }
    toggle.mutate(!piece.liked_by_me);
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={toggle.isPending}
      aria-pressed={piece.liked_by_me}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
        piece.liked_by_me
          ? "border-transparent bg-mk-lavender text-black"
          : "border-[var(--mk-border)] text-muted-foreground hover:text-foreground",
      )}
    >
      <Heart className={cn("size-4", piece.liked_by_me && "fill-current")} />
      {formatCount(piece.like_count)}
    </button>
  );
}
