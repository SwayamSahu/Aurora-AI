"use client";

import { useParams } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { useListing } from "@/lib/marketplace/queries";
import { ListingEditorForm } from "@/components/marketplace/listing-editor-form";
import { Skeleton } from "@/components/ui/skeleton";

export default function EditListingPage() {
  const params = useParams<{ id: string }>();
  const { user, status } = useAuth();
  const { data: listing, isLoading, isError } = useListing(params.id);

  if (status === "loading" || isLoading) {
    return (
      <div className="mx-auto w-full max-w-[720px] space-y-4 px-4 py-12">
        <Skeleton className="h-56 w-full" />
        <Skeleton className="h-10 w-2/3" />
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
        to edit this listing.
      </p>
    );
  }

  if (isError || !listing) {
    return (
      <p className="py-24 text-center text-muted-foreground">Listing not found.</p>
    );
  }

  if (listing.seller.id !== user?.id && !user?.is_superuser) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        You can only edit your own listings.
      </p>
    );
  }

  return <ListingEditorForm existing={listing} />;
}
