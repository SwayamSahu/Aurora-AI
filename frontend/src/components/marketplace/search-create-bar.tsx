"use client";

import Link from "next/link";
import { Search, Plus } from "lucide-react";

import { mkSearch } from "@/lib/marketplace/content";

export function SearchCreateBar({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="search"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={mkSearch.placeholder}
          aria-label="Search the marketplace"
          className="h-12 w-full rounded-full border border-[var(--mk-border)] bg-[var(--mk-surface-2)] pl-11 pr-4 text-[16px] text-foreground placeholder:text-muted-foreground focus:border-[var(--mk-border-strong)] focus:outline-none"
        />
      </div>
      <Link
        href={mkSearch.create.href}
        className="inline-flex h-12 shrink-0 items-center gap-2 rounded-full px-5 text-[15px] font-semibold text-black shadow-[0_8px_30px_-8px_var(--mk-violet)] transition-transform hover:scale-[1.02]"
        style={{ background: "var(--mk-grad-create)" }}
      >
        <Plus className="size-4" strokeWidth={2.6} />
        <span className="uppercase tracking-wide">Create</span>
      </Link>
    </div>
  );
}
