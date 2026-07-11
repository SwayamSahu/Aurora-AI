"use client";

import Link from "next/link";
import { FileText, ShoppingBag } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { Skeleton } from "@/components/ui/skeleton";

const SECTIONS = [
  {
    href: "/admin/blog",
    icon: FileText,
    title: "Blog Moderation",
    description:
      "Edit or delete any post, view drafts, and hide/edit/delete comments.",
  },
  {
    href: "/admin/marketplace",
    icon: ShoppingBag,
    title: "Marketplace Admin",
    description:
      "Plan catalog, listing moderation, wallet adjustments, refunds, and comment moderation.",
  },
];

export default function AdminIndexPage() {
  const { user, status } = useAuth();

  if (status === "loading") {
    return (
      <div className="mx-auto w-full max-w-[700px] space-y-3 px-4 py-12">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (status !== "authenticated" || !user?.is_superuser) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        Admin access required.
      </p>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[700px] px-4 py-12 md:px-8">
      <h1 className="mb-8 text-3xl font-extrabold tracking-tight">Admin</h1>

      <div className="grid gap-4 sm:grid-cols-2">
        {SECTIONS.map((section) => (
          <Link
            key={section.href}
            href={section.href}
            className="rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-5 transition-colors hover:border-[var(--mk-border-strong)]"
          >
            <section.icon className="size-6 text-mk-lavender" />
            <p className="mt-3 font-semibold">{section.title}</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {section.description}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
