"use client";

import Link from "next/link";
import { FileText, ScrollText, ShoppingBag, Users } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { isAdmin, isModerator } from "@/lib/admin/access";
import { Skeleton } from "@/components/ui/skeleton";

const SECTIONS = [
  {
    href: "/admin/blog",
    icon: FileText,
    title: "Blog Moderation",
    description:
      "Edit or delete any post, view drafts, and hide/edit/delete comments.",
    adminOnly: false,
  },
  {
    href: "/admin/marketplace",
    icon: ShoppingBag,
    title: "Marketplace Admin",
    description:
      "Listing moderation and comments for all; plans, wallet adjustments and refunds for admins.",
    adminOnly: false,
  },
  {
    href: "/admin/users",
    icon: Users,
    title: "User Management",
    description:
      "Search accounts, view aggregated activity, change roles, and suspend/reactivate.",
    adminOnly: true,
  },
  {
    href: "/admin/audit",
    icon: ScrollText,
    title: "Audit Log",
    description:
      "Append-only record of every privileged admin and moderator action.",
    adminOnly: true,
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

  if (status !== "authenticated" || !isModerator(user)) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        Admin access required.
      </p>
    );
  }

  const admin = isAdmin(user);

  return (
    <div className="mx-auto w-full max-w-[700px] px-4 py-12 md:px-8">
      <h1 className="mb-2 text-3xl font-extrabold tracking-tight">Admin</h1>
      <p className="mb-8 text-sm text-muted-foreground">
        Signed in as <span className="font-semibold">{user?.role}</span>.
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        {SECTIONS.filter((s) => admin || !s.adminOnly).map((section) => (
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
