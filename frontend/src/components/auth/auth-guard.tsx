"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/auth-provider";
import { PageLoader } from "@/components/shared/spinner";

/** Gates workspace routes — redirects unauthenticated users to /login. */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (status === "unauthenticated") {
      router.replace("/login");
    }
  }, [status, router]);

  if (status !== "authenticated") {
    return (
      <div className="flex h-svh items-center justify-center">
        <PageLoader label="Loading your workspace…" />
      </div>
    );
  }

  return <>{children}</>;
}
