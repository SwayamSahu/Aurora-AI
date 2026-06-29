"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { PageLoader } from "@/components/shared/spinner";

/** Wraps auth pages — sends already-authenticated users to the dashboard. */
export function RedirectIfAuthed({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (status === "authenticated") {
      router.replace("/dashboard");
    }
  }, [status, router]);

  if (status === "loading" || status === "authenticated") {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <PageLoader />
      </div>
    );
  }

  return <>{children}</>;
}
