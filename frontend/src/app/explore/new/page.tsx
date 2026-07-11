"use client";

import { useAuth } from "@/components/auth/auth-provider";
import { ListingEditorForm } from "@/components/marketplace/listing-editor-form";
import { Skeleton } from "@/components/ui/skeleton";

export default function NewListingPage() {
  const { status } = useAuth();

  if (status === "loading") {
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
        to list a creation.
      </p>
    );
  }

  return <ListingEditorForm />;
}
