"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Plus } from "lucide-react";

import { cn } from "@/lib/utils";
import { navSections } from "@/lib/navigation";
import { Logo } from "@/components/layout/logo";
import { Button } from "@/components/ui/button";

export function Sidebar({ className }: { className?: string }) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "flex h-full w-64 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground",
        className,
      )}
    >
      <div className="flex h-16 items-center px-5">
        <Link href="/dashboard" aria-label="Aurora home">
          <Logo />
        </Link>
      </div>

      <div className="px-3 pb-2">
        <Button asChild className="w-full justify-start gap-2">
          <Link href="/studio">
            <Plus className="size-4" />
            New video
          </Link>
        </Button>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4 scrollbar-thin">
        {navSections.map((section) => (
          <div key={section.label}>
            <p className="px-2 pb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {section.label}
            </p>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const active =
                  pathname === item.href ||
                  pathname.startsWith(item.href + "/");
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "flex items-center gap-3 rounded-md px-2 py-2 text-sm font-medium transition-colors",
                        active
                          ? "bg-sidebar-accent text-sidebar-accent-foreground"
                          : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-foreground",
                      )}
                    >
                      <item.icon className="size-4 shrink-0" />
                      {item.title}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-sidebar-border p-3">
        <p className="px-2 text-xs text-muted-foreground">
          Aurora · v0.1.0
        </p>
      </div>
    </aside>
  );
}
